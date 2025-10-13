"""
Генератор Google Sheets коммерческого предложения
Группирует товары и показывает все варианты маршрутов для каждого товара
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


class KPGoogleSheetsGenerator:
    """Генератор Google Sheets файлов для коммерческого предложения"""
    
    def __init__(self):
        self.db_manager = PostgreSQLManager()
        # Google Sheets API будет использоваться через MCP
    
    def get_kp_items(self, session_id):
        """Получает товары из КП и группирует по product_id"""
        
        db_session = self.db_manager.get_session_direct()
        
        try:
            result = db_session.execute(text("""
                SELECT 
                    ki.id as kp_item_id,
                    p.id as product_id,
                    p.name as product_name,
                    p.description,
                    p.sample_price,
                    p.sample_delivery_time,
                    po.id as price_offer_id,
                    po.quantity,
                    po.route,
                    po.price_usd,
                    po.price_rub,
                    po.delivery_time_days
                FROM kp_items ki
                JOIN products p ON p.id = ki.product_id
                JOIN price_offers po ON po.id = ki.price_offer_id
                WHERE ki.session_id = :session_id
                ORDER BY p.name, po.quantity
            """), {'session_id': session_id})
            
            # Группируем по product_id
            products_grouped = defaultdict(lambda: {
                'info': None,
                'offers': [],
                'images': []
            })
            
            for row in result:
                product_id = row[1]
                
                # Информация о товаре (заполняем один раз)
                if products_grouped[product_id]['info'] is None:
                    products_grouped[product_id]['info'] = {
                        'name': row[2],
                        'description': row[3],
                        'sample_price': float(row[4]) if row[4] else None,
                        'sample_delivery_time': row[5]
                    }
                
                # Добавляем ценовое предложение
                products_grouped[product_id]['offers'].append({
                    'quantity': row[7],
                    'route': row[8],
                    'price_usd': float(row[9]) if row[9] else None,
                    'price_rub': float(row[10]) if row[10] else None,
                    'delivery_days': row[11]
                })
            
            # Получаем все изображения для каждого товара
            for product_id in products_grouped.keys():
                img_result = db_session.execute(text("""
                    SELECT image_url, image_filename
                    FROM product_images
                    WHERE product_id = :product_id
                    AND (image_url IS NOT NULL OR image_filename IS NOT NULL)
                    ORDER BY CASE WHEN column_number = 1 THEN 0 ELSE 1 END, id
                    LIMIT 5
                """), {'product_id': product_id})
                
                for img_row in img_result:
                    image_url = img_row[0]
                    if not image_url and img_row[1]:
                        image_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{img_row[1]}"
                    
                    if image_url:
                        products_grouped[product_id]['images'].append(image_url)
            
            return products_grouped
        finally:
            db_session.close()
    
    def prepare_sheet_data(self, products_grouped):
        """Подготавливает данные для Google Sheets"""
        
        rows = []
        
        # Заголовок документа
        rows.append(['КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ'])
        rows.append([f'от {datetime.now().strftime("%d.%m.%Y")}'])
        rows.append([''])  # Пустая строка
        
        # Генерируем товары
        for product_id, product_data in products_grouped.items():
            product_info = product_data['info']
            offers = product_data['offers']
            images = product_data['images']
            
            print(f"   Обрабатываю: {product_info['name']} ({len(offers)} вариантов, {len(images)} изображений)")
            
            # Название товара
            rows.append([product_info['name'], '', '', '', '', ''])
            
            # Описание (если есть)
            if product_info['description']:
                desc_text = product_info['description'][:200]
                rows.append([desc_text, '', '', '', '', ''])
            
            # Информация об образце (если есть)
            if product_info['sample_price'] or product_info['sample_delivery_time']:
                sample_parts = []
                if product_info['sample_price']:
                    sample_parts.append(f"Образец: ${product_info['sample_price']:.2f}")
                if product_info['sample_delivery_time']:
                    sample_parts.append(f"Срок: {product_info['sample_delivery_time']} дн.")
                rows.append([' | '.join(sample_parts), '', '', '', '', ''])
            
            # Заголовок таблицы с ценами
            rows.append(['Тираж', 'USD', 'RUB', 'Доставка', 'Срок', 'Изображения'])
            
            # Ценовые предложения с изображениями
            for idx, offer in enumerate(offers):
                row_data = [
                    f"{offer['quantity']:,.0f} шт",
                    f"${offer['price_usd']:.2f}" if offer['price_usd'] else '-',
                    f"₽{offer['price_rub']:.2f}" if offer['price_rub'] else '-',
                    offer['route'] or '-',
                    f"{offer['delivery_days']} дн." if offer['delivery_days'] else '-'
                ]
                
                # Добавляем URL изображения в первую строку предложений
                if idx == 0 and images:
                    # Все изображения в последний столбец
                    row_data.append(', '.join(images[:5]))  # До 5 изображений
                else:
                    row_data.append('')
                
                rows.append(row_data)
            
            # Пустая строка между товарами
            rows.append(['', '', '', '', '', ''])
        
        return rows
    
    def generate_mcp_instructions(self, session_id):
        """Генерирует инструкции для MCP создания Google Sheets"""
        
        products = self.get_kp_items(session_id)
        
        if not products:
            raise ValueError("КП пустое. Добавьте товары перед генерацией.")
        
        sheet_data = self.prepare_sheet_data(products)
        
        # Возвращаем данные для дальнейшей обработки через MCP
        return {
            'title': f'КП_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'data': sheet_data,
            'products': products  # Для вставки изображений
        }
    
    def generate(self, session_id):
        """
        Генерирует Google Sheets КП
        
        ВАЖНО: Этот метод возвращает данные для создания через MCP.
        Фактическое создание Google Sheets должно происходить через:
        1. mcp_google-sheets_create_spreadsheet(title)
        2. mcp_google-sheets_update_cells(spreadsheet_id, sheet, range, data)
        3. Вставка изображений (требует специальную обработку)
        """
        
        return self.generate_mcp_instructions(session_id)


if __name__ == "__main__":
    """Тестовый запуск для проверки"""
    
    # Для теста нужен session_id
    test_session_id = input("Введите session_id для теста: ")
    
    generator = KPGoogleSheetsGenerator()
    
    try:
        result = generator.generate(test_session_id)
        print(f"\n✅ [Google Sheets] Данные подготовлены")
        print(f"   Название: {result['title']}")
        print(f"   Строк данных: {len(result['data'])}")
        print(f"   Товаров: {len(result['products'])}")
        
        print("\n📋 Первые 10 строк:")
        for i, row in enumerate(result['data'][:10], 1):
            print(f"   {i}. {row}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


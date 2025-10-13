"""
Генератор PDF коммерческого предложения
Группирует товары и показывает все варианты маршрутов для каждого товара
"""

import os
from pathlib import Path
import sys
from datetime import datetime
from collections import defaultdict

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import requests
from io import BytesIO
from PIL import Image as PILImage

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text


def get_bundled_font():
    """Возвращает путь к встроенному в репозиторий шрифту DejaVu Sans"""
    font_dir = Path(__file__).parent / 'fonts'
    font_file = font_dir / 'DejaVuSans.ttf'
    font_bold_file = font_dir / 'DejaVuSans-Bold.ttf'
    
    if font_file.exists():
        print(f"✅ [PDF] Найден встроенный шрифт DejaVu Sans")
        return str(font_file), str(font_bold_file) if font_bold_file.exists() else str(font_file)
    else:
        print(f"❌ [PDF] Шрифт не найден: {font_file}")
        print(f"   Проверьте что папка fonts/ есть в репозитории")
        return None, None


# АВТОМАТИЧЕСКАЯ ПРОВЕРКА ВСТРОЕННОГО ШРИФТА ПРИ ИМПОРТЕ
print("🔄 [PDF] Проверка встроенного шрифта для кириллицы...")
_FONT_PATHS = get_bundled_font()
if _FONT_PATHS and _FONT_PATHS[0]:
    print(f"✅ [PDF] Шрифт готов: {_FONT_PATHS[0]}")
else:
    print("⚠️  [PDF] Встроенный шрифт не найден - кириллица не будет работать")


class KPPDFGenerator:
    """Генератор PDF файлов для коммерческого предложения"""
    
    def __init__(self):
        self.db_manager = PostgreSQLManager()
        
        # Регистрация шрифта для русского языка
        font_loaded = False
        
        # 1. ПРИОРИТЕТ: Используем встроенный в репозиторий шрифт
        if _FONT_PATHS and _FONT_PATHS[0]:
            try:
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont('DejaVuSans', _FONT_PATHS[0]))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', _FONT_PATHS[1]))
                
                self.font_name = 'DejaVuSans'
                self.font_name_bold = 'DejaVuSans-Bold'
                font_loaded = True
                print(f"✅ [PDF] Зарегистрирован встроенный шрифт DejaVu Sans")
            except Exception as e:
                print(f"⚠️  [PDF] Ошибка регистрации встроенного шрифта: {e}")
        
        # 2. РЕЗЕРВНЫЙ: Проверяем системные шрифты
        if not font_loaded:
            font_paths = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux (Debian/Ubuntu)
                '/usr/share/fonts/dejavu/DejaVuSans.ttf',  # Linux (альтернативный путь)
                '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',  # macOS
                'C:\\Windows\\Fonts\\arial.ttf',  # Windows
            ]
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        from reportlab.pdfbase.ttfonts import TTFont
                        pdfmetrics.registerFont(TTFont('SystemFont', font_path))
                        
                        # Пробуем загрузить bold версию
                        bold_path = font_path.replace('Sans.ttf', 'Sans-Bold.ttf').replace('arial.ttf', 'arialbd.ttf')
                        if os.path.exists(bold_path):
                            pdfmetrics.registerFont(TTFont('SystemFont-Bold', bold_path))
                        else:
                            pdfmetrics.registerFont(TTFont('SystemFont-Bold', font_path))
                        
                        self.font_name = 'SystemFont'
                        self.font_name_bold = 'SystemFont-Bold'
                        font_loaded = True
                        print(f"✅ [PDF] Загружен системный шрифт: {font_path}")
                        break
                except Exception as e:
                    continue
        
        # 3. КРИТИЧЕСКОЕ FALLBACK: Helvetica БЕЗ кириллицы
        if not font_loaded:
            self.font_name = 'Helvetica'
            self.font_name_bold = 'Helvetica-Bold'
            print("❌ [PDF] ВНИМАНИЕ: Кириллица НЕ будет отображаться! Используется Helvetica.")
            print("   Проверьте логи скачивания шрифта выше.")
        
        # Стили в минималистичном UI стиле (серый, без ярких цветов)
        self.styles = getSampleStyleSheet()
        
        # Заголовок документа
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontName=self.font_name_bold,
            fontSize=18,
            textColor=colors.HexColor('#1f2937'),  # Темно-серый
            alignment=TA_CENTER,
            spaceAfter=10
        )
        
        # Дата
        self.date_style = ParagraphStyle(
            'DateStyle',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),  # Серый
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Название товара
        self.product_style = ParagraphStyle(
            'ProductName',
            parent=self.styles['Heading2'],
            fontName=self.font_name_bold,
            fontSize=14,
            textColor=colors.HexColor('#374151'),  # Темно-серый
            spaceAfter=6
        )
        
        # Описание товара
        self.description_style = ParagraphStyle(
            'Description',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.HexColor('#6b7280'),  # Серый
            spaceAfter=6
        )
        
        # Информация об образце (минималистичный стиль)
        self.sample_style = ParagraphStyle(
            'SampleInfo',
            parent=self.styles['Normal'],
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.HexColor('#4b5563'),  # Средне-серый
            spaceAfter=6
        )
    
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
            
            # Получаем изображения для каждого товара
            for product_id in products_grouped.keys():
                img_result = db_session.execute(text("""
                    SELECT image_url, image_filename
                    FROM product_images
                    WHERE product_id = :product_id
                    AND (image_url IS NOT NULL OR image_filename IS NOT NULL)
                    ORDER BY CASE WHEN column_number = 1 THEN 0 ELSE 1 END, id
                    LIMIT 3
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
    
    def download_image(self, url, max_width=80):
        """Скачивает и подготавливает изображение для PDF"""
        
        if not url:
            return None
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # Открываем изображение
                img = PILImage.open(BytesIO(response.content))
                
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = PILImage.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Сохраняем в BytesIO
                img_byte_arr = BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=85)
                img_byte_arr.seek(0)
                
                # Создаем RLImage с адаптивной высотой (сохраняем пропорции)
                original_width, original_height = img.size
                aspect_ratio = original_height / original_width
                
                target_width = max_width * mm
                target_height = target_width * aspect_ratio
                
                rl_img = RLImage(img_byte_arr, width=target_width, height=target_height)
                return rl_img
            else:
                print(f"⚠️  Не удалось загрузить изображение: {url} (статус {response.status_code})")
                return None
        except Exception as e:
            print(f"⚠️  Ошибка загрузки изображения {url}: {e}")
            return None
    
    def generate(self, session_id, output_path=None):
        """Генерирует PDF файл коммерческого предложения"""
        
        print("📄 [KP PDF] Начинаю генерацию PDF...")
        
        # Получаем товары
        products = self.get_kp_items(session_id)
        
        if not products:
            raise ValueError("КП пусто - нет товаров для генерации")
        
        print(f"   Найдено товаров: {len(products)}")
        print(f"   Общее количество предложений: {sum(len(p['offers']) for p in products.values())}")
        
        # Создание PDF
        if output_path is None:
            output_dir = Path(__file__).parent / 'output'
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f'KP_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Элементы документа
        story = []
        
        # Заголовок
        story.append(Paragraph('КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ', self.title_style))
        story.append(Paragraph(f'от {datetime.now().strftime("%d.%m.%Y")}', self.date_style))
        story.append(Spacer(1, 10*mm))
        
        # Генерируем товары
        for idx, (product_id, product_data) in enumerate(products.items()):
            product_info = product_data['info']
            offers = product_data['offers']
            images = product_data['images']
            
            print(f"   Обрабатываю: {product_info['name']} ({len(offers)} вариантов, {len(images)} изображений)")
            
            # Загружаем изображения
            # Основное изображение (большое)
            main_image = None
            if images and len(images) > 0:
                main_image = self.download_image(images[0], max_width=90)
            
            # Дополнительные изображения (маленькие, горизонтально)
            additional_images = []
            for img_url in images[1:4]:  # До 3 дополнительных
                img = self.download_image(img_url, max_width=40)
                if img:
                    additional_images.append(img)
            
            # Создаем блок с изображениями
            if main_image:
                images_block = []
                # Основное изображение
                images_block.append(main_image)
                images_block.append(Spacer(1, 3*mm))
                
                # Дополнительные изображения снизу
                if additional_images:
                    # Горизонтальная таблица с доп. изображениями
                    add_img_table = Table([additional_images], colWidths=[40*mm]*len(additional_images))
                    add_img_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ]))
                    images_block.append(add_img_table)
                
                # Собираем в вертикальную таблицу
                images_cell = Table([[elem] for elem in images_block], colWidths=[90*mm])
                images_cell.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
            else:
                images_cell = Paragraph('Нет изображения', self.description_style)
            
            # ВЕРТИКАЛЬНАЯ СТРУКТУРА: изображения → название/описание → таблица
            product_elements = []
            
            # 1. Блок с изображениями (если есть)
            if images_cell:
                product_elements.append(images_cell)
                product_elements.append(Spacer(1, 5*mm))
            
            # 2. Название товара
            product_elements.append(Paragraph(product_info['name'], self.product_style))
            
            # 3. Описание
            if product_info['description']:
                desc_text = product_info['description'][:250] + ('...' if len(product_info['description']) > 250 else '')
                product_elements.append(Paragraph(desc_text, self.description_style))
            
            # 4. Информация об образце
            if product_info['sample_price'] or product_info['sample_delivery_time']:
                sample_parts = []
                if product_info['sample_price']:
                    sample_parts.append(f"Образец: ${product_info['sample_price']:.2f}")
                if product_info['sample_delivery_time']:
                    sample_parts.append(f"Срок: {product_info['sample_delivery_time']} дн.")
                product_elements.append(Paragraph(' | '.join(sample_parts), self.sample_style))
            
            product_elements.append(Spacer(1, 5*mm))
            
            # 5. Таблица ценовых предложений
            price_table_data = [
                ['Тираж', 'USD', 'RUB', 'Доставка', 'Срок']
            ]
            
            for offer in offers:
                price_table_data.append([
                    f"{offer['quantity']:,.0f} шт",
                    f"${offer['price_usd']:.2f}" if offer['price_usd'] else '-',
                    f"₽{offer['price_rub']:.2f}" if offer['price_rub'] else '-',
                    offer['route'] or '-',
                    f"{offer['delivery_days']} дн." if offer['delivery_days'] else '-'
                ])
            
            price_table = Table(price_table_data, colWidths=[34*mm, 28*mm, 34*mm, 28*mm, 22*mm])
            price_table.setStyle(TableStyle([
                # Заголовок (минималистичный серый стиль)
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),  # Светло-серый фон
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),   # Темно-серый текст
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), self.font_name_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                
                # Данные
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),  # Светло-серая граница
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),  # Чередование белый/светло-серый
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            product_elements.append(price_table)
            
            # Добавляем все элементы товара в story
            for elem in product_elements:
                story.append(elem)
            
            story.append(Spacer(1, 10*mm))
            
            # Page break после каждых 2 товаров (чтобы не было перегруза страницы)
            if (idx + 1) % 2 == 0 and idx + 1 < len(products):
                story.append(PageBreak())
        
        # Сохранение
        doc.build(story)
        print(f"✅ [KP PDF] Файл сохранен: {output_path}")
        
        return str(output_path)


def main():
    """Тестовая генерация"""
    
    # Для теста используем session_id из первого найденного КП
    from database.postgresql_manager import PostgreSQLManager
    from sqlalchemy import text
    
    db_manager = PostgreSQLManager()
    db_session = db_manager.get_session_direct()
    
    try:
        result = db_session.execute(text("""
            SELECT DISTINCT session_id 
            FROM kp_items 
            LIMIT 1
        """))
        
        row = result.fetchone()
        if not row:
            print("❌ Нет товаров в КП для теста")
            return
        
        session_id = row[0]
        print(f"🧪 Тестовая генерация для session_id: {session_id}")
        
        generator = KPPDFGenerator()
        output_path = generator.generate(session_id)
        
        print(f"✅ Файл создан: {output_path}")
    finally:
        db_session.close()


if __name__ == '__main__':
    main()


"""
Генератор Google Sheets коммерческого предложения
Группирует товары и показывает все варианты маршрутов для каждого товара
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Google Sheets API
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("⚠️  [Google Sheets] google-auth и google-api-python-client не установлены")


class KPGoogleSheetsGenerator:
    """Генератор Google Sheets файлов для коммерческого предложения"""
    
    def __init__(self):
        self.db_manager = PostgreSQLManager()
        self.sheets_service = None
        self.drive_service = None
        
        # Инициализация Google API
        if GOOGLE_AVAILABLE:
            self._init_google_api()
    
    def _init_google_api(self):
        """Инициализирует Google Sheets и Drive API"""
        try:
            # Получаем credentials из переменной окружения
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            
            if not creds_json:
                print("⚠️  [Google Sheets] GOOGLE_CREDENTIALS_JSON не найден в .env")
                return
            
            # Парсим JSON credentials
            creds_dict = json.loads(creds_json)
            
            # Создаем credentials
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            
            # Создаем сервисы
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            print("✅ [Google Sheets] API инициализирован")
            
        except Exception as e:
            print(f"❌ [Google Sheets] Ошибка инициализации API: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    def create_spreadsheet(self, title):
        """Создает новый Google Spreadsheet"""
        if not self.sheets_service:
            raise Exception("Google Sheets API не инициализирован")
        
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        
        spreadsheet = self.sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()
        
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        spreadsheet_url = spreadsheet.get('spreadsheetUrl')
        
        print(f"✅ [Google Sheets] Создана таблица: {spreadsheet_id}")
        
        # Делаем публичной с правами на редактирование
        self._make_public_editable(spreadsheet_id)
        
        return spreadsheet_id, spreadsheet_url
    
    def _make_public_editable(self, spreadsheet_id):
        """Делает Google Spreadsheet публичным с правами на редактирование"""
        if not self.drive_service:
            return
        
        try:
            # Устанавливаем права: anyone with link can edit
            permission = {
                'type': 'anyone',
                'role': 'writer'  # writer = редактор
            }
            
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission,
                fields='id'
            ).execute()
            
            print(f"✅ [Google Sheets] Установлены публичные права на редактирование")
            
        except Exception as e:
            print(f"⚠️  [Google Sheets] Ошибка установки прав: {e}")
    
    def update_cells(self, spreadsheet_id, range_name, values):
        """Обновляет ячейки в Google Spreadsheet"""
        if not self.sheets_service:
            raise Exception("Google Sheets API не инициализирован")
        
        body = {
            'values': values
        }
        
        result = self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        
        print(f"✅ [Google Sheets] Обновлено ячеек: {result.get('updatedCells')}")
        
        return result
    
    def format_sheet(self, spreadsheet_id):
        """Применяет форматирование к Google Spreadsheet"""
        if not self.sheets_service:
            return
        
        try:
            requests = []
            
            # 1. Заголовок документа (жирный, большой шрифт)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': 6
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'fontSize': 16,
                                'bold': True
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,horizontalAlignment)'
                }
            })
            
            # 2. Дата (курсив, центр)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': 2,
                        'startColumnIndex': 0,
                        'endColumnIndex': 6
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'italic': True
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,horizontalAlignment)'
                }
            })
            
            # 3. Автоподбор ширины колонок
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 6
                    }
                }
            })
            
            body = {
                'requests': requests
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            print(f"✅ [Google Sheets] Применено форматирование")
            
        except Exception as e:
            print(f"⚠️  [Google Sheets] Ошибка форматирования: {e}")
    
    def generate(self, session_id):
        """
        Генерирует Google Sheets КП
        
        Создает Google Spreadsheet с публичным доступом на редактирование
        """
        
        if not self.sheets_service:
            raise Exception("Google Sheets API не доступен. Проверьте GOOGLE_CREDENTIALS_JSON в .env")
        
        # Получаем данные
        products = self.get_kp_items(session_id)
        
        if not products:
            raise ValueError("КП пустое. Добавьте товары перед генерацией.")
        
        sheet_data = self.prepare_sheet_data(products)
        
        # Создаем Google Spreadsheet
        title = f'КП_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        spreadsheet_id, spreadsheet_url = self.create_spreadsheet(title)
        
        # Заполняем данными
        self.update_cells(spreadsheet_id, 'Sheet1!A1', sheet_data)
        
        # Применяем форматирование
        self.format_sheet(spreadsheet_id)
        
        print(f"✅ [Google Sheets] КП создано: {spreadsheet_url}")
        
        return {
            'spreadsheet_id': spreadsheet_id,
            'spreadsheet_url': spreadsheet_url,
            'title': title
        }


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


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
            
            print("🔍 [Google Sheets] GOOGLE_CREDENTIALS_JSON найден")
            print(f"   Длина: {len(creds_json)} символов")
            
            # Парсим JSON credentials
            try:
                creds_dict = json.loads(creds_json)
            except json.JSONDecodeError as e:
                # Возможно проблема с экранированием - попробуем исправить
                print(f"⚠️  [Google Sheets] Ошибка парсинга JSON, пробую исправить экранирование...")
                # Заменяем двойное экранирование на одинарное
                creds_json = creds_json.replace('\\\\n', '\\n')
                creds_dict = json.loads(creds_json)
            
            # Проверяем ключи
            required_keys = ['type', 'project_id', 'private_key', 'client_email']
            missing_keys = [k for k in required_keys if k not in creds_dict]
            
            if missing_keys:
                print(f"❌ [Google Sheets] Отсутствуют ключи в credentials: {missing_keys}")
                return
            
            # Проверяем private_key
            private_key = creds_dict.get('private_key', '')
            if '\\n' in private_key:
                print("🔧 [Google Sheets] Исправляю формат private_key (\\n -> настоящие переводы)")
                creds_dict['private_key'] = private_key.replace('\\n', '\n')
            
            print(f"✅ [Google Sheets] Credentials валидны")
            print(f"   Project ID: {creds_dict.get('project_id')}")
            print(f"   Client Email: {creds_dict.get('client_email')}")
            print(f"   Private Key: {'BEGIN PRIVATE KEY' in creds_dict.get('private_key', '')}")
            
            # Создаем credentials с РАСШИРЕННЫМИ правами
            credentials = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive',  # Полный Drive доступ
                    'https://www.googleapis.com/auth/drive.file'
                ]
            )
            
            print("🔧 [Google Sheets] Создаю API сервисы...")
            
            # Создаем сервисы
            self.sheets_service = build('sheets', 'v4', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            
            print("✅ [Google Sheets] API инициализирован успешно")
            
            # ТЕСТ: Пробуем простой запрос для проверки доступа
            try:
                print("🧪 [Google Sheets] Тестирую доступ к APIs...")
                # Простой тест - получение информации о несуществующей таблице
                # Если API не включен - получим 403
                # Если включен - получим 404 (что нормально для теста)
                test_id = "test_invalid_id_12345"
                try:
                    self.sheets_service.spreadsheets().get(spreadsheetId=test_id).execute()
                except HttpError as e:
                    if e.resp.status == 404:
                        print("✅ [Google Sheets] Доступ к Google Sheets API работает!")
                    elif e.resp.status == 403:
                        print("❌ [Google Sheets] НЕТ ДОСТУПА К APIs!")
                        print("\n⚠️  КРИТИЧЕСКИ ВАЖНО:")
                        print("   Google Sheets API или Google Drive API НЕ ВКЛЮЧЕНЫ!")
                        print("\n📝 ДЕЙСТВИЯ:")
                        print("   1. Открой: https://console.cloud.google.com")
                        print(f"   2. Выбери проект: {creds_dict.get('project_id')}")
                        print("   3. Перейди: APIs & Services → Library")
                        print("   4. Включи (ENABLE):")
                        print("      - Google Sheets API")
                        print("      - Google Drive API")
                        print("   5. Подожди 2-3 минуты")
                        print("   6. Перезапусти приложение")
                        print("\n📸 Проверь Dashboard: https://console.cloud.google.com/apis/dashboard")
                    else:
                        print(f"⚠️  [Google Sheets] Неожиданный ответ: {e.resp.status}")
            except Exception as test_error:
                print(f"⚠️  [Google Sheets] Не удалось протестировать доступ: {test_error}")
            
        except json.JSONDecodeError as e:
            print(f"❌ [Google Sheets] Ошибка парсинга JSON credentials: {e}")
            print("   Проверь что GOOGLE_CREDENTIALS_JSON - валидный JSON")
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
        """Создает новый Google Spreadsheet (с workaround через копирование template)"""
        if not self.sheets_service:
            raise Exception("Google Sheets API не инициализирован")
        
        # WORKAROUND: Пробуем скопировать существующий template вместо создания нового
        template_id = os.environ.get('GOOGLE_SHEETS_TEMPLATE_ID')
        
        if template_id:
            print(f"🔄 [Google Sheets] Пробую скопировать template: {template_id}")
            try:
                file_metadata = {
                    'name': title,
                    'mimeType': 'application/vnd.google-apps.spreadsheet'
                }
                
                result = self.drive_service.files().copy(
                    fileId=template_id,
                    body=file_metadata,
                    fields='id, webViewLink'
                ).execute()
                
                spreadsheet_id = result['id']
                spreadsheet_url = result['webViewLink']
                
                print(f"✅ [Google Sheets] Скопирован template!")
                print(f"   ID: {spreadsheet_id}")
                print(f"   URL: {spreadsheet_url}")
                
                # Делаем публичным с правами на редактирование
                self._make_public_editable(spreadsheet_id)
                
                return spreadsheet_id, spreadsheet_url
                
            except HttpError as copy_error:
                print(f"⚠️  [Google Sheets] Не удалось скопировать template: HTTP {copy_error.resp.status}")
                print(f"   Пробую создать новый файл...")
        
        # Если нет template или копирование не удалось - пробуем создать новый
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            print(f"📝 [Google Sheets] Создаю таблицу: {title}")
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId,spreadsheetUrl'
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            spreadsheet_url = spreadsheet.get('spreadsheetUrl')
            
            print(f"✅ [Google Sheets] Создана таблица: {spreadsheet_id}")
            print(f"   URL: {spreadsheet_url}")
            
            # Делаем публичной с правами на редактирование
            self._make_public_editable(spreadsheet_id)
            
            return spreadsheet_id, spreadsheet_url
            
        except HttpError as e:
            error_details = e.error_details if hasattr(e, 'error_details') else []
            print(f"❌ [Google Sheets] HTTP Error {e.resp.status}: {e._get_reason()}")
            print(f"   URI: {e.uri}")
            print(f"   Details: {error_details}")
            
            if e.resp.status == 403:
                print("\n🔍 ДИАГНОЗ: Organization Policy блокирует создание новых файлов!")
                print("\n💡 WORKAROUND: Используй TEMPLATE!")
                print("\n📝 ИНСТРУКЦИЯ:")
                print("1. Создай Google Sheet вручную:")
                print("   https://docs.google.com/spreadsheets/")
                print("   Название: 'КП Template'")
                print("\n2. Расшарь с Service Account (дай права Editor):")
                print(f"   {os.environ.get('GOOGLE_CREDENTIALS_JSON', '')[:100]}...")
                print("   (найди client_email в credentials)")
                print("\n3. Скопируй Spreadsheet ID из URL:")
                print("   https://docs.google.com/spreadsheets/d/[THIS_IS_ID]/edit")
                print("\n4. Добавь переменную на Railway:")
                print("   GOOGLE_SHEETS_TEMPLATE_ID = 'твой-template-id'")
                print("\n5. Перезапусти Railway - теперь будет копировать template вместо создания!")
            else:
                print("\n🔍 ДИАГНОСТИКА:")
                print("1. Проверь что Google Sheets API включен:")
                print("   https://console.cloud.google.com/apis/library/sheets.googleapis.com")
                print("2. Проверь что Service Account имеет права:")
                print("   https://console.cloud.google.com/iam-admin/serviceaccounts")
            
            raise
    
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


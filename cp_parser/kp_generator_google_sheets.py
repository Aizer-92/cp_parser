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
    from google.oauth2.credentials import Credentials
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
            # ПРИОРИТЕТ 1: OAuth Token (работает от имени пользователя)
            oauth_token = os.getenv('GOOGLE_OAUTH_TOKEN')
            
            if oauth_token:
                print("🔍 [Google Sheets] Найден GOOGLE_OAUTH_TOKEN - использую OAuth!")
                try:
                    token_dict = json.loads(oauth_token)
                    
                    # Создаем OAuth credentials
                    credentials = Credentials(
                        token=token_dict.get('token'),
                        refresh_token=token_dict.get('refresh_token'),
                        token_uri=token_dict.get('token_uri'),
                        client_id=token_dict.get('client_id'),
                        client_secret=token_dict.get('client_secret'),
                        scopes=token_dict.get('scopes')
                    )
                    
                    print("✅ [Google Sheets] OAuth credentials загружены")
                    print(f"   Client ID: {token_dict.get('client_id')[:50]}...")
                    print(f"   Scopes: {len(token_dict.get('scopes', []))} scopes")
                    
                    # Создаем сервисы
                    self.sheets_service = build('sheets', 'v4', credentials=credentials)
                    self.drive_service = build('drive', 'v3', credentials=credentials)
                    
                    print("✅ [Google Sheets] API инициализирован через OAuth!")
                    print("   Файлы будут создаваться от имени пользователя!")
                    return
                    
                except Exception as e:
                    print(f"❌ [Google Sheets] Ошибка OAuth: {e}")
                    print("   Пробую Service Account...")
            
            # ПРИОРИТЕТ 2: Service Account (fallback)
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            
            if not creds_json:
                print("⚠️  [Google Sheets] Ни GOOGLE_OAUTH_TOKEN, ни GOOGLE_CREDENTIALS_JSON не найдены")
                print("   Создание Google Sheets недоступно")
                return
            
            print("🔍 [Google Sheets] Использую Service Account")
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
            
            print(f"✅ [Google Sheets] Service Account credentials валидны")
            print(f"   Project ID: {creds_dict.get('project_id')}")
            print(f"   Client Email: {creds_dict.get('client_email')}")
            
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
            
            print("⚠️  [Google Sheets] Service Account имеет ограничение 0GB квоты!")
            print("   Рекомендуется использовать OAuth (GOOGLE_OAUTH_TOKEN)")
            
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
        """Подготавливает данные для Google Sheets - ТАБЛИЧНЫЙ формат"""
        
        rows = []
        merge_requests = []  # Для объединения ячеек
        current_row = 0
        
        # Заголовок документа
        rows.append(['КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ'])
        current_row += 1
        rows.append([f'от {datetime.now().strftime("%d.%m.%Y")}'])
        current_row += 1
        rows.append([''])  # Пустая строка
        current_row += 1
        
        # ЗАГОЛОВОК ТАБЛИЦЫ
        rows.append(['Фото', 'Название', 'Дизайн', 'Характеристики', 'Тираж', 'USD/шт', 'RUB/шт', 'Маршрут', 'Срок', 'Доп. фото'])
        current_row += 1
        
        # Генерируем товары
        for product_id, product_data in products_grouped.items():
            product_info = product_data['info']
            offers = product_data['offers']
            images = product_data['images']
            
            print(f"   Обрабатываю: {product_info['name']} ({len(offers)} вариантов, {len(images)} изображений)")
            
            # Подготовка данных
            main_image = f'=IMAGE("{images[0]}"; 2)' if images else ''
            design_image = f'=IMAGE("{images[1]}"; 1)' if len(images) > 1 else ''
            
            # Характеристики в одной ячейке
            characteristics = []
            if product_info['description']:
                characteristics.append(product_info['description'][:150])
            # Добавляем образец если есть
            if product_info['sample_price']:
                characteristics.append(f"Образец: ${product_info['sample_price']:.2f}")
            if product_info['sample_delivery_time']:
                characteristics.append(f"Срок образца: {product_info['sample_delivery_time']} дн.")
            characteristics_text = '\n'.join(characteristics) if characteristics else '-'
            
            # Дополнительные фото (3-4-5 изображения)
            additional_photos = []
            if len(images) > 2:
                for img_url in images[2:6]:  # До 4 дополнительных
                    additional_photos.append(f'=IMAGE("{img_url}"; 1)')
            additional_photos_text = ' '.join(additional_photos) if additional_photos else ''
            
            # Запоминаем начальную строку для merge
            start_row = current_row
            
            # Добавляем строки для каждого маршрута
            for idx, offer in enumerate(offers):
                if idx == 0:
                    # Первая строка - со всеми данными
                    row_data = [
                        main_image,  # Фото (будет объединено вертикально)
                        product_info['name'],  # Название
                        design_image,  # Дизайн
                        characteristics_text,  # Характеристики
                        f"{offer['quantity']:,.0f}".replace(',', ' '),  # Тираж
                        f"${offer['price_usd']:.2f}" if offer['price_usd'] else '-',  # USD
                        f"₽{offer['price_rub']:.2f}" if offer['price_rub'] else '-',  # RUB
                        offer['route'] or '-',  # Маршрут
                        f"{offer['delivery_days']} дн." if offer['delivery_days'] else '-',  # Срок
                        additional_photos_text  # Доп. фото (будет объединено)
                    ]
                else:
                    # Остальные строки - только цены и маршруты
                    row_data = [
                        '',  # Фото (пустая, будет merge)
                        '',  # Название (пустая)
                        '',  # Дизайн (пустая)
                        '',  # Характеристики (пустая)
                        f"{offer['quantity']:,.0f}".replace(',', ' '),  # Тираж
                        f"${offer['price_usd']:.2f}" if offer['price_usd'] else '-',  # USD
                        f"₽{offer['price_rub']:.2f}" if offer['price_rub'] else '-',  # RUB
                        offer['route'] or '-',  # Маршрут
                        f"{offer['delivery_days']} дн." if offer['delivery_days'] else '-',  # Срок
                        ''  # Доп. фото (пустая, будет merge)
                    ]
                
                rows.append(row_data)
                current_row += 1
            
            # Запоминаем merge для фото и доп. фото (колонки 0 и 9)
            if len(offers) > 1:
                end_row = current_row - 1
                # Merge для основного фото (колонка A = 0)
                merge_requests.append({
                    'startRowIndex': start_row,
                    'endRowIndex': end_row + 1,
                    'startColumnIndex': 0,
                    'endColumnIndex': 1
                })
                # Merge для названия (колонка B = 1)
                merge_requests.append({
                    'startRowIndex': start_row,
                    'endRowIndex': end_row + 1,
                    'startColumnIndex': 1,
                    'endColumnIndex': 2
                })
                # Merge для дизайна (колонка C = 2)
                merge_requests.append({
                    'startRowIndex': start_row,
                    'endRowIndex': end_row + 1,
                    'startColumnIndex': 2,
                    'endColumnIndex': 3
                })
                # Merge для характеристик (колонка D = 3)
                merge_requests.append({
                    'startRowIndex': start_row,
                    'endRowIndex': end_row + 1,
                    'startColumnIndex': 3,
                    'endColumnIndex': 4
                })
                # Merge для доп. фото (колонка J = 9)
                merge_requests.append({
                    'startRowIndex': start_row,
                    'endRowIndex': end_row + 1,
                    'startColumnIndex': 9,
                    'endColumnIndex': 10
                })
        
        return rows, merge_requests
    
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
    
    def get_first_sheet_name(self, spreadsheet_id):
        """Получает имя первого листа в spreadsheet"""
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheets = spreadsheet.get('sheets', [])
            if sheets:
                first_sheet_title = sheets[0]['properties']['title']
                print(f"📄 [Google Sheets] Первый лист: '{first_sheet_title}'")
                return first_sheet_title
            
            # Fallback
            return 'Sheet1'
            
        except Exception as e:
            print(f"⚠️  [Google Sheets] Не удалось получить имя листа: {e}")
            return 'Sheet1'
    
    def create_spreadsheet(self, title):
        """Создает новый Google Spreadsheet в папке КП"""
        if not self.sheets_service:
            raise Exception("Google Sheets API не инициализирован")
        
        # ID папки КП (приоритет)
        kp_folder_id = os.environ.get('GOOGLE_DRIVE_KP_FOLDER_ID', '1JceijhZMn8myEpIA80dQ34tYTqF5NFsE')
        
        # Fallback на старую переменную
        if not kp_folder_id:
            kp_folder_id = os.environ.get('GOOGLE_DRIVE_SHARED_FOLDER_ID')
        
        shared_folder_id = kp_folder_id
        
        if shared_folder_id:
            print(f"📁 [Google Sheets] Создаю в расшаренной папке: {shared_folder_id}")
            try:
                file_metadata = {
                    'name': title,
                    'mimeType': 'application/vnd.google-apps.spreadsheet',
                    'parents': [shared_folder_id]  # Создаем СРАЗУ в папке!
                }
                
                result = self.drive_service.files().create(
                    body=file_metadata,
                    fields='id, webViewLink'
                ).execute()
                
                spreadsheet_id = result['id']
                spreadsheet_url = result['webViewLink']
                
                print(f"✅ [Google Sheets] Создан в папке!")
                print(f"   ID: {spreadsheet_id}")
                print(f"   URL: {spreadsheet_url}")
                
                # Делаем публичным с правами на редактирование
                self._make_public_editable(spreadsheet_id)
                
                return spreadsheet_id, spreadsheet_url
                
            except HttpError as folder_error:
                print(f"⚠️  [Google Sheets] Не удалось создать в папке: HTTP {folder_error.resp.status}")
                if 'storageQuotaExceeded' in str(folder_error.error_details):
                    print(f"❌ У Service Account закончилось место на Drive!")
                    print(f"   Используй GOOGLE_DRIVE_SHARED_FOLDER_ID с твоей расшаренной папкой!")
                print(f"   Пробую другие варианты...")
        
        # ПРИОРИТЕТ 2: Копировать существующий template
        template_id = os.environ.get('GOOGLE_SHEETS_TEMPLATE_ID')
        
        if template_id:
            print(f"🔄 [Google Sheets] Пробую скопировать template: {template_id}")
            try:
                file_metadata = {
                    'name': title,
                    'mimeType': 'application/vnd.google-apps.spreadsheet'
                }
                
                # Если есть папка - копируем сразу в нее
                if shared_folder_id:
                    file_metadata['parents'] = [shared_folder_id]
                
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
        
        # ПРИОРИТЕТ 3 (fallback): Создать новый в корне
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
    
    def apply_merge_cells(self, spreadsheet_id, merge_requests):
        """Применяет объединение ячеек"""
        if not self.sheets_service or not merge_requests:
            return
        
        try:
            requests = []
            for merge_range in merge_requests:
                requests.append({
                    'mergeCells': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': merge_range['startRowIndex'],
                            'endRowIndex': merge_range['endRowIndex'],
                            'startColumnIndex': merge_range['startColumnIndex'],
                            'endColumnIndex': merge_range['endColumnIndex']
                        },
                        'mergeType': 'MERGE_ALL'  # Объединить все ячейки
                    }
                })
            
            body = {'requests': requests}
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            print(f"✅ [Google Sheets] Применено {len(merge_requests)} объединений ячеек")
            
        except Exception as e:
            print(f"⚠️  [Google Sheets] Ошибка объединения ячеек: {e}")
    
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
                        'endColumnIndex': 10
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
                        'endColumnIndex': 10
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
            
            # 3. Заголовок таблицы (строка 4, жирный, серый фон)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 3,
                        'endRowIndex': 4,
                        'startColumnIndex': 0,
                        'endColumnIndex': 10
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 11
                            },
                            'horizontalAlignment': 'CENTER',
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,horizontalAlignment,backgroundColor)'
                }
            })
            
            # 4. Автоподбор ширины колонок (до 10 колонок для таблицы)
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 10
                    }
                }
            })
            
            # 5. Автоподбор высоты строк для таблицы
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'ROWS',
                        'startIndex': 0,
                        'endIndex': 1000
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
        
        sheet_data, merge_requests = self.prepare_sheet_data(products)
        
        # Создаем Google Spreadsheet
        title = f'КП_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        spreadsheet_id, spreadsheet_url = self.create_spreadsheet(title)
        
        # Получаем реальное имя первого листа
        first_sheet_name = self.get_first_sheet_name(spreadsheet_id)
        
        # Заполняем данными
        self.update_cells(spreadsheet_id, f'{first_sheet_name}!A1', sheet_data)
        
        # Применяем объединение ячеек
        if merge_requests:
            self.apply_merge_cells(spreadsheet_id, merge_requests)
        
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


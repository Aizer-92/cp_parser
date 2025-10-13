"""
WORKAROUND для создания Google Sheets КП

Вместо создания НОВОГО файла (403 ошибка):
- Копируем существующий template
- Или пишем в существующий файл

Это обходит Organization Policy ограничения
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def copy_existing_template(template_id: str, new_title: str):
    """
    Копирует существующий Google Sheet template
    
    Args:
        template_id: ID существующего Google Sheet для копирования
        new_title: Название нового файла
        
    Returns:
        (spreadsheet_id, spreadsheet_url)
    """
    import json
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        raise ValueError("GOOGLE_CREDENTIALS_JSON не найден")
    
    creds_dict = json.loads(creds_json)
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    
    drive_service = build('drive', 'v3', credentials=credentials)
    
    try:
        # Копируем существующий файл
        file_metadata = {
            'name': new_title,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        
        result = drive_service.files().copy(
            fileId=template_id,
            body=file_metadata,
            fields='id, webViewLink'
        ).execute()
        
        spreadsheet_id = result['id']
        spreadsheet_url = result['webViewLink']
        
        print(f"✅ Файл скопирован!")
        print(f"   ID: {spreadsheet_id}")
        print(f"   URL: {spreadsheet_url}")
        
        return spreadsheet_id, spreadsheet_url
        
    except HttpError as e:
        if e.resp.status == 403:
            print(f"❌ Ошибка 403: Нет прав для копирования файла")
            print(f"   Template ID: {template_id}")
            print(f"\n📝 РЕШЕНИЕ:")
            print(f"   1. Открой: https://docs.google.com/spreadsheets/d/{template_id}")
            print(f"   2. Share → Add: {creds_dict['client_email']}")
            print(f"   3. Дай права: Editor")
        else:
            print(f"❌ Ошибка {e.resp.status}: {e.error_details}")
        raise

def create_manual_workaround():
    """
    Инструкция по ручному созданию template
    """
    import json
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)
    
    print("\n" + "="*60)
    print("  WORKAROUND: СОЗДАНИЕ КП ЧЕРЕЗ TEMPLATE")
    print("="*60)
    
    print("\n📝 ИНСТРУКЦИЯ:")
    print("\n1. Создай Google Sheet вручную:")
    print("   https://docs.google.com/spreadsheets/")
    print("   Название: 'КП Template'")
    
    print("\n2. Расшарь с Service Account:")
    print("   Share → Add:")
    print(f"   {creds_dict['client_email']}")
    print("   Права: Editor")
    
    print("\n3. Скопируй Spreadsheet ID из URL:")
    print("   https://docs.google.com/spreadsheets/d/[THIS_IS_ID]/edit")
    
    print("\n4. Сохрани ID в переменную окружения:")
    print("   export GOOGLE_SHEETS_TEMPLATE_ID='your-template-id'")
    
    print("\n5. Используй copy_existing_template():")
    print("   template_id = os.environ.get('GOOGLE_SHEETS_TEMPLATE_ID')")
    print("   sheet_id, url = copy_existing_template(template_id, 'КП #123')")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    # Пример использования
    create_manual_workaround()
    
    # Тест копирования (раскомментируй когда будет template)
    # template_id = os.environ.get('GOOGLE_SHEETS_TEMPLATE_ID')
    # if template_id:
    #     copy_existing_template(template_id, 'TEST КП')
    # else:
    #     print("\n⚠️  GOOGLE_SHEETS_TEMPLATE_ID не найден")


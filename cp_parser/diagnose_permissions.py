#!/usr/bin/env python3
"""
Детальная проверка прав Service Account
"""

import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def test_read_existing_file():
    """Тест чтения существующего файла"""
    print("\n" + "="*60)
    print("  ТЕСТ 1: ЧТЕНИЕ СУЩЕСТВУЮЩЕГО ФАЙЛА")
    print("="*60)
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
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
        # Получаем список файлов
        results = drive_service.files().list(
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            print("❌ Нет доступных файлов")
            return None
        
        print(f"✅ Найдено файлов: {len(files)}")
        for f in files:
            print(f"   - {f['name']} ({f['mimeType']})")
        
        # Пробуем прочитать первый Google Sheets
        sheets_files = [f for f in files if 'spreadsheet' in f.get('mimeType', '')]
        
        if sheets_files:
            sheet_id = sheets_files[0]['id']
            print(f"\n🧪 Пробую прочитать таблицу: {sheets_files[0]['name']}")
            
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            try:
                sheet_metadata = sheets_service.spreadsheets().get(
                    spreadsheetId=sheet_id
                ).execute()
                
                print("✅ ЧТЕНИЕ СУЩЕСТВУЮЩЕГО ФАЙЛА РАБОТАЕТ!")
                return sheet_id
            except HttpError as e:
                print(f"❌ Ошибка чтения: HTTP {e.resp.status}")
                print(f"   {e.error_details}")
                return None
        else:
            print("⚠️  Нет Google Sheets файлов для теста")
            return None
            
    except HttpError as e:
        print(f"❌ Ошибка получения списка: HTTP {e.resp.status}")
        print(f"   {e.error_details}")
        return None

def test_write_to_existing_file(sheet_id):
    """Тест записи в существующий файл"""
    print("\n" + "="*60)
    print("  ТЕСТ 2: ЗАПИСЬ В СУЩЕСТВУЮЩИЙ ФАЙЛ")
    print("="*60)
    
    if not sheet_id:
        print("⚠️  Нет файла для теста записи")
        return False
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
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
    
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    try:
        # Пробуем записать в первую пустую ячейку
        print(f"🧪 Пробую записать в таблицу: {sheet_id}")
        
        result = sheets_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range='Sheet1!Z1',  # Далекая ячейка чтобы не испортить данные
            valueInputOption='RAW',
            body={'values': [['test']]}
        ).execute()
        
        print("✅ ЗАПИСЬ В СУЩЕСТВУЮЩИЙ ФАЙЛ РАБОТАЕТ!")
        print(f"   Обновлено ячеек: {result.get('updatedCells')}")
        
        # Очищаем тестовое значение
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=sheet_id,
            range='Sheet1!Z1'
        ).execute()
        
        return True
        
    except HttpError as e:
        print(f"❌ Ошибка записи: HTTP {e.resp.status}")
        print(f"   {e.error_details}")
        
        if e.resp.status == 403:
            print("\n🔍 ДИАГНОЗ: Service Account может ЧИТАТЬ, но не может ПИСАТЬ!")
            print("   Возможные причины:")
            print("   1. Файл принадлежит другому пользователю")
            print("   2. Файл не расшарен с Service Account с правами Editor")
            print("   3. Organization policy запрещает запись")
        
        return False

def test_create_in_shared_drive():
    """Тест создания файла в Shared Drive"""
    print("\n" + "="*60)
    print("  ТЕСТ 3: СОЗДАНИЕ В SHARED DRIVE")
    print("="*60)
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
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
        # Проверяем есть ли Shared Drives
        shared_drives = drive_service.drives().list().execute()
        
        drives = shared_drives.get('drives', [])
        
        if not drives:
            print("⚠️  Shared Drives не найдены")
            return False
        
        print(f"✅ Найдено Shared Drives: {len(drives)}")
        for d in drives:
            print(f"   - {d['name']}")
        
        # Пробуем создать файл в первом Shared Drive
        drive_id = drives[0]['id']
        print(f"\n🧪 Пробую создать файл в: {drives[0]['name']}")
        
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        spreadsheet = {
            'properties': {
                'title': f'TEST - Shared Drive - {creds_dict["project_id"]}'
            }
        }
        
        result = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()
        
        # Перемещаем в Shared Drive
        file_id = result['spreadsheetId']
        drive_service.files().update(
            fileId=file_id,
            addParents=drive_id,
            supportsAllDrives=True,
            fields='id, parents'
        ).execute()
        
        print("✅ СОЗДАНИЕ В SHARED DRIVE РАБОТАЕТ!")
        print(f"   URL: {result['spreadsheetUrl']}")
        
        # Удаляем тестовый файл
        drive_service.files().delete(
            fileId=file_id,
            supportsAllDrives=True
        ).execute()
        
        return True
        
    except HttpError as e:
        print(f"❌ Ошибка: HTTP {e.resp.status}")
        print(f"   {e.error_details}")
        return False

def test_domain_restrictions():
    """Проверка domain restrictions"""
    print("\n" + "="*60)
    print("  ПРОВЕРКА DOMAIN RESTRICTIONS")
    print("="*60)
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    creds_dict = json.loads(creds_json)
    
    client_email = creds_dict.get('client_email', '')
    
    print(f"Service Account: {client_email}")
    
    if '@' in client_email:
        domain = client_email.split('@')[1]
        print(f"Domain: {domain}")
        
        if 'iam.gserviceaccount.com' in domain:
            print("✅ Это стандартный Service Account domain")
            print("   (не должно быть domain restrictions)")
        else:
            print("⚠️  Нестандартный domain!")
            print("   Возможны domain restrictions!")
    
    return True

def main():
    """Главная функция"""
    print("\n" + "🔍 " * 30)
    print("ДЕТАЛЬНАЯ ДИАГНОСТИКА ПРАВ SERVICE ACCOUNT")
    print("🔍 " * 30)
    
    # Тест 1: Чтение
    sheet_id = test_read_existing_file()
    
    # Тест 2: Запись
    if sheet_id:
        test_write_to_existing_file(sheet_id)
    
    # Тест 3: Shared Drive
    test_create_in_shared_drive()
    
    # Проверка domain restrictions
    test_domain_restrictions()
    
    print("\n" + "="*60)
    print("  ИТОГИ")
    print("="*60)
    print("\nЕсли Service Account может:")
    print("✅ Читать существующие файлы")
    print("❌ Но НЕ может создавать новые")
    print("\nТо проблема в:")
    print("1. Organization Policy (ограничения на создание ресурсов)")
    print("2. Domain restrictions")
    print("3. Недостаточные права (хотя роль Owner должна давать все права)")
    print("\nРЕШЕНИЕ:")
    print("- Создай файл вручную в My Drive")
    print("- Расшарь его с Service Account email с правами Editor")
    print("- Записывай в этот файл вместо создания новых")

if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Диагностика проблем с Google Sheets API - 403 PERMISSION_DENIED

Этот скрипт проверяет:
1. Валидность JSON credentials
2. Формат private_key
3. Доступ к Google Sheets API
4. Доступ к Google Drive API
5. Настройки проекта
"""

import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def print_section(title):
    """Красиво печатаем заголовок секции"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_credentials_json():
    """Проверка JSON credentials"""
    print_section("1. ПРОВЕРКА JSON CREDENTIALS")
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    if not creds_json:
        print("❌ GOOGLE_CREDENTIALS_JSON не найден в переменных окружения!")
        return None
    
    print(f"✅ Переменная GOOGLE_CREDENTIALS_JSON найдена")
    print(f"   Длина: {len(creds_json)} символов")
    
    try:
        creds_dict = json.loads(creds_json)
        print("✅ JSON валиден")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return None
    
    # Проверяем обязательные поля
    required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 
                      'client_email', 'client_id', 'auth_uri', 'token_uri']
    
    print("\n📋 Обязательные поля:")
    for field in required_fields:
        if field in creds_dict:
            if field == 'private_key':
                # Проверяем формат private_key
                pk = creds_dict[field]
                if '\\n' in pk or '\\\\n' in pk:
                    print(f"   ⚠️  {field}: найден (но содержит экранированные \\n)")
                else:
                    print(f"   ✅ {field}: найден")
            else:
                print(f"   ✅ {field}: {creds_dict.get(field, 'N/A')[:50]}...")
        else:
            print(f"   ❌ {field}: ОТСУТСТВУЕТ!")
            return None
    
    return creds_dict

def check_private_key_format(creds_dict):
    """Проверка формата private_key"""
    print_section("2. ПРОВЕРКА ФОРМАТА PRIVATE_KEY")
    
    private_key = creds_dict.get('private_key', '')
    
    # Проверяем наличие BEGIN/END
    if 'BEGIN PRIVATE KEY' not in private_key:
        print("❌ private_key не содержит 'BEGIN PRIVATE KEY'")
        print("   Возможно ключ поврежден или некорректный формат")
        return False
    
    if 'END PRIVATE KEY' not in private_key:
        print("❌ private_key не содержит 'END PRIVATE KEY'")
        return False
    
    print("✅ Найдены маркеры BEGIN/END PRIVATE KEY")
    
    # Проверяем экранирование
    if '\\\\n' in private_key:
        print("⚠️  Найдено двойное экранирование \\\\n")
        print("   Это может вызывать проблемы!")
        return False
    
    if '\\n' in private_key:
        print("⚠️  Найдено экранирование \\n вместо настоящих переводов строк")
        print("   Попытаюсь исправить...")
        creds_dict['private_key'] = private_key.replace('\\n', '\n')
        print("✅ Исправлено!")
    
    # Проверяем количество строк
    lines = private_key.split('\n')
    print(f"✅ Ключ содержит {len(lines)} строк")
    
    if len(lines) < 3:
        print("⚠️  Слишком мало строк! Возможно ключ поврежден")
        return False
    
    return True

def test_credentials_auth(creds_dict):
    """Тест аутентификации"""
    print_section("3. ТЕСТ АУТЕНТИФИКАЦИИ")
    
    try:
        # Исправляем private_key если нужно
        if '\\n' in creds_dict['private_key']:
            creds_dict['private_key'] = creds_dict['private_key'].replace('\\n', '\n')
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=scopes
        )
        
        print("✅ Credentials созданы успешно")
        print(f"   Service Account: {creds_dict['client_email']}")
        print(f"   Project ID: {creds_dict['project_id']}")
        
        return credentials
    
    except Exception as e:
        print(f"❌ Ошибка создания credentials: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        return None

def test_sheets_api(credentials):
    """Тест доступа к Google Sheets API"""
    print_section("4. ТЕСТ GOOGLE SHEETS API")
    
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        print("✅ Service объект создан")
        
        # Пробуем простой запрос к несуществующей таблице
        test_id = "test_invalid_id_12345"
        try:
            sheets_service.spreadsheets().get(spreadsheetId=test_id).execute()
            print("⚠️  Неожиданно: запрос прошел без ошибки")
        except HttpError as e:
            if e.resp.status == 404:
                print("✅ Google Sheets API РАБОТАЕТ!")
                print("   (404 Not Found - это нормально для тестового ID)")
                return True
            elif e.resp.status == 403:
                print("❌ Google Sheets API НЕ ДОСТУПЕН!")
                print(f"   HTTP 403: {e.error_details}")
                print("\n🔍 ВОЗМОЖНЫЕ ПРИЧИНЫ:")
                print("   1. API не включен в Google Cloud Console")
                print("   2. APIs включены в ДРУГОМ проекте (не там где Service Account)")
                print("   3. Billing не настроен (требуется привязка карты)")
                print("   4. Service Account не имеет прав (нужна роль Editor или Owner)")
                print("\n📝 ПРОВЕРЬ:")
                print(f"   - Проект: {credentials.project_id}")
                print("   - APIs Dashboard: https://console.cloud.google.com/apis/dashboard")
                print("   - Billing: https://console.cloud.google.com/billing")
                print("   - IAM: https://console.cloud.google.com/iam-admin/iam")
                return False
            else:
                print(f"⚠️  Неожиданный статус: {e.resp.status}")
                print(f"   Детали: {e.error_details}")
                return False
    
    except Exception as e:
        print(f"❌ Ошибка при тесте API: {e}")
        return False

def test_drive_api(credentials):
    """Тест доступа к Google Drive API"""
    print_section("5. ТЕСТ GOOGLE DRIVE API")
    
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Service объект создан")
        
        # Пробуем получить список файлов (пустой результат это нормально)
        try:
            results = drive_service.files().list(pageSize=1).execute()
            print("✅ Google Drive API РАБОТАЕТ!")
            print(f"   Найдено файлов: {len(results.get('files', []))}")
            return True
        except HttpError as e:
            if e.resp.status == 403:
                print("❌ Google Drive API НЕ ДОСТУПЕН!")
                print(f"   HTTP 403: {e.error_details}")
                return False
            else:
                print(f"⚠️  Статус: {e.resp.status}")
                print(f"   Детали: {e.error_details}")
                return False
    
    except Exception as e:
        print(f"❌ Ошибка при тесте API: {e}")
        return False

def test_create_spreadsheet(credentials, creds_dict):
    """Тест создания Google Sheet"""
    print_section("6. ТЕСТ СОЗДАНИЯ GOOGLE SHEET")
    
    try:
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        spreadsheet = {
            'properties': {
                'title': f'TEST - Diagnostic Script - {creds_dict["project_id"]}'
            }
        }
        
        print("🧪 Пробую создать тестовую таблицу...")
        result = sheets_service.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()
        
        print("✅ УСПЕХ! Таблица создана!")
        print(f"   ID: {result['spreadsheetId']}")
        print(f"   URL: {result['spreadsheetUrl']}")
        
        print("\n🗑️  Пробую удалить тестовую таблицу...")
        try:
            drive_service = build('drive', 'v3', credentials=credentials)
            drive_service.files().delete(fileId=result['spreadsheetId']).execute()
            print("✅ Тестовая таблица удалена")
        except:
            print("⚠️  Не удалось удалить, но это не критично")
            print(f"   Удали вручную: {result['spreadsheetUrl']}")
        
        return True
    
    except HttpError as e:
        print(f"❌ Ошибка создания таблицы!")
        print(f"   HTTP {e.resp.status}: {e.error_details}")
        
        if e.resp.status == 403:
            print("\n🔍 ДИАГНОЗ: ПРОБЛЕМА С ПРАВАМИ!")
            print("\n📝 ЧТО ПРОВЕРИТЬ:")
            print("   1. BILLING:")
            print(f"      https://console.cloud.google.com/billing/linkedaccount?project={creds_dict['project_id']}")
            print("      Должен быть привязан платежный аккаунт (даже для бесплатного использования)")
            print()
            print("   2. IAM РОЛИ:")
            print(f"      https://console.cloud.google.com/iam-admin/iam?project={creds_dict['project_id']}")
            print(f"      Service Account {creds_dict['client_email']} должен иметь роль:")
            print("      - Editor ИЛИ")
            print("      - Owner ИЛИ")
            print("      - Конкретные роли: 'Drive File Creator' + 'Sheets Editor'")
            print()
            print("   3. APIS ENABLED В ПРАВИЛЬНОМ ПРОЕКТЕ:")
            print(f"      https://console.cloud.google.com/apis/dashboard?project={creds_dict['project_id']}")
            print("      Должны быть включены: Google Sheets API, Google Drive API")
        
        return False
    
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def main():
    """Главная функция диагностики"""
    print("\n" + "🔍 " * 30)
    print("ДИАГНОСТИКА GOOGLE SHEETS API - 403 PERMISSION_DENIED")
    print("🔍 " * 30)
    
    # 1. Проверка JSON
    creds_dict = check_credentials_json()
    if not creds_dict:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Невалидный JSON credentials")
        sys.exit(1)
    
    # 2. Проверка private_key
    if not check_private_key_format(creds_dict):
        print("\n⚠️  ПРЕДУПРЕЖДЕНИЕ: Проблемы с форматом private_key")
    
    # 3. Тест аутентификации
    credentials = test_credentials_auth(creds_dict)
    if not credentials:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось создать credentials")
        sys.exit(1)
    
    # 4-5. Тест APIs
    sheets_ok = test_sheets_api(credentials)
    drive_ok = test_drive_api(credentials)
    
    if not sheets_ok or not drive_ok:
        print("\n❌ ОДИН ИЛИ ОБА API НЕ РАБОТАЮТ!")
        print("\n📋 ФИНАЛЬНЫЕ РЕКОМЕНДАЦИИ:")
        print("   1. Проверь что выбран ПРАВИЛЬНЫЙ ПРОЕКТ в Google Cloud Console")
        print(f"      Project ID: {creds_dict['project_id']}")
        print("   2. Включи APIs в этом проекте (не в другом!)")
        print("   3. Настрой Billing (привяжи карту)")
        print("   4. Дай Service Account роль Editor или Owner")
        sys.exit(1)
    
    # 6. Тест создания таблицы
    if not test_create_spreadsheet(credentials, creds_dict):
        print("\n❌ ФИНАЛЬНЫЙ ТЕСТ НЕ ПРОЙДЕН!")
        print("   APIs работают, но создать таблицу не удалось")
        print("   Скорее всего проблема с Billing или IAM ролями")
        sys.exit(1)
    
    # Успех!
    print_section("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("\n🎉 Google Sheets API полностью настроен и работает!")
    print(f"   Project ID: {creds_dict['project_id']}")
    print(f"   Service Account: {creds_dict['client_email']}")
    print("\n✅ Можно использовать в продакшене!")

if __name__ == '__main__':
    main()


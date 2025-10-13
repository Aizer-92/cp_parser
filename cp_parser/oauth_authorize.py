#!/usr/bin/env python3
"""
OAuth авторизация для Google Sheets/Drive

Запусти этот скрипт ЛОКАЛЬНО чтобы получить token.json
"""

import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes для полного доступа к Drive и Sheets
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def authorize():
    """Получает OAuth credentials через браузер"""
    
    print("\n" + "="*60)
    print("  OAUTH АВТОРИЗАЦИЯ")
    print("="*60)
    
    creds = None
    token_file = 'token.json'
    credentials_file = 'oauth_credentials.json'
    
    # Проверяем есть ли уже токен
    if os.path.exists(token_file):
        print(f"\n✅ Найден существующий token: {token_file}")
        print("   Проверяю валидность...")
        
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        
        if creds and creds.valid:
            print("✅ Token валиден!")
            return creds
        
        if creds and creds.expired and creds.refresh_token:
            print("⚠️  Token истек, обновляю...")
            try:
                creds.refresh(Request())
                
                # Сохраняем обновленный токен
                with open(token_file, 'w') as f:
                    f.write(creds.to_json())
                
                print("✅ Token обновлен!")
                return creds
            except Exception as e:
                print(f"❌ Ошибка обновления: {e}")
                print("   Нужна повторная авторизация...")
                creds = None
    
    # Проверяем есть ли OAuth credentials
    if not os.path.exists(credentials_file):
        print(f"\n❌ OAuth credentials не найдены!")
        print(f"\n📝 ИНСТРУКЦИЯ:")
        print(f"1. Открой: https://console.cloud.google.com/apis/credentials")
        print(f"2. Создай OAuth Client ID (Desktop app)")
        print(f"3. Скачай JSON файл")
        print(f"4. Сохрани как: {credentials_file}")
        print(f"\nПодробная инструкция: OAUTH_SETUP.md")
        return None
    
    # Запускаем OAuth flow
    print(f"\n🔐 Запускаю OAuth авторизацию...")
    print(f"   Откроется браузер для авторизации...")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_file,
            SCOPES
        )
        
        # Запускаем локальный сервер для получения кода
        creds = flow.run_local_server(
            port=8080,
            prompt='consent',
            success_message='✅ Авторизация успешна! Можешь закрыть эту вкладку.'
        )
        
        # Сохраняем token
        with open(token_file, 'w') as f:
            f.write(creds.to_json())
        
        print(f"\n✅ Авторизация успешна!")
        print(f"   Token сохранен: {token_file}")
        
        # Показываем содержимое для Railway
        print(f"\n📋 ДЛЯ RAILWAY:")
        print(f"   Скопируй содержимое {token_file} в переменную:")
        print(f"   GOOGLE_OAUTH_TOKEN")
        
        with open(token_file, 'r') as f:
            token_data = f.read()
        
        print(f"\n" + "="*60)
        print("СОДЕРЖИМОЕ (скопируй это):")
        print("="*60)
        print(token_data)
        print("="*60)
        
        return creds
        
    except Exception as e:
        print(f"\n❌ Ошибка авторизации: {e}")
        print(f"\nПроверь:")
        print(f"1. OAuth Consent Screen настроен")
        print(f"2. Твой email добавлен в Test users")
        print(f"3. APIs включены (Drive, Sheets)")
        return None

def test_credentials(creds):
    """Тестирует credentials"""
    
    print("\n" + "="*60)
    print("  ТЕСТ ДОСТУПА")
    print("="*60)
    
    from googleapiclient.discovery import build
    
    try:
        # Тест Drive API
        print("\n🧪 Тестирую Drive API...")
        drive = build('drive', 'v3', credentials=creds)
        
        results = drive.files().list(pageSize=5).execute()
        files = results.get('files', [])
        
        print(f"✅ Drive API работает!")
        print(f"   Найдено файлов: {len(files)}")
        
        # Тест Sheets API
        print("\n🧪 Тестирую Sheets API...")
        sheets = build('sheets', 'v4', credentials=creds)
        
        # Пробуем создать тестовый файл
        spreadsheet = {
            'properties': {
                'title': 'TEST - OAuth Authorization'
            }
        }
        
        result = sheets.spreadsheets().create(
            body=spreadsheet,
            fields='spreadsheetId,spreadsheetUrl'
        ).execute()
        
        print(f"✅ Sheets API работает!")
        print(f"   Создан тестовый файл:")
        print(f"   ID: {result['spreadsheetId']}")
        print(f"   URL: {result['spreadsheetUrl']}")
        
        # Удаляем тестовый файл
        print(f"\n🗑️  Удаляю тестовый файл...")
        drive.files().delete(fileId=result['spreadsheetId']).execute()
        print(f"✅ Удалено")
        
        print("\n" + "="*60)
        print("  🎉 ВСЁ РАБОТАЕТ!")
        print("="*60)
        print("\n✅ OAuth credentials настроены правильно!")
        print("✅ Можно добавлять token.json на Railway!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка теста: {e}")
        return False

if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              OAUTH АВТОРИЗАЦИЯ ДЛЯ GOOGLE                ║
║                                                           ║
║  Этот скрипт поможет получить OAuth token для работы     ║
║  с Google Drive и Sheets от твоего имени.                ║
║                                                           ║
║  После авторизации файлы будут создаваться как           ║
║  будто ТЫ сам их создаешь - используется ТВОЯ квота!    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    creds = authorize()
    
    if creds:
        test_credentials(creds)
    else:
        print("\n❌ Авторизация не удалась")
        print("   Прочитай инструкцию: OAUTH_SETUP.md")


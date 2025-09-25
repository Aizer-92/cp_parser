#!/usr/bin/env python3
"""
Скачивание больших Google Sheets таблиц через Sheets API
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import time

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config import GOOGLE_SCOPES
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def get_sheets_service():
    """Создание сервиса Google Sheets API"""
    try:
        credentials_path = project_root / 'credentials' / 'service_account.json'
        credentials = Credentials.from_service_account_file(
            str(credentials_path),
            scopes=GOOGLE_SCOPES
        )
        service = build('sheets', 'v4', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Ошибка создания Google Sheets сервиса: {e}")
        return None

def extract_sheet_id(url):
    """Извлечение ID таблицы из URL"""
    try:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split('/')
        if 'd' in path_parts:
            sheet_id_index = path_parts.index('d') + 1
            if sheet_id_index < len(path_parts):
                return path_parts[sheet_id_index]
        return None
    except Exception as e:
        print(f"❌ Ошибка извлечения ID: {e}")
        return None

def download_large_sheet(sheet_url, sheet_title=None):
    """Скачивание большой таблицы через Sheets API"""
    
    print(f"🔄 Скачивание большой таблицы: {sheet_url}")
    
    try:
        # Извлекаем ID таблицы
        sheet_id = extract_sheet_id(sheet_url)
        if not sheet_id:
            return None
        
        print(f"📋 ID таблицы: {sheet_id}")
        
        # Создаем сервис Google Sheets
        sheets_service = get_sheets_service()
        if not sheets_service:
            return None
        
        # Получаем информацию о таблице
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheet_properties = sheet_metadata.get('sheets', [])
        
        print(f"📊 Найдено листов: {len(sheet_properties)}")
        
        # Создаем директорию для Excel файлов
        excel_dir = project_root / 'storage' / 'excel_files'
        excel_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем имя файла
        if not sheet_title:
            sheet_title = f"large_sheet_{sheet_id[:8]}"
        
        timestamp = int(time.time())
        filename = f"{sheet_title}_{timestamp}.xlsx"
        excel_path = excel_dir / filename
        
        # Создаем Excel файл с несколькими листами
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            
            for sheet_prop in sheet_properties:
                sheet_name = sheet_prop.get('properties', {}).get('title', 'Sheet1')
                print(f"📄 Обрабатываем лист: {sheet_name}")
                
                # Получаем данные листа
                range_name = f"{sheet_name}!A:ZZ"  # Читаем все данные
                result = sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=range_name
                ).execute()
                
                values = result.get('values', [])
                
                if values:
                    # Преобразуем в DataFrame
                    df = pd.DataFrame(values)
                    
                    # Сохраняем в Excel
                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                    print(f"  ✅ Сохранено {len(values)} строк")
                else:
                    print(f"  ⚠️ Лист пустой")
        
        print(f"✅ Файл сохранен: {excel_path}")
        return str(excel_path)
        
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Тестирование скачивания большой таблицы"""
    
    # URL большой таблицы
    large_sheet_url = "https://docs.google.com/spreadsheets/d/1iB1J0TJevoHzrduqeySqO6gI_xLdhSDV9jxOdKICDY8/edit?gid=1464438736#gid=1464438736"
    
    print("🚀 Скачивание большой таблицы через Sheets API")
    print("=" * 50)
    
    result = download_large_sheet(large_sheet_url, "Мерч для Sense")
    
    if result:
        print(f"✅ Успешно скачано: {result}")
    else:
        print(f"❌ Не удалось скачать таблицу")

if __name__ == "__main__":
    main()

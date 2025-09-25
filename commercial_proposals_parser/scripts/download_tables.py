#!/usr/bin/env python3
"""
Скачивание Google Sheets таблиц в формате Excel
"""

import os
import sys
import json
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import time

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config import GOOGLE_SCOPES
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

def get_drive_service():
    """Создание сервиса Google Drive API"""
    try:
        credentials_path = project_root / 'credentials' / 'service_account.json'
        credentials = Credentials.from_service_account_file(
            str(credentials_path),
            scopes=GOOGLE_SCOPES
        )
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"❌ Ошибка создания Google Drive сервиса: {e}")
        return None

def extract_sheet_id(url):
    """Извлечение ID таблицы из URL"""
    try:
        # Парсим URL
        parsed_url = urlparse(url)
        
        # Ищем ID в пути
        path_parts = parsed_url.path.split('/')
        if 'd' in path_parts:
            sheet_id_index = path_parts.index('d') + 1
            if sheet_id_index < len(path_parts):
                sheet_id = path_parts[sheet_id_index]
                return sheet_id
        
        # Альтернативный способ - поиск в query параметрах
        query_params = parse_qs(parsed_url.query)
        if 'id' in query_params:
            return query_params['id'][0]
        
        print(f"❌ Не удалось извлечь ID из URL: {url}")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка извлечения ID: {e}")
        return None

def download_sheet_as_excel(sheet_url, sheet_title=None):
    """Скачивание Google Sheets таблицы в формате Excel"""
    
    print(f"🔄 Скачивание таблицы: {sheet_url}")
    
    try:
        # Извлекаем ID таблицы
        sheet_id = extract_sheet_id(sheet_url)
        if not sheet_id:
            return None
        
        print(f"📋 ID таблицы: {sheet_id}")
        
        # Создаем сервис Google Drive
        drive_service = get_drive_service()
        if not drive_service:
            return None
        
        # Скачиваем файл в формате Excel
        request = drive_service.files().export_media(
            fileId=sheet_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        # Создаем директорию для Excel файлов
        excel_dir = project_root / 'storage' / 'excel_files'
        excel_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем имя файла
        if not sheet_title:
            sheet_title = f"sheet_{sheet_id[:8]}"
        
        timestamp = int(time.time())
        filename = f"{sheet_title}_{timestamp}.xlsx"
        excel_path = excel_dir / filename
        
        # Скачиваем файл
        with open(excel_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    print(f"📥 Прогресс: {int(status.progress() * 100)}%")
        
        print(f"✅ Файл скачан: {excel_path}")
        return str(excel_path)
        
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return None

def load_sheets_config():
    """Загрузка конфигурации таблиц"""
    config_path = project_root / 'sheets_config.json'
    
    if not config_path.exists():
        # Создаем конфигурацию по умолчанию
        default_config = {
            "sheets": [
                {
                    "title": "Мерч для Sense",
                    "description": "Таблица с мерчем для Sense (худи, шапки, шопперы, брелоки)",
                    "url": "https://docs.google.com/spreadsheets/d/1iB1J0TJevoHzrduqeySqO6gI_xLdhSDV9jxOdKICDY8/edit?gid=1464438736#gid=1464438736",
                    "downloaded": False,
                    "excel_path": None,
                    "last_download": None
                },
                {
                    "title": "Вторая таблица",
                    "description": "Вторая тестовая таблица для парсинга",
                    "url": "https://docs.google.com/spreadsheets/d/13DOK6_4ox-pmqurespTyWkAuHezBnHsbqFxAfIFnXd4/edit?gid=1628889079#gid=1628889079",
                    "downloaded": False,
                    "excel_path": None,
                    "last_download": None
                }
            ]
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        print(f"📝 Создан файл конфигурации: {config_path}")
        return default_config
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_sheets_config(config):
    """Сохранение конфигурации таблиц"""
    config_path = project_root / 'sheets_config.json'
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def download_all_sheets():
    """Скачивание всех таблиц из конфигурации"""
    
    print("🚀 Скачивание Google Sheets таблиц")
    print("=" * 50)
    
    config = load_sheets_config()
    
    downloaded_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, sheet in enumerate(config['sheets'], 1):
        print(f"\n📊 Таблица {i}/{len(config['sheets'])}: {sheet['title']}")
        print(f"📝 Описание: {sheet['description']}")
        print(f"🔗 URL: {sheet['url']}")
        print("-" * 50)
        
        # Проверяем, нужно ли скачивать
        if sheet.get('downloaded', False) and sheet.get('excel_path') and Path(sheet['excel_path']).exists():
            print(f"⏭️  Таблица уже скачана: {sheet['excel_path']}")
            skipped_count += 1
            continue
        
        # Скачиваем таблицу
        excel_path = download_sheet_as_excel(sheet['url'], sheet['title'])
        
        if excel_path:
            # Обновляем конфигурацию
            sheet['downloaded'] = True
            sheet['excel_path'] = excel_path
            sheet['last_download'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            downloaded_count += 1
            print(f"✅ Таблица {i} скачана успешно")
        else:
            error_count += 1
            print(f"❌ Ошибка при скачивании таблицы {i}")
    
    # Сохраняем обновленную конфигурацию
    save_sheets_config(config)
    
    print(f"\n📊 Итоговые результаты:")
    print(f"  - Всего таблиц: {len(config['sheets'])}")
    print(f"  - Скачано: {downloaded_count}")
    print(f"  - Пропущено: {skipped_count}")
    print(f"  - Ошибок: {error_count}")
    
    if downloaded_count > 0 or skipped_count > 0:
        print(f"\n✅ Скачивание завершено! Можно переходить к анализу.")
    else:
        print(f"\n❌ Не удалось скачать ни одной таблицы")

if __name__ == "__main__":
    download_all_sheets()

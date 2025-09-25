#!/usr/bin/env python3
"""
Скачивание Google Sheets таблиц в формате Excel
"""

import os
import sys
import requests
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

def get_google_service():
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
        print(f"❌ Ошибка создания Google сервиса: {e}")
        return None

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

def main():
    """Тестирование скачивания"""
    
    # Тестовые URL
    test_urls = [
        'https://docs.google.com/spreadsheets/d/1iB1J0TJevoHzrduqeySqO6gI_xLdhSDV9jxOdKICDY8/edit?gid=1464438736#gid=1464438736',
        'https://docs.google.com/spreadsheets/d/13DOK6_4ox-pmqurespTyWkAuHezBnHsbqFxAfIFnXd4/edit?gid=1628889079#gid=1628889079'
    ]
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📊 Тест {i}: {url}")
        result = download_sheet_as_excel(url, f"test_sheet_{i}")
        if result:
            print(f"✅ Успешно скачан: {result}")
        else:
            print(f"❌ Ошибка скачивания")

if __name__ == "__main__":
    main()

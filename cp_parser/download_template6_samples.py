#!/usr/bin/env python3
"""
Скачивание образцов файлов для анализа Шаблона 6
"""

import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload

# Настройки
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 
          'https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service_account.json'

def download_excel(table_id, output_dir):
    """Скачивает Google Sheets как Excel"""
    try:
        # Авторизация
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Скачиваем как Excel
        request = drive_service.files().export_media(
            fileId=table_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        output_path = output_dir / f"{table_id}.xlsx"
        
        with io.FileIO(output_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        file_size = output_path.stat().st_size / 1024
        return True, file_size
        
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("📥 СКАЧИВАНИЕ ОБРАЗЦОВ ДЛЯ ШАБЛОНА 6")
    print("=" * 80)
    
    # Создаем директорию
    output_dir = Path('template6_samples')
    output_dir.mkdir(exist_ok=True)
    
    # Загружаем список
    with open('template6_sample_ids.txt', 'r') as f:
        table_ids = [line.strip() for line in f if line.strip()]
    
    print(f"\n📋 К скачиванию: {len(table_ids)} файлов")
    print(f"📁 Директория: {output_dir}\n")
    
    success = 0
    failed = 0
    
    for i, table_id in enumerate(table_ids, 1):
        print(f"[{i}/{len(table_ids)}] {table_id[:30]}... ", end='', flush=True)
        
        ok, result = download_excel(table_id, output_dir)
        
        if ok:
            print(f"✅ {result:.1f} KB")
            success += 1
        else:
            print(f"❌ {result}")
            failed += 1
    
    print(f"\n" + "=" * 80)
    print(f"📊 РЕЗУЛЬТАТ:")
    print(f"  ✅ Скачано: {success}")
    print(f"  ❌ Ошибок: {failed}")
    print("=" * 80)

if __name__ == '__main__':
    main()




"""
Скачивание образцов файлов для анализа Шаблона 6
"""

import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
from googleapiclient.http import MediaIoBaseDownload

# Настройки
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 
          'https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'service_account.json'

def download_excel(table_id, output_dir):
    """Скачивает Google Sheets как Excel"""
    try:
        # Авторизация
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=creds)
        
        # Скачиваем как Excel
        request = drive_service.files().export_media(
            fileId=table_id,
            mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
        output_path = output_dir / f"{table_id}.xlsx"
        
        with io.FileIO(output_path, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
        
        file_size = output_path.stat().st_size / 1024
        return True, file_size
        
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 80)
    print("📥 СКАЧИВАНИЕ ОБРАЗЦОВ ДЛЯ ШАБЛОНА 6")
    print("=" * 80)
    
    # Создаем директорию
    output_dir = Path('template6_samples')
    output_dir.mkdir(exist_ok=True)
    
    # Загружаем список
    with open('template6_sample_ids.txt', 'r') as f:
        table_ids = [line.strip() for line in f if line.strip()]
    
    print(f"\n📋 К скачиванию: {len(table_ids)} файлов")
    print(f"📁 Директория: {output_dir}\n")
    
    success = 0
    failed = 0
    
    for i, table_id in enumerate(table_ids, 1):
        print(f"[{i}/{len(table_ids)}] {table_id[:30]}... ", end='', flush=True)
        
        ok, result = download_excel(table_id, output_dir)
        
        if ok:
            print(f"✅ {result:.1f} KB")
            success += 1
        else:
            print(f"❌ {result}")
            failed += 1
    
    print(f"\n" + "=" * 80)
    print(f"📊 РЕЗУЛЬТАТ:")
    print(f"  ✅ Скачано: {success}")
    print(f"  ❌ Ошибок: {failed}")
    print("=" * 80)

if __name__ == '__main__':
    main()












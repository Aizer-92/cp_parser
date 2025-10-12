#!/usr/bin/env python3
"""
Скачивание Excel файлов для проектов без изображений
"""

import sys
from pathlib import Path
from sqlalchemy import text
import gspread
from google.oauth2.service_account import Credentials
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def download_excel(table_id, output_path):
    """Скачивает Excel файл из Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Открываем таблицу
        spreadsheet = client.open_by_key(table_id)
        
        # Скачиваем как Excel
        url = f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=xlsx"
        
        import requests
        response = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'})
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"    ❌ Ошибка скачивания: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
        return False

def main():
    print("=" * 80)
    print("📥 СКАЧИВАНИЕ EXCEL ФАЙЛОВ ДЛЯ ПРОЕКТОВ БЕЗ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    
    # Читаем списки
    template4_missing = []
    with open('missing_images_template4.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                template4_missing.append((int(parts[0]), parts[1]))
    
    template5_missing = []
    with open('missing_images_template5.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                template5_missing.append((int(parts[0]), parts[1]))
    
    all_missing = template4_missing + template5_missing
    
    print(f"\n📊 К скачиванию:")
    print(f"  Шаблон 4: {len(template4_missing)} файлов")
    print(f"  Шаблон 5: {len(template5_missing)} файлов")
    print(f"  ВСЕГО: {len(all_missing)} файлов")
    
    # Создаем директорию если нет
    storage_dir = Path('storage/excel_files')
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🚀 Начинаю скачивание...")
    
    downloaded = 0
    skipped = 0
    errors = 0
    
    for idx, (proj_id, table_id) in enumerate(all_missing, 1):
        output_path = storage_dir / f"{table_id}.xlsx"
        
        # Проверяем существование
        if output_path.exists():
            print(f"  [{idx}/{len(all_missing)}] ⏩ Проект {proj_id}: уже есть")
            skipped += 1
            continue
        
        print(f"  [{idx}/{len(all_missing)}] 📥 Проект {proj_id}...", end='')
        
        if download_excel(table_id, output_path):
            size_kb = output_path.stat().st_size / 1024
            print(f" ✅ {size_kb:.1f} KB")
            downloaded += 1
        else:
            errors += 1
            print()
        
        # Задержка между запросами
        if idx % 10 == 0:
            time.sleep(1)
    
    print("\n" + "=" * 80)
    print("✅ СКАЧИВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    print(f"\n📊 Статистика:")
    print(f"  • Скачано:   {downloaded}")
    print(f"  • Пропущено: {skipped}")
    print(f"  • Ошибок:    {errors}")
    print(f"  • Всего:     {len(all_missing)}")
    print("=" * 80)

if __name__ == '__main__':
    main()




"""
Скачивание Excel файлов для проектов без изображений
"""

import sys
from pathlib import Path
from sqlalchemy import text
import gspread
from google.oauth2.service_account import Credentials
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def download_excel(table_id, output_path):
    """Скачивает Excel файл из Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        # Открываем таблицу
        spreadsheet = client.open_by_key(table_id)
        
        # Скачиваем как Excel
        url = f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=xlsx"
        
        import requests
        response = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'})
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"    ❌ Ошибка скачивания: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"    ❌ Ошибка: {e}")
        return False

def main():
    print("=" * 80)
    print("📥 СКАЧИВАНИЕ EXCEL ФАЙЛОВ ДЛЯ ПРОЕКТОВ БЕЗ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    
    # Читаем списки
    template4_missing = []
    with open('missing_images_template4.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                template4_missing.append((int(parts[0]), parts[1]))
    
    template5_missing = []
    with open('missing_images_template5.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                template5_missing.append((int(parts[0]), parts[1]))
    
    all_missing = template4_missing + template5_missing
    
    print(f"\n📊 К скачиванию:")
    print(f"  Шаблон 4: {len(template4_missing)} файлов")
    print(f"  Шаблон 5: {len(template5_missing)} файлов")
    print(f"  ВСЕГО: {len(all_missing)} файлов")
    
    # Создаем директорию если нет
    storage_dir = Path('storage/excel_files')
    storage_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🚀 Начинаю скачивание...")
    
    downloaded = 0
    skipped = 0
    errors = 0
    
    for idx, (proj_id, table_id) in enumerate(all_missing, 1):
        output_path = storage_dir / f"{table_id}.xlsx"
        
        # Проверяем существование
        if output_path.exists():
            print(f"  [{idx}/{len(all_missing)}] ⏩ Проект {proj_id}: уже есть")
            skipped += 1
            continue
        
        print(f"  [{idx}/{len(all_missing)}] 📥 Проект {proj_id}...", end='')
        
        if download_excel(table_id, output_path):
            size_kb = output_path.stat().st_size / 1024
            print(f" ✅ {size_kb:.1f} KB")
            downloaded += 1
        else:
            errors += 1
            print()
        
        # Задержка между запросами
        if idx % 10 == 0:
            time.sleep(1)
    
    print("\n" + "=" * 80)
    print("✅ СКАЧИВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    print(f"\n📊 Статистика:")
    print(f"  • Скачано:   {downloaded}")
    print(f"  • Пропущено: {skipped}")
    print(f"  • Ошибок:    {errors}")
    print(f"  • Всего:     {len(all_missing)}")
    print("=" * 80)

if __name__ == '__main__':
    main()












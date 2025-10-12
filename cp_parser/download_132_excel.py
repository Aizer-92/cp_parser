#!/usr/bin/env python3
"""
Скрипт для скачивания 132 Excel файлов проектов с изображениями но без спарсенных изображений
"""

import sys
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import requests
import time

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def download_excel_files():
    """Скачивает Excel файлы для 132 проектов"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("📥 СКАЧИВАНИЕ EXCEL ФАЙЛОВ")
    print("=" * 80)
    print(f"\n📊 Проектов к скачиванию: {len(project_ids)}")
    
    db = PostgreSQLManager()
    
    # Подключаемся к Google Sheets
    print("\n🔐 Подключение к Google Sheets API...")
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    
    success = 0
    errors = 0
    already_exist = 0
    
    excel_dir = Path('excel_files')
    excel_dir.mkdir(exist_ok=True)
    
    for i, proj_id in enumerate(project_ids, 1):
        print(f"\n[{i}/{len(project_ids)}] Проект {proj_id}...", end=' ')
        
        try:
            # Получаем table_id из БД
            with db.get_session() as session:
                table_id = session.execute(text("""
                    SELECT table_id FROM projects WHERE id = :id
                """), {'id': proj_id}).scalar()
                
                if not table_id:
                    print(f"❌ Нет table_id в БД")
                    errors += 1
                    continue
            
            # Проверяем есть ли уже файл
            excel_path = excel_dir / f'project_{proj_id}_{table_id}.xlsx'
            
            if excel_path.exists() and excel_path.stat().st_size > 0:
                print(f"✓ Уже скачан ({excel_path.stat().st_size:,} байт)")
                already_exist += 1
                continue
            
            # Удаляем пустой файл если есть
            if excel_path.exists():
                excel_path.unlink()
            
            # Скачиваем через прямой URL
            url = f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=xlsx"
            response = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'})
            
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                errors += 1
                continue
            
            # Сохраняем файл
            with open(excel_path, 'wb') as f:
                f.write(response.content)
            
            file_size = excel_path.stat().st_size
            if file_size == 0:
                print(f"❌ Пустой файл")
                excel_path.unlink()
                errors += 1
                continue
            
            print(f"✓ {file_size:,} байт")
            success += 1
            
            # Небольшая пауза между запросами
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ {str(e)}")
            errors += 1
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ СКАЧИВАНИЯ:")
    print("=" * 80)
    print(f"✅ Скачано:        {success}")
    print(f"✓  Уже были:       {already_exist}")
    print(f"❌ Ошибок:         {errors}")
    print(f"📁 Всего файлов:   {success + already_exist}")
    print("=" * 80)
    
    if success > 0 or already_exist > 0:
        print("\n✅ Файлы готовы к парсингу!")
        print("Следующий шаг: python3 reparse_images_from_excel.py")

if __name__ == '__main__':
    download_excel_files()



"""
Скрипт для скачивания 132 Excel файлов проектов с изображениями но без спарсенных изображений
"""

import sys
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import requests
import time

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def download_excel_files():
    """Скачивает Excel файлы для 132 проектов"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("📥 СКАЧИВАНИЕ EXCEL ФАЙЛОВ")
    print("=" * 80)
    print(f"\n📊 Проектов к скачиванию: {len(project_ids)}")
    
    db = PostgreSQLManager()
    
    # Подключаемся к Google Sheets
    print("\n🔐 Подключение к Google Sheets API...")
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    
    success = 0
    errors = 0
    already_exist = 0
    
    excel_dir = Path('excel_files')
    excel_dir.mkdir(exist_ok=True)
    
    for i, proj_id in enumerate(project_ids, 1):
        print(f"\n[{i}/{len(project_ids)}] Проект {proj_id}...", end=' ')
        
        try:
            # Получаем table_id из БД
            with db.get_session() as session:
                table_id = session.execute(text("""
                    SELECT table_id FROM projects WHERE id = :id
                """), {'id': proj_id}).scalar()
                
                if not table_id:
                    print(f"❌ Нет table_id в БД")
                    errors += 1
                    continue
            
            # Проверяем есть ли уже файл
            excel_path = excel_dir / f'project_{proj_id}_{table_id}.xlsx'
            
            if excel_path.exists() and excel_path.stat().st_size > 0:
                print(f"✓ Уже скачан ({excel_path.stat().st_size:,} байт)")
                already_exist += 1
                continue
            
            # Удаляем пустой файл если есть
            if excel_path.exists():
                excel_path.unlink()
            
            # Скачиваем через прямой URL
            url = f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=xlsx"
            response = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'})
            
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                errors += 1
                continue
            
            # Сохраняем файл
            with open(excel_path, 'wb') as f:
                f.write(response.content)
            
            file_size = excel_path.stat().st_size
            if file_size == 0:
                print(f"❌ Пустой файл")
                excel_path.unlink()
                errors += 1
                continue
            
            print(f"✓ {file_size:,} байт")
            success += 1
            
            # Небольшая пауза между запросами
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ {str(e)}")
            errors += 1
    
    # Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ СКАЧИВАНИЯ:")
    print("=" * 80)
    print(f"✅ Скачано:        {success}")
    print(f"✓  Уже были:       {already_exist}")
    print(f"❌ Ошибок:         {errors}")
    print(f"📁 Всего файлов:   {success + already_exist}")
    print("=" * 80)
    
    if success > 0 or already_exist > 0:
        print("\n✅ Файлы готовы к парсингу!")
        print("Следующий шаг: python3 reparse_images_from_excel.py")

if __name__ == '__main__':
    download_excel_files()











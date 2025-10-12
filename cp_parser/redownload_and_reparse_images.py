#!/usr/bin/env python3
"""
Перескачивание Excel файлов и допарсинг изображений
Для проектов с офферами но без изображений
"""

import sys
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import requests
import time

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def redownload_and_reparse():
    """Перескачивает файлы и допарсивает изображения"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("🔄 ПЕРЕСКАЧИВАНИЕ И ДОПАРСИНГ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print(f"\n📊 Проектов к обработке: {len(project_ids)}")
    
    parser = Template6Parser()
    db = PostgreSQLManager()
    
    # Подключаемся к Google Sheets
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    success = 0
    errors = 0
    no_images = 0
    
    for i, proj_id in enumerate(project_ids, 1):
        print(f"\n[{i}/{len(project_ids)}] Проект {proj_id}...")
        
        try:
            # Получаем table_id из БД
            with db.get_session() as session:
                table_id = session.execute(text("""
                    SELECT table_id FROM projects WHERE id = :id
                """), {'id': proj_id}).scalar()
                
                if not table_id:
                    print(f"  ❌ Нет table_id в БД")
                    errors += 1
                    continue
            
            # Скачиваем Excel через прямой URL
            print(f"  📥 Скачивание...")
            excel_path = Path(f'excel_files/project_{proj_id}_{table_id}.xlsx')
            excel_path.parent.mkdir(exist_ok=True)
            
            url = f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=xlsx"
            response = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'})
            
            if response.status_code != 200:
                print(f"  ❌ Ошибка скачивания: HTTP {response.status_code}")
                errors += 1
                continue
            
            with open(excel_path, 'wb') as f:
                f.write(response.content)
            
            if not excel_path or not Path(excel_path).exists():
                print(f"  ❌ Не удалось скачать")
                errors += 1
                continue
            
            # Парсим ТОЛЬКО изображения (не офферы, они уже есть)
            print(f"  🖼️  Парсинг изображений...")
            result = parser.reparse_images_only(proj_id, excel_path)
            
            if result.get('images', 0) > 0:
                print(f"  ✅ Добавлено {result['images']} изображений")
                success += 1
            else:
                print(f"  ⚠️  Изображений не найдено")
                no_images += 1
            
            # Удаляем Excel файл
            Path(excel_path).unlink()
            
            # Пауза чтобы не перегружать API
            if i % 10 == 0:
                print(f"\n⏸️  Пауза 5 сек...")
                time.sleep(5)
        
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            errors += 1
    
    print("\n" + "=" * 80)
    print("✅ ОБРАБОТКА ЗАВЕРШЕНА")
    print("=" * 80)
    print(f"\n📊 Результаты:")
    print(f"  ✅ Успешно: {success}")
    print(f"  ⚠️  Без изображений: {no_images}")
    print(f"  ❌ Ошибок: {errors}")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    redownload_and_reparse()


Перескачивание Excel файлов и допарсинг изображений
Для проектов с офферами но без изображений
"""

import sys
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
import requests
import time

sys.path.insert(0, str(Path(__file__).parent))
from parse_template_6 import Template6Parser
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# Google Sheets credentials
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 
          'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'service_account.json'

def redownload_and_reparse():
    """Перескачивает файлы и допарсивает изображения"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print("=" * 80)
    print("🔄 ПЕРЕСКАЧИВАНИЕ И ДОПАРСИНГ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print(f"\n📊 Проектов к обработке: {len(project_ids)}")
    
    parser = Template6Parser()
    db = PostgreSQLManager()
    
    # Подключаемся к Google Sheets
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    success = 0
    errors = 0
    no_images = 0
    
    for i, proj_id in enumerate(project_ids, 1):
        print(f"\n[{i}/{len(project_ids)}] Проект {proj_id}...")
        
        try:
            # Получаем table_id из БД
            with db.get_session() as session:
                table_id = session.execute(text("""
                    SELECT table_id FROM projects WHERE id = :id
                """), {'id': proj_id}).scalar()
                
                if not table_id:
                    print(f"  ❌ Нет table_id в БД")
                    errors += 1
                    continue
            
            # Скачиваем Excel через прямой URL
            print(f"  📥 Скачивание...")
            excel_path = Path(f'excel_files/project_{proj_id}_{table_id}.xlsx')
            excel_path.parent.mkdir(exist_ok=True)
            
            url = f"https://docs.google.com/spreadsheets/d/{table_id}/export?format=xlsx"
            response = requests.get(url, headers={'Authorization': f'Bearer {creds.token}'})
            
            if response.status_code != 200:
                print(f"  ❌ Ошибка скачивания: HTTP {response.status_code}")
                errors += 1
                continue
            
            with open(excel_path, 'wb') as f:
                f.write(response.content)
            
            if not excel_path or not Path(excel_path).exists():
                print(f"  ❌ Не удалось скачать")
                errors += 1
                continue
            
            # Парсим ТОЛЬКО изображения (не офферы, они уже есть)
            print(f"  🖼️  Парсинг изображений...")
            result = parser.reparse_images_only(proj_id, excel_path)
            
            if result.get('images', 0) > 0:
                print(f"  ✅ Добавлено {result['images']} изображений")
                success += 1
            else:
                print(f"  ⚠️  Изображений не найдено")
                no_images += 1
            
            # Удаляем Excel файл
            Path(excel_path).unlink()
            
            # Пауза чтобы не перегружать API
            if i % 10 == 0:
                print(f"\n⏸️  Пауза 5 сек...")
                time.sleep(5)
        
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            errors += 1
    
    print("\n" + "=" * 80)
    print("✅ ОБРАБОТКА ЗАВЕРШЕНА")
    print("=" * 80)
    print(f"\n📊 Результаты:")
    print(f"  ✅ Успешно: {success}")
    print(f"  ⚠️  Без изображений: {no_images}")
    print(f"  ❌ Ошибок: {errors}")
    print("\n" + "=" * 80)

if __name__ == '__main__':
    redownload_and_reparse()


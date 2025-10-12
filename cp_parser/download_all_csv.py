#!/usr/bin/env python3
"""
Простое скачивание CSV для всех Template 4 проектов
Без проверки БД - только скачивание
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv as csv_lib
from datetime import datetime
import time
import gspread
from google.oauth2.service_account import Credentials

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

# Глобальный клиент
GSPREAD_CLIENT = None

def get_gspread_client():
    """Создает gspread клиента один раз"""
    global GSPREAD_CLIENT
    if GSPREAD_CLIENT is None:
        print("🔐 Авторизуюсь в Google API...", flush=True)
        scope = ['https://www.googleapis.com/auth/spreadsheets.readonly',
                 'https://www.googleapis.com/auth/drive.readonly']
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        GSPREAD_CLIENT = gspread.authorize(creds)
        print("✅ Авторизация успешна!\n", flush=True)
    return GSPREAD_CLIENT

def download_csv(sheet_id, output_path):
    """Скачивает CSV"""
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)
        values = worksheet.get_all_values()
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerows(values)
        
        return True
    except Exception as e:
        print(f"  ❌ Ошибка: {e}", flush=True)
        return False

def main():
    print("="*80, flush=True)
    print("📥 СКАЧИВАНИЕ CSV ДЛЯ ВСЕХ TEMPLATE 4 ПРОЕКТОВ", flush=True)
    print("="*80, flush=True)
    
    print("\n📊 Подключаюсь к БД...", flush=True)
    db = PostgreSQLManager()
    
    print("📊 Получаю список проектов...", flush=True)
    
    with db.get_session() as session:
        projects_data = session.execute(text("""
            SELECT DISTINCT
                pr.id,
                pr.project_name,
                pr.google_sheets_url
            FROM projects pr
            INNER JOIN products p ON pr.id = p.project_id
            WHERE p.sample_price IS NOT NULL
            AND pr.google_sheets_url IS NOT NULL
            ORDER BY pr.id
        """)).fetchall()
    
    print(f"✅ Найдено: {len(projects_data)} проектов Template 4", flush=True)
    
    # Преобразуем
    projects = []
    for proj in projects_data:
        if '/d/' in proj.google_sheets_url:
            sheet_id = proj.google_sheets_url.split('/d/')[1].split('/')[0]
            projects.append({
                'id': proj.id,
                'name': proj.project_name,
                'sheet_id': sheet_id,
                'url': proj.google_sheets_url
            })
    
    total_projects = len(projects)
    print(f"📋 С валидными URL: {total_projects}", flush=True)
    
    csv_dir = Path('verification_csv_all')
    csv_dir.mkdir(exist_ok=True)
    
    # Проверяем сколько CSV уже есть
    existing_csvs = len(list(csv_dir.glob('*.csv')))
    print(f"📁 CSV уже скачано: {existing_csvs}", flush=True)
    print(f"📥 Нужно докачать: {total_projects - existing_csvs}", flush=True)
    print(f"📁 Папка: {csv_dir.absolute()}\n", flush=True)
    
    start_time = time.time()
    downloaded = 0
    skipped = 0
    failed = 0
    
    print("🚀 НАЧИНАЮ СКАЧИВАНИЕ...\n", flush=True)
    
    for i, project in enumerate(projects, 1):
        csv_path = csv_dir / f"proj_{project['id']}.csv"
        
        # Пропускаем если уже есть
        if csv_path.exists():
            skipped += 1
            continue
        
        # Скачиваем
        print(f"📥 [{i}/{total_projects}] Проект {project['id']}: {project['name'][:60]}...", flush=True)
        
        if download_csv(project['sheet_id'], csv_path):
            downloaded += 1
            print(f"  ✅ Скачано", flush=True)
        else:
            failed += 1
            print(f"  ❌ Не удалось", flush=True)
        
        # Прогресс каждые 50 проектов
        if i % 50 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (total_projects - i) * avg_time / 60
            
            print(f"\n⏱️  ПРОГРЕСС: {i}/{total_projects} ({i*100//total_projects}%)", flush=True)
            print(f"  ✅ Скачано: {downloaded}", flush=True)
            print(f"  ⏭️  Пропущено: {skipped}", flush=True)
            print(f"  ❌ Ошибок: {failed}", flush=True)
            print(f"  ⏱️  Осталось: ~{int(remaining)} мин\n", flush=True)
        
        # Пауза для API (избегаем 429 ошибки)
        time.sleep(1.2)
    
    # ИТОГОВЫЙ ОТЧЕТ
    print("\n" + "="*80, flush=True)
    print("📊 ИТОГОВЫЙ ОТЧЕТ", flush=True)
    print("="*80, flush=True)
    print(f"✅ Скачано новых: {downloaded:,}", flush=True)
    print(f"⏭️  Пропущено (уже были): {skipped:,}", flush=True)
    print(f"❌ Ошибок: {failed:,}", flush=True)
    print(f"📁 Всего CSV файлов: {len(list(csv_dir.glob('*.csv'))):,}", flush=True)
    
    elapsed_total = time.time() - start_time
    print(f"\n⏱️  Время выполнения: {int(elapsed_total/60)} мин {int(elapsed_total%60)} сек", flush=True)
    print("="*80, flush=True)
    
    if failed > 0:
        print(f"\n⚠️  Есть {failed} проектов с ошибками скачивания", flush=True)
        print("💡 Можно перезапустить скрипт - он пропустит уже скачанные файлы", flush=True)

if __name__ == '__main__':
    main()


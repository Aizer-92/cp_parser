#!/usr/bin/env python3
"""
ПОЛНАЯ проверка ВСЕХ тиражей Template 4 через CSV
Проверяет все тиражи без фильтров, чтобы выловить ВСЕ ошибки x10
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

import json
from google.oauth2.service_account import Credentials
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv as csv_lib
from datetime import datetime
import time
import requests

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def download_csv(sheet_id, output_path):
    """Скачивает как CSV через gspread"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        
        scope = ['https://www.googleapis.com/auth/spreadsheets.readonly',
                 'https://www.googleapis.com/auth/drive.readonly']
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Открываем таблицу
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.get_worksheet(0)
        
        # Получаем все значения
        values = worksheet.get_all_values()
        
        # Записываем в CSV
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerows(values)
        
        return True
    except Exception as e:
        return False

def extract_quantity_from_csv(csv_path, row_number):
    """Извлекает тираж из колонки E (индекс 4)"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.reader(f)
            rows = list(reader)
            
            if row_number <= len(rows):
                target_row = rows[row_number - 1]
                
                if len(target_row) > 4:
                    qty_str = target_row[4].strip()
                    
                    qty_str = qty_str.replace(' ', '').replace(',', '')
                    
                    if qty_str.isdigit():
                        return int(qty_str)
        return None
    except:
        return None

def verify_project(db, project_data, csv_dir):
    """Проверяет ВСЕ тиражи проекта (без фильтров)"""
    project_id = project_data['id']
    sheet_id = project_data['sheet_id']
    
    csv_path = csv_dir / f"proj_{project_id}.csv"
    
    # Скачиваем только если нет
    if not csv_path.exists():
        if not download_csv(sheet_id, csv_path):
            return None
    
    with db.get_session() as session:
        # ВАЖНО: Берем ВСЕ price_offers без фильтров!
        products = session.execute(text("""
            SELECT 
                p.id, p.name, p.row_number,
                po.id as offer_id, po.quantity, po.route
            FROM products p
            INNER JOIN price_offers po ON p.id = po.product_id
            WHERE p.project_id = :pid
            ORDER BY p.row_number, po.route
        """), {'pid': project_id}).fetchall()
        
        if not products:
            return None
        
        results = []
        checked_rows = {}
        
        for prod in products:
            row_num = prod.row_number
            
            # Кешируем тираж из CSV по строке
            if row_num not in checked_rows:
                checked_rows[row_num] = extract_quantity_from_csv(csv_path, row_num)
            
            excel_qty = checked_rows[row_num]
            db_qty = int(prod.quantity)
            
            # Проверяем ошибку x10
            is_x10 = False
            if excel_qty and isinstance(excel_qty, int) and excel_qty * 10 == db_qty:
                is_x10 = True
            
            results.append({
                'offer_id': prod.offer_id,
                'product_id': prod.id,
                'product_name': prod.name,
                'row': row_num,
                'csv_qty': excel_qty,
                'db_qty': db_qty,
                'route': prod.route,
                'is_x10': is_x10
            })
        
        x10_count = sum(1 for r in results if r['is_x10'])
        
        return {
            'id': project_id,
            'name': project_data['name'],
            'url': project_data['url'],
            'total': len(results),
            'x10': x10_count,
            'results': results
        }

def main():
    print("="*80)
    print("🚀 ПОЛНАЯ ПРОВЕРКА ВСЕХ ТИРАЖЕЙ - ВСЕ TEMPLATE 4 (БЕЗ ФИЛЬТРОВ)")
    print("="*80)
    
    db = PostgreSQLManager()
    
    print("\n📊 Получаю список Template 4...")
    
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
    
    print(f"✅ Найдено: {len(projects_data)} проектов Template 4")
    
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
    print(f"📋 С валидными URL: {total_projects}")
    print(f"📁 CSV в: verification_full_csv/\n")
    
    csv_dir = Path('verification_full_csv')
    csv_dir.mkdir(exist_ok=True)
    
    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    
    start_time = time.time()
    processed = 0
    failed = 0
    total_x10_errors = 0
    
    for i, project in enumerate(projects, 1):
        try:
            result = verify_project(db, project, csv_dir)
            
            if result:
                processed += 1
                total_x10_errors += result['x10']
                all_results.append(result)
            else:
                failed += 1
            
            # Прогресс каждые 100 проектов
            if i % 100 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (total_projects - i) * avg_time / 60
                
                print(f"⏱️  {i}/{total_projects} ({i*100//total_projects}%) | "
                      f"Ошибок x10: {total_x10_errors} | "
                      f"Осталось: ~{int(remaining)} мин")
        
        except Exception as e:
            failed += 1
            continue
    
    # ИТОГОВЫЙ ОТЧЕТ
    print("\n" + "="*80)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*80)
    print(f"✅ Проверено: {processed:,} проектов")
    print(f"❌ Не удалось: {failed:,} проектов")
    
    if processed > 0:
        total_offers = sum(r['total'] for r in all_results)
        total_x10 = sum(r['x10'] for r in all_results)
        percent = (total_x10 / total_offers * 100) if total_offers > 0 else 0
        
        print(f"❌ Ошибок x10: {total_x10:,} из {total_offers:,} ({percent:.1f}%)")
        
        # Сохраняем ПОЛНЫЙ отчет
        full_report = f"ПОЛНАЯ_ПРОВЕРКА_ВСЕХ_ТИРАЖЕЙ_{timestamp}.csv"
        with open(full_report, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID_Проекта', 'Название', 'ID_Товара', 'ID_Оффера', 
                           'Товар', 'Строка', 'Тираж_Google', 'Тираж_БД', 
                           'Маршрут', 'Ошибка_x10', 'URL'])
            
            for proj in all_results:
                for res in proj['results']:
                    writer.writerow([
                        proj['id'],
                        proj['name'],
                        res['product_id'],
                        res['offer_id'],
                        res['product_name'],
                        res['row'],
                        res['csv_qty'],
                        res['db_qty'],
                        res['route'],
                        'ДА' if res['is_x10'] else 'НЕТ',
                        proj['url']
                    ])
        
        print(f"✅ Полный отчет: {full_report}")
        
        # Сохраняем только ошибки для исправления
        errors_report = f"ИСПРАВИТЬ_ОФФЕРЫ_{timestamp}.csv"
        with open(errors_report, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID_Оффера', 'ID_Проекта', 'Название_Проекта', 
                           'ID_Товара', 'Товар', 'Строка', 'Тираж_Google', 
                           'Тираж_БД', 'Маршрут', 'URL'])
            
            for proj in all_results:
                for res in proj['results']:
                    if res['is_x10']:
                        writer.writerow([
                            res['offer_id'],
                            proj['id'],
                            proj['name'],
                            res['product_id'],
                            res['product_name'],
                            res['row'],
                            res['csv_qty'],
                            res['db_qty'],
                            res['route'],
                            proj['url']
                        ])
        
        print(f"✅ Для исправления: {errors_report}")
        
        # Проекты с ошибками
        projects_with_errors = [p for p in all_results if p['x10'] > 0]
        if projects_with_errors:
            projects_report = f"ПРОЕКТЫ_С_ОШИБКАМИ_{timestamp}.csv"
            with open(projects_report, 'w', encoding='utf-8', newline='') as f:
                writer = csv_lib.writer(f)
                writer.writerow(['ID', 'Название', 'Ошибок', 'Всего', '%', 'URL'])
                
                for proj in sorted(projects_with_errors, key=lambda x: x['x10'], reverse=True):
                    percent = (proj['x10'] / proj['total'] * 100) if proj['total'] > 0 else 0
                    writer.writerow([
                        proj['id'],
                        proj['name'],
                        proj['x10'],
                        proj['total'],
                        f"{percent:.1f}%",
                        proj['url']
                    ])
            
            print(f"✅ Проекты с ошибками: {projects_report}")
    
    elapsed_total = time.time() - start_time
    print(f"\n⏱️  Время выполнения: {int(elapsed_total/60)} мин {int(elapsed_total%60)} сек")
    print("="*80)

if __name__ == '__main__':
    main()


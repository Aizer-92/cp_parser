#!/usr/bin/env python3
"""
БЫСТРАЯ проверка тиражей через CSV для всех Template 4
CSV скачивается в 10-20 раз быстрее чем Excel
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
    """Скачивает как CSV (очень быстро)"""
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets.readonly',
                 'https://www.googleapis.com/auth/drive.readonly']
        creds = Credentials.from_service_account_file('service_account.json', scopes=scope)
        
        export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
        
        response = requests.get(export_url, headers={'Authorization': f'Bearer {creds.token}'}, timeout=10)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except:
        return False

def extract_quantity_from_csv(csv_path, row_number):
    """Извлекает тираж из колонки E (индекс 4)"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.reader(f)
            rows = list(reader)
            
            if row_number <= len(rows):
                row_data = rows[row_number - 1]
                
                if len(row_data) > 4:
                    cell_value = row_data[4]
                    
                    if not cell_value:
                        return None
                    
                    try:
                        return int(float(str(cell_value).replace(',', '').replace(' ', '')))
                    except:
                        return str(cell_value)
        return None
    except:
        return None

def verify_project(project_data, db, csv_dir):
    """Проверяет проект через CSV"""
    project_id = project_data['id']
    sheet_id = project_data['sheet_id']
    
    csv_path = csv_dir / f"proj_{project_id}.csv"
    
    # Скачиваем только если нет
    if not csv_path.exists():
        if not download_csv(sheet_id, csv_path):
            return None
    
    with db.get_session() as session:
        products = session.execute(text("""
            SELECT 
                p.id, p.name, p.row_number,
                po.quantity, po.route
            FROM products p
            INNER JOIN price_offers po ON p.id = po.product_id
            WHERE p.project_id = :pid
            AND po.quantity >= 300
            AND po.quantity % 10 = 0
            ORDER BY p.row_number
        """), {'pid': project_id}).fetchall()
        
        if not products:
            return None
        
        results = []
        checked_rows = {}
        
        for prod in products:
            row_num = prod.row_number
            
            if row_num not in checked_rows:
                checked_rows[row_num] = extract_quantity_from_csv(csv_path, row_num)
            
            excel_qty = checked_rows[row_num]
            db_qty = int(prod.quantity)
            
            is_x10 = False
            if excel_qty and isinstance(excel_qty, int) and excel_qty * 10 == db_qty:
                is_x10 = True
            
            results.append({
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
    print("="*70)
    print("🚀 БЫСТРАЯ ПРОВЕРКА ЧЕРЕЗ CSV - ВСЕ TEMPLATE 4")
    print("="*70)
    
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
    
    print(f"✅ Найдено: {len(projects_data)} проектов")
    
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
    
    print(f"📋 С валидными URL: {len(projects)}")
    print(f"📁 CSV в: verification_csv_all/\n")
    
    csv_dir = Path('verification_csv_all')
    csv_dir.mkdir(exist_ok=True)
    
    all_results = []
    failed = 0
    
    start_time = time.time()
    
    for i, proj in enumerate(projects, 1):
        # Компактный вывод
        if i == 1 or i % 50 == 0 or i == len(projects):
            print(f"\r🔍 {i}/{len(projects)} ({i/len(projects)*100:.1f}%)", end='', flush=True)
        
        result = verify_project(proj, db, csv_dir)
        if result:
            all_results.append(result)
        else:
            failed += 1
        
        # Прогресс каждые 200
        if i % 200 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(projects) - i) * avg_time
            errors_count = len([r for r in all_results if r['x10'] > 0])
            print(f"\n⏱️  {i}/{len(projects)} ({i/len(projects)*100:.0f}%) | "
                  f"Ошибки: {errors_count} проектов | "
                  f"Осталось: ~{remaining/60:.0f} мин")
        
        time.sleep(0.05)  # Минимальная пауза
    
    # Итог
    print("\n\n" + "="*70)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*70)
    
    if not all_results:
        print("\n⚠️  Не удалось проверить")
        return
    
    total_x10 = sum(r['x10'] for r in all_results)
    total_rec = sum(r['total'] for r in all_results)
    projects_errors = len([r for r in all_results if r['x10'] > 0])
    
    print(f"\n✅ Проверено: {len(all_results):,} проектов")
    print(f"❌ Не удалось: {failed:,} проектов")
    print(f"📊 Записей: {total_rec:,}")
    print(f"❌ Ошибок x10: {total_x10:,} ({total_x10/total_rec*100:.1f}%)")
    print(f"⚠️  Проектов с ошибками: {projects_errors:,} ({projects_errors/len(all_results)*100:.1f}%)")
    
    # Топ ошибок
    error_projects = sorted([r for r in all_results if r['x10'] > 0], 
                          key=lambda x: x['x10'], reverse=True)
    
    if error_projects:
        print(f"\n📋 ТОП-20 С НАИБОЛЬШИМ КОЛ-ВОМ ОШИБОК:")
        for r in error_projects[:20]:
            pct = r['x10']/r['total']*100
            print(f"  ❌ ID {r['id']}: {r['x10']}/{r['total']} ({pct:.0f}%) - {r['name'][:40]}")
    
    # Сохраняем CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    csv_report = Path(f"ПОЛНАЯ_ПРОВЕРКА_CSV_{timestamp}.csv")
    
    print(f"\n💾 Сохраняю отчет...")
    
    with open(csv_report, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv_lib.writer(f)
        writer.writerow([
            'ID_Проекта', 'Название', 'ID_Товара', 'Товар',
            'Строка', 'Тираж_Google', 'Тираж_БД', 'Маршрут', 'Ошибка_x10', 'URL'
        ])
        
        for proj in all_results:
            for r in proj['results']:
                writer.writerow([
                    proj['id'], proj['name'],
                    r['product_id'], r['product_name'],
                    r['row'], r['csv_qty'], r['db_qty'],
                    r['route'], 'ДА' if r['is_x10'] else 'НЕТ',
                    proj['url']
                ])
    
    print(f"✅ Отчет: {csv_report}")
    
    # Список для исправления
    if error_projects:
        fix_list = Path(f"ИСПРАВИТЬ_ПРОЕКТЫ_{timestamp}.csv")
        
        with open(fix_list, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID', 'Название', 'Ошибок', 'Всего', '%', 'URL'])
            
            for r in error_projects:
                pct = r['x10']/r['total']*100
                writer.writerow([r['id'], r['name'], r['x10'], r['total'], f"{pct:.1f}%", r['url']])
        
        print(f"✅ Для исправления: {fix_list}")
    
    # Рекомендация
    if total_x10 > 0:
        error_pct = total_x10 / total_rec * 100
        print(f"\n💡 РЕКОМЕНДАЦИЯ:")
        if error_pct > 10:
            print(f"   🚨 {error_pct:.1f}% ошибок! Массовое исправление")
        elif error_pct > 5:
            print(f"   ⚠️  {error_pct:.1f}% ошибок. Исправить >10%")
        else:
            print(f"   ✅ {error_pct:.1f}% ошибок. Выборочно")
    
    elapsed = time.time() - start_time
    print(f"\n⏱️  Время: {elapsed/60:.1f} минут ({elapsed/len(projects):.2f} сек/проект)")
    print("="*70)

if __name__ == '__main__':
    main()





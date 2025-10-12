#!/usr/bin/env python3
"""
Проверка ВСЕХ тиражей Template 4 из уже скачанных CSV
Использует готовые CSV файлы - быстрая проверка
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

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def extract_quantity_from_csv(csv_path, row_number):
    """Извлекает тираж из колонки E"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.reader(f)
            rows = list(reader)
            
            if row_number <= len(rows):
                target_row = rows[row_number - 1]
                
                if len(target_row) > 4:
                    qty_str = target_row[4].strip().replace(' ', '').replace(',', '')
                    
                    if qty_str.isdigit():
                        return int(qty_str)
        return None
    except:
        return None

def verify_project(db, project_id, csv_path):
    """Проверяет все тиражи проекта из CSV"""
    with db.get_session() as session:
        # Берем ВСЕ price_offers
        products = session.execute(text("""
            SELECT 
                pr.project_name,
                pr.google_sheets_url,
                p.id, p.name, p.row_number,
                po.id as offer_id, po.quantity, po.route
            FROM products p
            INNER JOIN price_offers po ON p.id = po.product_id
            INNER JOIN projects pr ON p.project_id = pr.id
            WHERE p.project_id = :pid
            ORDER BY p.row_number, po.route
        """), {'pid': project_id}).fetchall()
        
        if not products:
            return None
        
        results = []
        checked_rows = {}
        project_name = products[0].project_name
        project_url = products[0].google_sheets_url
        
        for prod in products:
            row_num = prod.row_number
            
            if row_num not in checked_rows:
                checked_rows[row_num] = extract_quantity_from_csv(csv_path, row_num)
            
            csv_qty = checked_rows[row_num]
            db_qty = int(prod.quantity)
            
            is_x10 = False
            if csv_qty and isinstance(csv_qty, int) and csv_qty * 10 == db_qty:
                is_x10 = True
            
            results.append({
                'offer_id': prod.offer_id,
                'product_id': prod.id,
                'product_name': prod.name,
                'row': row_num,
                'csv_qty': csv_qty,
                'db_qty': db_qty,
                'route': prod.route,
                'is_x10': is_x10
            })
        
        x10_count = sum(1 for r in results if r['is_x10'])
        
        return {
            'id': project_id,
            'name': project_name,
            'url': project_url,
            'total': len(results),
            'x10': x10_count,
            'results': results
        }

def main():
    print("="*80, flush=True)
    print("🔍 ПРОВЕРКА ВСЕХ ТИРАЖЕЙ ИЗ СКАЧАННЫХ CSV", flush=True)
    print("="*80, flush=True)
    
    csv_dir = Path('verification_csv_all')
    csv_files = list(csv_dir.glob('proj_*.csv'))
    
    if not csv_files:
        print("❌ Нет CSV файлов в verification_csv_all/", flush=True)
        print("💡 Сначала запустите: python3 download_all_csv.py", flush=True)
        return
    
    print(f"\n✅ Найдено CSV файлов: {len(csv_files)}", flush=True)
    print(f"📁 Папка: {csv_dir.absolute()}\n", flush=True)
    
    print("📊 Подключаюсь к БД...", flush=True)
    db = PostgreSQLManager()
    
    print("🚀 НАЧИНАЮ ПРОВЕРКУ...\n", flush=True)
    
    all_results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    start_time = time.time()
    processed = 0
    failed = 0
    total_x10_errors = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        # Извлекаем project_id из имени файла
        project_id = int(csv_file.stem.replace('proj_', ''))
        
        try:
            result = verify_project(db, project_id, csv_file)
            
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
                remaining = (len(csv_files) - i) * avg_time / 60
                
                print(f"⏱️  {i}/{len(csv_files)} ({i*100//len(csv_files)}%) | "
                      f"✅ Проверено: {processed} | "
                      f"❌ Ошибок x10: {total_x10_errors} | "
                      f"Осталось: ~{int(remaining)} мин", flush=True)
        
        except Exception as e:
            failed += 1
            continue
    
    # ИТОГОВЫЙ ОТЧЕТ
    print("\n" + "="*80, flush=True)
    print("📊 ИТОГОВЫЙ ОТЧЕТ", flush=True)
    print("="*80, flush=True)
    print(f"✅ Проверено проектов: {processed:,}", flush=True)
    print(f"❌ Не удалось: {failed:,}", flush=True)
    
    if processed > 0:
        total_offers = sum(r['total'] for r in all_results)
        total_x10 = sum(r['x10'] for r in all_results)
        percent = (total_x10 / total_offers * 100) if total_offers > 0 else 0
        
        print(f"\n❌ НАЙДЕНО ОШИБОК x10: {total_x10:,} из {total_offers:,} офферов ({percent:.1f}%)", flush=True)
        
        # Сохраняем ПОЛНЫЙ отчет
        full_report = f"ПОЛНАЯ_ПРОВЕРКА_{timestamp}.csv"
        with open(full_report, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID_Проекта', 'Название', 'ID_Товара', 'ID_Оффера', 
                           'Товар', 'Строка', 'Тираж_CSV', 'Тираж_БД', 
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
        
        print(f"\n✅ Полный отчет: {full_report}", flush=True)
        
        # Сохраняем ТОЛЬКО ОШИБКИ для исправления
        if total_x10 > 0:
            errors_report = f"ИСПРАВИТЬ_ОФФЕРЫ_{timestamp}.csv"
            with open(errors_report, 'w', encoding='utf-8', newline='') as f:
                writer = csv_lib.writer(f)
                writer.writerow(['ID_Оффера', 'ID_Проекта', 'Название_Проекта', 
                               'ID_Товара', 'Товар', 'Строка', 'Тираж_CSV', 
                               'Тираж_БД', 'Новый_Тираж', 'Маршрут', 'URL'])
                
                for proj in all_results:
                    for res in proj['results']:
                        if res['is_x10']:
                            new_qty = res['db_qty'] // 10
                            writer.writerow([
                                res['offer_id'],
                                proj['id'],
                                proj['name'],
                                res['product_id'],
                                res['product_name'],
                                res['row'],
                                res['csv_qty'],
                                res['db_qty'],
                                new_qty,
                                res['route'],
                                proj['url']
                            ])
            
            print(f"✅ Для исправления: {errors_report} ({total_x10} офферов)", flush=True)
            
            # Проекты с ошибками
            projects_with_errors = [p for p in all_results if p['x10'] > 0]
            projects_report = f"ПРОЕКТЫ_С_ОШИБКАМИ_{timestamp}.csv"
            with open(projects_report, 'w', encoding='utf-8', newline='') as f:
                writer = csv_lib.writer(f)
                writer.writerow(['ID', 'Название', 'Ошибок_x10', 'Всего_Офферов', '%', 'URL'])
                
                for proj in sorted(projects_with_errors, key=lambda x: x['x10'], reverse=True):
                    percent_proj = (proj['x10'] / proj['total'] * 100) if proj['total'] > 0 else 0
                    writer.writerow([
                        proj['id'],
                        proj['name'],
                        proj['x10'],
                        proj['total'],
                        f"{percent_proj:.1f}%",
                        proj['url']
                    ])
            
            print(f"✅ Проекты с ошибками: {projects_report} ({len(projects_with_errors)} проектов)", flush=True)
            
            print(f"\n🎯 ДЛЯ ИСПРАВЛЕНИЯ В БД:", flush=True)
            print(f"  • {total_x10:,} офферов нужно поделить на 10", flush=True)
            print(f"  • {len(projects_with_errors)} проектов затронуто", flush=True)
    
    elapsed_total = time.time() - start_time
    print(f"\n⏱️  Время выполнения: {int(elapsed_total/60)} мин {int(elapsed_total%60)} сек", flush=True)
    print("="*80, flush=True)

if __name__ == '__main__':
    main()




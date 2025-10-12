#!/usr/bin/env python3
"""
УМНАЯ проверка тиражей Template 4
Учитывает что в CSV несколько тиражей идут подряд для одного товара
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
from collections import defaultdict

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def extract_all_quantities_from_product_group(csv_path, start_row):
    """
    Извлекает ВСЕ тиражи из группы строк товара
    (первая строка с названием + следующие пустые строки)
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv_lib.reader(f)
            rows = list(reader)
            
            quantities = []
            current_row = start_row - 1  # 0-based index
            
            # Читаем строки пока не закончатся или не встретим новый товар
            while current_row < len(rows):
                row = rows[current_row]
                
                # Если длина строки < 5, пропускаем
                if len(row) <= 4:
                    break
                
                # Колонка B (index 1) - название товара
                # Колонка E (index 4) - тираж
                product_name = row[1].strip() if len(row) > 1 else ''
                qty_str = row[4].strip().replace(' ', '').replace(',', '') if len(row) > 4 else ''
                
                # Если название есть и это не первая строка - значит начался новый товар
                if current_row > start_row - 1 and product_name:
                    break
                
                # Извлекаем тираж
                if qty_str and qty_str.isdigit():
                    quantities.append(int(qty_str))
                
                current_row += 1
                
                # Если это была первая строка (с названием) - продолжаем
                # Если это уже дополнительная строка и нет тиража - останавливаемся
                if current_row > start_row and not qty_str:
                    break
            
            return quantities
            
    except Exception as e:
        return []

def verify_project(db, project_id, csv_path):
    """Проверяет все тиражи проекта с учетом множественных тиражей"""
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
            ORDER BY p.row_number, po.quantity, po.route
        """), {'pid': project_id}).fetchall()
        
        if not products:
            return None
        
        results = []
        checked_rows = {}  # row_number -> list of quantities
        project_name = products[0].project_name
        project_url = products[0].google_sheets_url
        
        # Группируем офферы по товару (по row_number)
        products_by_row = defaultdict(list)
        for prod in products:
            products_by_row[prod.row_number].append(prod)
        
        # Обрабатываем каждую группу товаров
        for row_num, prods in products_by_row.items():
            # Извлекаем все тиражи из CSV для этой группы
            if row_num not in checked_rows:
                checked_rows[row_num] = extract_all_quantities_from_product_group(csv_path, row_num)
            
            csv_quantities = checked_rows[row_num]
            
            # Получаем уникальные quantity из БД для этого товара
            db_quantities = sorted(set(int(p.quantity) for p in prods))
            
            # Пытаемся сопоставить каждый оффер с CSV тиражом
            for prod in prods:
                db_qty = int(prod.quantity)
                
                # Ищем подходящий CSV тираж
                csv_qty = None
                is_x10 = False
                
                # Пытаемся найти точное совпадение
                if db_qty in csv_quantities:
                    csv_qty = db_qty
                # Проверяем x10 ошибку
                elif db_qty // 10 in csv_quantities and db_qty % 10 == 0:
                    csv_qty = db_qty // 10
                    is_x10 = True
                # Если не нашли - берем ближайший или None
                else:
                    # Ищем среди CSV тиражей умноженных на 10
                    for cq in csv_quantities:
                        if cq * 10 == db_qty:
                            csv_qty = cq
                            is_x10 = True
                            break
                
                results.append({
                    'offer_id': prod.offer_id,
                    'product_id': prod.id,
                    'product_name': prod.name,
                    'row': row_num,
                    'csv_qty': csv_qty,
                    'db_qty': db_qty,
                    'route': prod.route,
                    'is_x10': is_x10,
                    'csv_all_qtys': csv_quantities  # для отладки
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
    print("🔍 УМНАЯ ПРОВЕРКА ТИРАЖЕЙ (учитывает множественные тиражи)", flush=True)
    print("="*80, flush=True)
    
    csv_dir = Path('verification_csv_all')
    csv_files = list(csv_dir.glob('proj_*.csv'))
    
    if not csv_files:
        print("❌ Нет CSV файлов", flush=True)
        return
    
    print(f"\n✅ Найдено CSV: {len(csv_files)}", flush=True)
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
        project_id = int(csv_file.stem.replace('proj_', ''))
        
        try:
            result = verify_project(db, project_id, csv_file)
            
            if result:
                processed += 1
                total_x10_errors += result['x10']
                all_results.append(result)
            else:
                failed += 1
            
            if i % 100 == 0:
                elapsed = time.time() - start_time
                avg_time = elapsed / i
                remaining = (len(csv_files) - i) * avg_time / 60
                
                print(f"⏱️  {i}/{len(csv_files)} ({i*100//len(csv_files)}%) | "
                      f"Ошибок x10: {total_x10_errors} | "
                      f"Осталось: ~{int(remaining)} мин", flush=True)
        
        except Exception as e:
            failed += 1
            if i <= 10:  # Показываем первые ошибки
                print(f"❌ Проект {project_id}: {e}", flush=True)
            continue
    
    # ИТОГОВЫЙ ОТЧЕТ
    print("\n" + "="*80, flush=True)
    print("📊 ИТОГОВЫЙ ОТЧЕТ", flush=True)
    print("="*80, flush=True)
    print(f"✅ Проверено: {processed:,}", flush=True)
    print(f"❌ Не удалось: {failed:,}", flush=True)
    
    if processed > 0:
        total_offers = sum(r['total'] for r in all_results)
        total_x10 = sum(r['x10'] for r in all_results)
        percent = (total_x10 / total_offers * 100) if total_offers > 0 else 0
        
        print(f"\n❌ ОШИБОК x10: {total_x10:,} из {total_offers:,} ({percent:.1f}%)", flush=True)
        
        # Полный отчет
        full_report = f"ПРОВЕРКА_SMART_{timestamp}.csv"
        with open(full_report, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID_Проекта', 'Название', 'ID_Товара', 'ID_Оффера', 
                           'Товар', 'Строка', 'Тираж_CSV', 'Тираж_БД', 
                           'Маршрут', 'Ошибка_x10', 'Все_CSV_Тиражи', 'URL'])
            
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
                        ', '.join(map(str, res['csv_all_qtys'])),
                        proj['url']
                    ])
        
        print(f"✅ Полный отчет: {full_report}", flush=True)
        
        # Только ошибки
        if total_x10 > 0:
            errors_report = f"ИСПРАВИТЬ_SMART_{timestamp}.csv"
            with open(errors_report, 'w', encoding='utf-8', newline='') as f:
                writer = csv_lib.writer(f)
                writer.writerow(['ID_Оффера', 'ID_Проекта', 'Название', 
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
            projects_report = f"ПРОЕКТЫ_SMART_{timestamp}.csv"
            with open(projects_report, 'w', encoding='utf-8', newline='') as f:
                writer = csv_lib.writer(f)
                writer.writerow(['ID', 'Название', 'Ошибок_x10', 'Всего', '%', 'URL'])
                
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
            
            print(f"✅ Проекты: {projects_report} ({len(projects_with_errors)})", flush=True)
    
    elapsed_total = time.time() - start_time
    print(f"\n⏱️  Время: {int(elapsed_total/60)} мин {int(elapsed_total%60)} сек", flush=True)
    print("="*80, flush=True)

if __name__ == '__main__':
    main()


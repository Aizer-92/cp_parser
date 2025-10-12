#!/usr/bin/env python3
"""
Анализ уже скачанных CSV файлов
Проверка тиражей без повторного скачивания
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv
from datetime import datetime

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def extract_quantity_from_csv(csv_path, row_number):
    """Извлекает тираж из колонки E (индекс 4)"""
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
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

def analyze_csv_file(csv_path, db):
    """Анализирует один CSV файл"""
    # Извлекаем project_id из имени файла
    filename = csv_path.name
    if not filename.startswith('proj_') or not filename.endswith('.csv'):
        return None
    
    try:
        project_id = int(filename.replace('proj_', '').replace('.csv', ''))
    except:
        return None
    
    with db.get_session() as session:
        # Получаем товары с подозрительными тиражами
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
        
        # Получаем название проекта
        project_info = session.execute(text("""
            SELECT project_name, google_sheets_url
            FROM projects
            WHERE id = :pid
        """), {'pid': project_id}).fetchone()
        
        if not project_info:
            return None
        
        results = []
        checked_rows = {}
        
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
                'product_id': prod.id,
                'product_name': prod.name,
                'row': row_num,
                'csv_qty': csv_qty,
                'db_qty': db_qty,
                'route': prod.route,
                'is_x10': is_x10
            })
        
        x10_count = sum(1 for r in results if r['is_x10'])
        
        if x10_count == 0:
            return None  # Пропускаем проекты без ошибок
        
        return {
            'id': project_id,
            'name': project_info.project_name,
            'url': project_info.google_sheets_url,
            'total': len(results),
            'x10': x10_count,
            'results': results
        }

def main():
    print("="*70)
    print("🔍 АНАЛИЗ УЖЕ СКАЧАННЫХ CSV")
    print("="*70)
    
    csv_dir = Path('verification_csv_all')
    
    if not csv_dir.exists():
        print("\n❌ Папка verification_csv_all не найдена")
        return
    
    csv_files = list(csv_dir.glob('proj_*.csv'))
    print(f"\n✅ Найдено CSV файлов: {len(csv_files)}")
    
    if not csv_files:
        print("⚠️  Еще нет скачанных файлов")
        return
    
    print(f"📊 Анализирую...\n")
    
    db = PostgreSQLManager()
    
    projects_with_errors = []
    checked = 0
    
    for i, csv_path in enumerate(csv_files, 1):
        if i % 100 == 0:
            print(f"\r🔍 Проверено: {i}/{len(csv_files)}", end='', flush=True)
        
        result = analyze_csv_file(csv_path, db)
        if result:
            projects_with_errors.append(result)
        
        checked += 1
    
    print(f"\n\n{'='*70}")
    print("📊 РЕЗУЛЬТАТЫ")
    print("="*70)
    
    print(f"\n✅ Проверено CSV файлов: {checked:,}")
    print(f"❌ Проектов с ошибками x10: {len(projects_with_errors):,}")
    print(f"📊 Процент: {len(projects_with_errors)/checked*100:.1f}%")
    
    if projects_with_errors:
        # Сортируем по количеству ошибок
        projects_with_errors.sort(key=lambda x: x['x10'], reverse=True)
        
        print(f"\n📋 ТОП-20 ПРОЕКТОВ С ОШИБКАМИ:")
        for proj in projects_with_errors[:20]:
            pct = proj['x10']/proj['total']*100
            print(f"  ❌ ID {proj['id']}: {proj['x10']}/{proj['total']} ({pct:.0f}%) - {proj['name'][:45]}")
        
        # Сохраняем отчет
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        report_file = Path(f"ПРОВЕРЕННЫЕ_CSV_{timestamp}.csv")
        
        print(f"\n💾 Сохраняю отчет...")
        
        import csv as csv_lib
        with open(report_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv_lib.writer(f)
            writer.writerow([
                'ID_Проекта', 'Название', 'ID_Товара', 'Товар',
                'Строка', 'Тираж_CSV', 'Тираж_БД', 'Маршрут', 'Ошибка_x10', 'URL'
            ])
            
            for proj in projects_with_errors:
                for r in proj['results']:
                    writer.writerow([
                        proj['id'], proj['name'],
                        r['product_id'], r['product_name'],
                        r['row'], r['csv_qty'], r['db_qty'],
                        r['route'], 'ДА' if r['is_x10'] else 'НЕТ',
                        proj['url']
                    ])
        
        print(f"✅ Отчет: {report_file}")
        
        # Список проектов
        summary_file = Path(f"СПИСОК_ОШИБОК_{timestamp}.csv")
        
        with open(summary_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID', 'Название', 'Ошибок_x10', 'Всего', 'Процент', 'URL'])
            
            for proj in projects_with_errors:
                pct = proj['x10']/proj['total']*100
                writer.writerow([
                    proj['id'], proj['name'], proj['x10'], 
                    proj['total'], f"{pct:.1f}%", proj['url']
                ])
        
        print(f"✅ Список: {summary_file}")
        
        # Статистика по проценту ошибок
        high_errors = [p for p in projects_with_errors if p['x10']/p['total'] > 0.5]
        medium_errors = [p for p in projects_with_errors if 0.1 < p['x10']/p['total'] <= 0.5]
        low_errors = [p for p in projects_with_errors if p['x10']/p['total'] <= 0.1]
        
        print(f"\n📊 РАСПРЕДЕЛЕНИЕ ПО СТЕПЕНИ ОШИБОК:")
        print(f"  🚨 Критично (>50% ошибок): {len(high_errors)} проектов")
        print(f"  ⚠️  Средне (10-50%): {len(medium_errors)} проектов")
        print(f"  ℹ️  Низко (<10%): {len(low_errors)} проектов")
        
        if high_errors:
            print(f"\n🚨 КРИТИЧНЫЕ ПРОЕКТЫ (>50% ошибок):")
            for proj in high_errors[:10]:
                pct = proj['x10']/proj['total']*100
                print(f"  ID {proj['id']}: {pct:.0f}% - {proj['name'][:50]}")
    else:
        print(f"\n✅ Отлично! В проверенных файлах нет ошибок x10")
    
    print("\n" + "="*70)

if __name__ == '__main__':
    main()





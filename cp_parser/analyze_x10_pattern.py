#!/usr/bin/env python3
"""
Анализ паттерна ошибок x10
Почему не все тиражи имеют ошибку?
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def extract_quantity_from_csv(csv_path, row_number):
    """Извлекает тираж из колонки E"""
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

def analyze_project_pattern(project_id, csv_path, db):
    """Детальный анализ одного проекта"""
    
    with db.get_session() as session:
        # Получаем ВСЕ товары и офферы (не только подозрительные)
        all_data = session.execute(text("""
            SELECT 
                p.id, p.name, p.row_number,
                po.quantity, po.route, po.price_usd
            FROM products p
            INNER JOIN price_offers po ON p.id = po.product_id
            WHERE p.project_id = :pid
            ORDER BY p.row_number, po.quantity
        """), {'pid': project_id}).fetchall()
        
        if not all_data:
            return None
        
        # Анализируем каждый оффер
        results = []
        checked_rows = {}
        
        for offer in all_data:
            row_num = offer.row_number
            
            if row_num not in checked_rows:
                checked_rows[row_num] = extract_quantity_from_csv(csv_path, row_num)
            
            csv_qty = checked_rows[row_num]
            db_qty = int(offer.quantity)
            
            is_x10 = False
            is_correct = False
            is_suspicious = (db_qty >= 300 and db_qty % 10 == 0)
            
            if csv_qty and isinstance(csv_qty, int):
                if csv_qty * 10 == db_qty:
                    is_x10 = True
                elif csv_qty == db_qty:
                    is_correct = True
            
            results.append({
                'row': row_num,
                'product_name': offer.name,
                'csv_qty': csv_qty,
                'db_qty': db_qty,
                'route': offer.route,
                'is_x10': is_x10,
                'is_correct': is_correct,
                'is_suspicious': is_suspicious,
                'price_usd': float(offer.price_usd) if offer.price_usd else None
            })
        
        return results

def main():
    print("="*70)
    print("🔍 АНАЛИЗ ПАТТЕРНА ОШИБОК x10")
    print("="*70)
    
    csv_dir = Path('verification_csv_all')
    db = PostgreSQLManager()
    
    # Берем несколько проектов с разным процентом ошибок
    test_projects = [
        204,  # 100% ошибок
        155,  # 53% ошибок
        197,  # 50% ошибок
        83,   # 26% ошибок
        271,  # 17% ошибок
    ]
    
    for proj_id in test_projects:
        csv_path = csv_dir / f"proj_{proj_id}.csv"
        
        if not csv_path.exists():
            print(f"\n⚠️  Проект {proj_id}: CSV не найден")
            continue
        
        print(f"\n{'='*70}")
        
        with db.get_session() as session:
            proj_info = session.execute(text("""
                SELECT project_name FROM projects WHERE id = :pid
            """), {'pid': proj_id}).fetchone()
        
        print(f"📊 ПРОЕКТ ID {proj_id}: {proj_info.project_name[:50]}")
        print("="*70)
        
        results = analyze_project_pattern(proj_id, csv_path, db)
        
        if not results:
            continue
        
        # Статистика
        total = len(results)
        x10_count = sum(1 for r in results if r['is_x10'])
        correct_count = sum(1 for r in results if r['is_correct'])
        suspicious_count = sum(1 for r in results if r['is_suspicious'])
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"  Всего офферов: {total}")
        print(f"  ❌ С ошибкой x10: {x10_count} ({x10_count/total*100:.1f}%)")
        print(f"  ✅ Правильные: {correct_count} ({correct_count/total*100:.1f}%)")
        print(f"  ⚠️  Подозрительные (>=300, кратны 10): {suspicious_count}")
        
        # Анализируем тиражи с ошибкой vs без ошибки
        x10_quantities = [r['db_qty'] for r in results if r['is_x10']]
        correct_quantities = [r['db_qty'] for r in results if r['is_correct']]
        
        print(f"\n🔍 ТИРАЖИ С ОШИБКОЙ x10:")
        print(f"  Диапазон: {min(x10_quantities) if x10_quantities else 'N/A'} - {max(x10_quantities) if x10_quantities else 'N/A'}")
        if x10_quantities:
            print(f"  Примеры: {sorted(set(x10_quantities))[:10]}")
        
        print(f"\n✅ ПРАВИЛЬНЫЕ ТИРАЖИ:")
        print(f"  Диапазон: {min(correct_quantities) if correct_quantities else 'N/A'} - {max(correct_quantities) if correct_quantities else 'N/A'}")
        if correct_quantities:
            print(f"  Примеры: {sorted(set(correct_quantities))[:10]}")
        
        # Проверяем паттерн: может ошибка только в определенных диапазонах?
        print(f"\n🎯 ПАТТЕРН АНАЛИЗ:")
        
        # Группируем по диапазонам тиражей
        ranges = {
            '< 500': [],
            '500-1000': [],
            '1000-5000': [],
            '5000-10000': [],
            '> 10000': []
        }
        
        for r in results:
            qty = r['db_qty']
            has_error = r['is_x10']
            
            if qty < 500:
                ranges['< 500'].append(has_error)
            elif qty < 1000:
                ranges['500-1000'].append(has_error)
            elif qty < 5000:
                ranges['1000-5000'].append(has_error)
            elif qty < 10000:
                ranges['5000-10000'].append(has_error)
            else:
                ranges['> 10000'].append(has_error)
        
        for range_name, errors_list in ranges.items():
            if errors_list:
                error_count = sum(errors_list)
                total_in_range = len(errors_list)
                pct = error_count / total_in_range * 100
                print(f"  {range_name:15}: {error_count}/{total_in_range} ({pct:.0f}% ошибок)")
        
        # Показываем несколько примеров с ошибками и без
        print(f"\n📝 ПРИМЕРЫ С ОШИБКОЙ x10:")
        x10_examples = [r for r in results if r['is_x10']][:3]
        for ex in x10_examples:
            print(f"  Строка {ex['row']}: CSV={ex['csv_qty']} → БД={ex['db_qty']} | {ex['route']}")
        
        print(f"\n📝 ПРИМЕРЫ БЕЗ ОШИБКИ (правильные):")
        correct_examples = [r for r in results if r['is_correct']][:3]
        for ex in correct_examples:
            print(f"  Строка {ex['row']}: CSV={ex['csv_qty']} = БД={ex['db_qty']} | {ex['route']}")
    
    print(f"\n\n{'='*70}")
    print("💡 ВЫВОДЫ")
    print("="*70)
    
    print("""
1. Проверим диапазоны тиражей где происходит ошибка
2. Возможно ошибка только в определенном диапазоне (например, только <1000)
3. Может быть связано с типом маршрута или другими условиями
4. Нужно понять логику парсера - почему умножал только часть тиражей
    """)

if __name__ == '__main__':
    main()



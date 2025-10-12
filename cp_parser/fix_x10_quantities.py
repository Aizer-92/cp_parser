#!/usr/bin/env python3
"""
Исправление тиражей с ошибкой x10 в БД
Использует данные из уже проверенных CSV
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

def main():
    print("="*70)
    print("🔧 ИСПРАВЛЕНИЕ ТИРАЖЕЙ x10 В БД")
    print("="*70)
    
    # Загружаем список ошибок из отчета
    report_file = Path("СПИСОК_ОШИБОК_20251011_1258.csv")
    
    if not report_file.exists():
        print(f"\n❌ Файл {report_file} не найден")
        print("Запустите сначала: python3 analyze_downloaded_csv.py")
        return
    
    print(f"\n📋 Загружаю список проектов с ошибками...")
    
    projects_to_fix = []
    with open(report_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            projects_to_fix.append({
                'id': int(row['ID']),
                'name': row['Название'],
                'errors': int(row['Ошибок_x10']),
                'total': int(row['Всего'])
            })
    
    print(f"✅ Найдено проектов с ошибками: {len(projects_to_fix)}")
    
    # Загружаем детальный отчет с конкретными офферами
    detail_file = Path("ПРОВЕРЕННЫЕ_CSV_20251011_1258.csv")
    
    if not detail_file.exists():
        print(f"❌ Файл {detail_file} не найден")
        return
    
    print(f"📊 Загружаю детальный отчет...")
    
    offers_to_fix = []
    with open(detail_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Ошибка_x10'] == 'ДА':
                offers_to_fix.append({
                    'project_id': int(row['ID_Проекта']),
                    'product_id': int(row['ID_Товара']),
                    'row': int(row['Строка']),
                    'csv_qty': int(row['Тираж_CSV']) if row['Тираж_CSV'] and row['Тираж_CSV'].isdigit() else None,
                    'db_qty': int(row['Тираж_БД']),
                    'route': row['Маршрут'],
                    'product_name': row['Товар']
                })
    
    print(f"✅ Найдено офферов для исправления: {len(offers_to_fix)}")
    
    if not offers_to_fix:
        print("\n✅ Нет офферов для исправления")
        return
    
    # Статистика
    total_errors = len(offers_to_fix)
    unique_products = len(set(o['product_id'] for o in offers_to_fix))
    unique_projects = len(set(o['project_id'] for o in offers_to_fix))
    
    print(f"\n📊 СТАТИСТИКА:")
    print(f"  Проектов: {unique_projects}")
    print(f"  Товаров: {unique_products}")
    print(f"  Офферов (price_offers): {total_errors}")
    
    # Группируем по проектам
    by_project = {}
    for offer in offers_to_fix:
        proj_id = offer['project_id']
        if proj_id not in by_project:
            by_project[proj_id] = []
        by_project[proj_id].append(offer)
    
    print(f"\n📋 ТОП-10 ПРОЕКТОВ ПО КОЛ-ВУ ОШИБОК:")
    sorted_projects = sorted(by_project.items(), key=lambda x: len(x[1]), reverse=True)
    for proj_id, offers in sorted_projects[:10]:
        proj_name = next((p['name'] for p in projects_to_fix if p['id'] == proj_id), 'N/A')
        print(f"  ID {proj_id}: {len(offers)} офферов - {proj_name[:45]}")
    
    # Запрашиваем подтверждение
    print(f"\n{'='*70}")
    print(f"⚠️  ВНИМАНИЕ!")
    print(f"{'='*70}")
    print(f"\nБудет исправлено {total_errors} записей в таблице price_offers")
    print(f"Все тиражи будут РАЗДЕЛЕНЫ НА 10")
    print(f"\nПример:")
    for offer in offers_to_fix[:3]:
        new_qty = offer['db_qty'] // 10
        print(f"  Проект {offer['project_id']}, Товар {offer['product_id']}: {offer['db_qty']} → {new_qty}")
    
    response = input(f"\n❓ Продолжить? (да/нет): ").strip().lower()
    
    if response not in ['да', 'yes', 'y']:
        print("\n❌ Отменено пользователем")
        return
    
    # Выполняем исправление
    print(f"\n🔧 Начинаю исправление...")
    
    db = PostgreSQLManager()
    
    with db.get_session() as session:
        fixed_count = 0
        
        for i, offer in enumerate(offers_to_fix, 1):
            if i % 100 == 0:
                print(f"\r  Обработано: {i}/{total_errors}", end='', flush=True)
            
            new_qty = offer['db_qty'] // 10
            
            # Обновляем quantity в price_offers
            session.execute(text("""
                UPDATE price_offers
                SET quantity = :new_qty,
                    updated_at = NOW()
                WHERE product_id = :product_id
                AND quantity = :old_qty
                AND route = :route
            """), {
                'new_qty': new_qty,
                'product_id': offer['product_id'],
                'old_qty': offer['db_qty'],
                'route': offer['route']
            })
            
            fixed_count += 1
        
        # Коммитим изменения
        session.commit()
        
        print(f"\n\n✅ Исправлено: {fixed_count} офферов")
    
    # Создаем отчет
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    log_file = Path(f"ИСПРАВЛЕНИЕ_x10_{timestamp}.csv")
    
    with open(log_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'ID_Проекта', 'ID_Товара', 'Название_товара',
            'Старый_тираж', 'Новый_тираж', 'Маршрут'
        ])
        
        for offer in offers_to_fix:
            new_qty = offer['db_qty'] // 10
            writer.writerow([
                offer['project_id'],
                offer['product_id'],
                offer['product_name'],
                offer['db_qty'],
                new_qty,
                offer['route']
            ])
    
    print(f"💾 Отчет сохранен: {log_file}")
    
    print(f"\n{'='*70}")
    print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО")
    print("="*70)
    print(f"\n📊 Исправлено офферов: {fixed_count}")
    print(f"📊 Проектов: {unique_projects}")
    print(f"📊 Товаров: {unique_products}")
    
    print(f"\n💡 Все тиражи разделены на 10 и обновлены в БД Railway")

if __name__ == '__main__':
    main()





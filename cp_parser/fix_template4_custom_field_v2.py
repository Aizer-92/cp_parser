#!/usr/bin/env python3
"""
Быстрое исправление custom_field - одним SQL запросом
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()

print("=" * 100)
print("🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ CUSTOM_FIELD В ШАБЛОНЕ 4")
print("=" * 100)

with open('template_4_perfect_ids.txt', 'r') as f:
    project_ids = [int(line.strip()) for line in f if line.strip()]

with db.get_session() as session:
    # Убираем "Образец" из custom_field одним запросом
    print("\n📝 Убираем 'Образец' из custom_field...")
    
    result = session.execute(text("""
        UPDATE products
        SET custom_field = TRIM(REGEXP_REPLACE(custom_field, ',?\s*Образец$', '', 'i'))
        WHERE project_id = ANY(:ids)
        AND custom_field LIKE '%Образец%'
    """), {'ids': project_ids})
    
    updated = result.rowcount
    session.commit()
    
    print(f"✅ Обновлено товаров: {updated}")
    
    # Проверяем результат
    print("\n📊 Проверка результата...")
    
    stats = session.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN custom_field LIKE '%Образец%' THEN 1 END) as still_with_obrazec
        FROM products
        WHERE project_id = ANY(:ids)
    """), {'ids': project_ids}).fetchone()
    
    total, still_with = stats
    
    print(f"   Всего товаров:             {total:,}")
    print(f"   Еще с 'Образец':           {still_with:,}")
    
    if still_with == 0:
        print("\n✅ УСПЕШНО! Все 'Образцы' убраны из custom_field")
    else:
        print(f"\n⚠️  Осталось {still_with} товаров с 'Образец'")
    
    # Примеры
    print("\n📋 ПРИМЕРЫ (после исправления):")
    examples = session.execute(text("""
        SELECT id, name, custom_field
        FROM products
        WHERE project_id = ANY(:ids)
        AND custom_field IS NOT NULL
        ORDER BY id
        LIMIT 5
    """), {'ids': project_ids}).fetchall()
    
    for prod_id, name, custom in examples:
        print(f"\nID {prod_id}: {name[:40]}")
        print(f"   Custom: {custom[:80]}")
    
    print("\n" + "=" * 100)

PYTHON_SCRIPT





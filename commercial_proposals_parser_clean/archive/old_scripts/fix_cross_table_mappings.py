#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для исправления смешивания изображений и товаров из разных таблиц
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata

def fix_cross_table_mappings():
    """
    Исправляет все случаи когда изображения из одной таблицы
    привязаны к товарам из другой таблицы
    """
    session = DatabaseManager.get_session()
    
    try:
        print("🔧 ИСПРАВЛЕНИЕ СМЕШИВАНИЯ ДАННЫХ ИЗ РАЗНЫХ ТАБЛИЦ")
        print("=" * 60)
        
        # Находим все неправильные привязки
        wrong_mappings = session.execute(text('''
            SELECT p.id as product_id, p.name, p.sheet_id as product_sheet, 
                   pi.id as image_id, pi.local_path, pi.sheet_id as image_sheet,
                   sm1.sheet_title as product_table, sm2.sheet_title as image_table
            FROM products p
            JOIN product_images pi ON p.id = pi.product_id
            LEFT JOIN sheets_metadata sm1 ON p.sheet_id = sm1.id
            LEFT JOIN sheets_metadata sm2 ON pi.sheet_id = sm2.id
            WHERE p.sheet_id != pi.sheet_id
            ORDER BY p.id
        ''')).fetchall()
        
        print(f"❌ Найдено {len(wrong_mappings)} неправильных привязок:")
        
        if not wrong_mappings:
            print("✅ Все привязки корректны!")
            return
        
        # Группируем по товарам
        products_with_issues = {}
        for row in wrong_mappings:
            if row.product_id not in products_with_issues:
                products_with_issues[row.product_id] = {
                    'name': row.name,
                    'product_table': row.product_table,
                    'wrong_images': []
                }
            products_with_issues[row.product_id]['wrong_images'].append({
                'image_id': row.image_id,
                'path': row.local_path,
                'image_table': row.image_table
            })
        
        # Показываем проблемы
        for product_id, info in products_with_issues.items():
            print(f"\n📦 Товар {product_id}: {info['name']} (из {info['product_table']})")
            for img in info['wrong_images']:
                print(f"   ❌ Изображение из {img['image_table']}: {Path(img['path']).name}")
        
        # Спрашиваем подтверждение
        print(f"\n⚠️ Будет отвязано {len(wrong_mappings)} изображений от неправильных товаров")
        choice = input("Продолжить? (y/N): ").lower().strip()
        
        if choice != 'y':
            print("❌ Операция отменена")
            return
        
        # Отвязываем неправильные изображения
        fixed_count = 0
        for row in wrong_mappings:
            image = session.query(ProductImage).filter(ProductImage.id == row.image_id).first()
            if image:
                print(f"   🔧 Отвязываем {Path(image.local_path).name} от товара {row.product_id}")
                image.product_id = None
                fixed_count += 1
        
        session.commit()
        
        print(f"\n✅ ИСПРАВЛЕНО: отвязано {fixed_count} изображений")
        print("📋 Теперь изображения можно правильно привязать к товарам из своих таблиц")
        
        # Статистика по таблицам
        print(f"\n📊 СТАТИСТИКА ПО ТАБЛИЦАМ:")
        tables_stats = session.execute(text('''
            SELECT sm.sheet_title,
                   COUNT(DISTINCT p.id) as products_count,
                   COUNT(DISTINCT pi.id) as images_count,
                   COUNT(DISTINCT CASE WHEN pi.product_id IS NOT NULL THEN pi.id END) as assigned_images
            FROM sheets_metadata sm
            LEFT JOIN products p ON sm.id = p.sheet_id
            LEFT JOIN product_images pi ON sm.id = pi.sheet_id
            GROUP BY sm.id, sm.sheet_title
            ORDER BY products_count DESC
        ''')).fetchall()
        
        for row in tables_stats:
            if row.products_count > 0:
                print(f"   📋 {row.sheet_title}")
                print(f"      📦 Товаров: {row.products_count}")
                print(f"      🖼️ Изображений: {row.images_count}")
                print(f"      🔗 Привязано: {row.assigned_images}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    fix_cross_table_mappings()

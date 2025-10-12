#!/usr/bin/env python3
"""
Быстрая проверка наличия "Новая категория" в БД
"""

import os
import sys

# Устанавливаем переменные окружения для Railway (если запускаем локально)
# os.environ["DATABASE_URL"] = "postgresql://..."

from database import load_categories_from_db

def main():
    print("🔍 Проверка категорий в БД...")
    print("="*60)
    
    try:
        categories = load_categories_from_db()
        print(f"✅ Загружено категорий: {len(categories)}")
        
        # Ищем "Новая категория"
        new_category = None
        for cat in categories:
            if cat.get('category') == 'Новая категория':
                new_category = cat
                break
        
        if new_category:
            print("\n✅ 'Новая категория' найдена в БД!")
            print("\nДанные:")
            print(f"  - category: {new_category.get('category')}")
            print(f"  - material: '{new_category.get('material', '')}'")
            print(f"  - rail_base: {new_category.get('rates', {}).get('rail_base', 'Н/Д')}")
            print(f"  - air_base: {new_category.get('rates', {}).get('air_base', 'Н/Д')}")
            print(f"  - description: {new_category.get('description', 'Н/Д')}")
        else:
            print("\n❌ 'Новая категория' НЕ найдена в БД!")
            print("\n📋 Доступные категории:")
            for cat in categories[:10]:  # Первые 10
                print(f"  - {cat.get('category')} ({cat.get('material', 'без материала')})")
            
            if len(categories) > 10:
                print(f"  ... и еще {len(categories) - 10} категорий")
        
        print("\n" + "="*60)
        return 0 if new_category else 1
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())






#!/usr/bin/env python3
"""
Удаление дублей товаров из БД
"""

import sys
from pathlib import Path
from sqlalchemy import text

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("🗑️  УДАЛЕНИЕ ДУБЛЕЙ ТОВАРОВ")
    print("=" * 80)
    
    # Загружаем список ID для удаления
    delete_file = 'real_duplicate_ids_to_delete_20251010_140909.txt'
    
    if not Path(delete_file).exists():
        print(f"\n❌ Файл {delete_file} не найден!")
        return
    
    with open(delete_file, 'r') as f:
        delete_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print(f"\n📋 Загружено ID для удаления: {len(delete_ids)}")
    
    with db.get_session() as session:
        # Сначала проверим что эти товары есть
        existing = session.execute(text("""
            SELECT COUNT(*)
            FROM products
            WHERE id = ANY(:ids)
        """), {'ids': delete_ids}).scalar()
        
        print(f"   Найдено в БД: {existing}")
        
        if existing != len(delete_ids):
            print(f"\n⚠️  ВНИМАНИЕ: {len(delete_ids) - existing} ID не найдены в БД!")
        
        # Проверяем связанные данные
        offers_count = session.execute(text("""
            SELECT COUNT(*)
            FROM price_offers
            WHERE product_id = ANY(:ids)
        """), {'ids': delete_ids}).scalar()
        
        images_count = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images
            WHERE product_id = ANY(:ids)
        """), {'ids': delete_ids}).scalar()
        
        print(f"\n📊 Связанные данные:")
        print(f"   • Ценовых предложений: {offers_count}")
        print(f"   • Изображений: {images_count}")
        
        print(f"\n⚠️  НАЧИНАЮ УДАЛЕНИЕ...")
        
        # Удаляем в правильном порядке (сначала зависимые таблицы)
        
        # 1. Удаляем price_offers
        print(f"\n  1️⃣  Удаление ценовых предложений...")
        result = session.execute(text("""
            DELETE FROM price_offers
            WHERE product_id = ANY(:ids)
        """), {'ids': delete_ids})
        deleted_offers = result.rowcount
        print(f"     ✅ Удалено: {deleted_offers}")
        
        # 2. Удаляем product_images
        print(f"\n  2️⃣  Удаление изображений...")
        result = session.execute(text("""
            DELETE FROM product_images
            WHERE product_id = ANY(:ids)
        """), {'ids': delete_ids})
        deleted_images = result.rowcount
        print(f"     ✅ Удалено: {deleted_images}")
        
        # 3. Удаляем products
        print(f"\n  3️⃣  Удаление товаров...")
        result = session.execute(text("""
            DELETE FROM products
            WHERE id = ANY(:ids)
        """), {'ids': delete_ids})
        deleted_products = result.rowcount
        print(f"     ✅ Удалено: {deleted_products}")
        
        # Коммитим изменения
        session.commit()
        
        print(f"\n" + "=" * 80)
        print(f"✅ УДАЛЕНИЕ ЗАВЕРШЕНО")
        print("=" * 80)
        print(f"\n📊 Итого удалено:")
        print(f"   • Товаров: {deleted_products}")
        print(f"   • Ценовых предложений: {deleted_offers}")
        print(f"   • Изображений: {deleted_images}")
        
        # Проверяем результат
        remaining = session.execute(text("""
            SELECT COUNT(*)
            FROM products
            WHERE id = ANY(:ids)
        """), {'ids': delete_ids}).scalar()
        
        if remaining == 0:
            print(f"\n✅✅✅ ВСЕ ДУБЛИ УСПЕШНО УДАЛЕНЫ!")
        else:
            print(f"\n⚠️  ВНИМАНИЕ: Осталось {remaining} товаров из списка!")
        
        # Финальная статистика
        total_products = session.execute(text("""
            SELECT COUNT(*) FROM products
        """)).scalar()
        
        total_offers = session.execute(text("""
            SELECT COUNT(*) FROM price_offers
        """)).scalar()
        
        total_images = session.execute(text("""
            SELECT COUNT(*) FROM product_images
        """)).scalar()
        
        print(f"\n📊 Итоговая статистика БД:")
        print(f"   • Товаров: {total_products}")
        print(f"   • Ценовых предложений: {total_offers}")
        print(f"   • Изображений: {total_images}")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    main()




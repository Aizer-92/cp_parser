#!/usr/bin/env python3
"""
Скрипт для сброса проектов Template 6 без офферов или с малым % офферов
1. Удаляет товары
2. Удаляет изображения
3. Меняет статус на 'pending'
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("🔄 СБРОС ПРОЕКТОВ TEMPLATE 6 БЕЗ ОФФЕРОВ")
    print("=" * 80)
    
    # Читаем список проектов
    projects_file = Path('projects_to_reset_all.txt')
    
    if not projects_file.exists():
        print("\n❌ Файл projects_to_reset_all.txt не найден!")
        print("   Сначала запустите анализ")
        return
    
    with open(projects_file, 'r') as f:
        project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]
    
    print(f"\n📋 Проектов для сброса: {len(project_ids)}")
    
    # Подтверждение
    print(f"\n⚠️  ВНИМАНИЕ!")
    print(f"   Это удалит:")
    print(f"   • Все товары из {len(project_ids)} проектов")
    print(f"   • Все изображения этих товаров")
    print(f"   • Все ценовые предложения (если есть)")
    print(f"   • Статус проектов изменится на 'pending'")
    
    response = input(f"\nПродолжить? (yes/no): ")
    
    if response.lower() != 'yes':
        print("\n❌ Отменено")
        return
    
    with db.get_session() as session:
        # Статистика ДО
        stats_before = session.execute(text("""
            SELECT 
                COUNT(DISTINCT p.id) as products,
                COUNT(DISTINCT pi.id) as images,
                COUNT(DISTINCT po.id) as offers
            FROM products p
            JOIN projects proj ON proj.table_id = p.table_id
            LEFT JOIN product_images pi ON pi.product_id = p.id
            LEFT JOIN price_offers po ON po.product_id = p.id
            WHERE proj.id = ANY(:ids)
        """), {'ids': project_ids}).first()
        
        print(f"\n📊 ДАННЫЕ ДО:")
        print(f"   Товаров: {stats_before.products:,}")
        print(f"   Изображений: {stats_before.images:,}")
        print(f"   Офферов: {stats_before.offers:,}")
        
        # ЭТАП 1: Удаляем изображения
        print(f"\n🗑️  Удаление изображений...")
        result_images = session.execute(text("""
            DELETE FROM product_images
            WHERE product_id IN (
                SELECT p.id
                FROM products p
                JOIN projects proj ON proj.table_id = p.table_id
                WHERE proj.id = ANY(:ids)
            )
        """), {'ids': project_ids})
        print(f"   ✅ Удалено изображений: {result_images.rowcount:,}")
        
        # ЭТАП 2: Удаляем ценовые предложения
        print(f"\n🗑️  Удаление ценовых предложений...")
        result_offers = session.execute(text("""
            DELETE FROM price_offers
            WHERE product_id IN (
                SELECT p.id
                FROM products p
                JOIN projects proj ON proj.table_id = p.table_id
                WHERE proj.id = ANY(:ids)
            )
        """), {'ids': project_ids})
        print(f"   ✅ Удалено офферов: {result_offers.rowcount:,}")
        
        # ЭТАП 3: Удаляем товары
        print(f"\n🗑️  Удаление товаров...")
        result_products = session.execute(text("""
            DELETE FROM products
            WHERE table_id IN (
                SELECT table_id FROM projects WHERE id = ANY(:ids)
            )
        """), {'ids': project_ids})
        print(f"   ✅ Удалено товаров: {result_products.rowcount:,}")
        
        # ЭТАП 4: Обновляем статус проектов
        print(f"\n🔄 Изменение статуса проектов...")
        result_status = session.execute(text("""
            UPDATE projects
            SET parsing_status = 'pending',
                total_products_found = 0,
                total_images_found = 0,
                updated_at = NOW()
            WHERE id = ANY(:ids)
        """), {'ids': project_ids})
        print(f"   ✅ Обновлено проектов: {result_status.rowcount}")
        
        # Коммит
        session.commit()
        
        print(f"\n" + "=" * 80)
        print(f"✅ СБРОС ЗАВЕРШЕН!")
        print(f"=" * 80)
        print(f"   Удалено:")
        print(f"   • Товаров: {result_products.rowcount:,}")
        print(f"   • Изображений: {result_images.rowcount:,}")
        print(f"   • Офферов: {result_offers.rowcount:,}")
        print(f"   Обновлено проектов: {result_status.rowcount}")
        
        print(f"\n💡 СЛЕДУЮЩИЙ ШАГ:")
        print(f"   Эти проекты теперь в статусе 'pending'")
        print(f"   Можно заново провалидировать с правильным шаблоном")

if __name__ == '__main__':
    main()


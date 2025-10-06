#!/usr/bin/env python3
"""
Очистка товаров без ценовых предложений.
Удаляет товары, которые не имеют ни одного ценового предложения.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from database import db_manager
from sqlalchemy import text
from loguru import logger

class ProductCleanup:
    """Очистка проблемных товаров"""
    
    def __init__(self):
        self.logger = logger
        
    def find_products_without_prices(self):
        """Находит товары без ценовых предложений"""
        
        with db_manager.get_session() as session:
            query = text("""
                SELECT 
                    p.id,
                    p.name,
                    p.table_id,
                    p.row_number,
                    proj.file_name
                FROM products p
                LEFT JOIN price_offers po ON p.id = po.product_id
                LEFT JOIN projects proj ON p.project_id = proj.id
                GROUP BY p.id, p.name, p.table_id, p.row_number, proj.file_name
                HAVING COUNT(po.id) = 0
                ORDER BY proj.file_name, p.row_number
            """)
            
            results = session.execute(query).fetchall()
            return results
    
    def delete_products_without_prices(self, dry_run=True):
        """Удаляет товары без ценовых предложений"""
        
        products_to_delete = self.find_products_without_prices()
        
        if not products_to_delete:
            print("✅ Товаров без ценовых предложений не найдено!")
            return 0
        
        print(f"🔍 Найдено {len(products_to_delete)} товаров без ценовых предложений:")
        
        # Группируем по файлам для лучшего отображения
        by_file = {}
        for product in products_to_delete:
            file_name = product.file_name
            if file_name not in by_file:
                by_file[file_name] = []
            by_file[file_name].append(product)
        
        # Показываем что будет удалено
        for file_name, products in by_file.items():
            print(f"\n📁 {file_name}: {len(products)} товаров")
            for product in products:
                print(f"   • ID {product.id}: {product.name} (строка {product.row_number})")
        
        if dry_run:
            print(f"\n🔍 РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА")
            print(f"   Для реального удаления запустите: python cleanup_products.py --execute")
            return 0
        
        # Реальное удаление
        print(f"\n🗑️  УДАЛЯЮ ТОВАРЫ БЕЗ ЦЕН...")
        
        deleted_count = 0
        with db_manager.get_session() as session:
            for product in products_to_delete:
                try:
                    # Удаляем связанные изображения
                    images_deleted = session.execute(
                        text("DELETE FROM product_images WHERE product_id = :product_id"),
                        {"product_id": product.id}
                    ).rowcount
                    
                    # Удаляем товар
                    session.execute(
                        text("DELETE FROM products WHERE id = :product_id"),
                        {"product_id": product.id}
                    )
                    
                    session.commit()
                    deleted_count += 1
                    
                    print(f"   ✅ Удален товар ID {product.id}: {product.name} (+ {images_deleted} изображений)")
                    
                except Exception as e:
                    session.rollback()
                    print(f"   ❌ Ошибка удаления товара ID {product.id}: {e}")
        
        print(f"\n✅ Удалено {deleted_count} товаров без ценовых предложений")
        return deleted_count
    
    def get_statistics_after_cleanup(self):
        """Получает статистику после очистки"""
        
        with db_manager.get_session() as session:
            stats = session.execute(text("""
                SELECT 
                    COUNT(DISTINCT p.id) as total_products,
                    COUNT(DISTINCT po.id) as total_price_offers,
                    COUNT(DISTINCT CASE WHEN po.id IS NOT NULL THEN p.id END) as products_with_prices,
                    COUNT(DISTINCT CASE WHEN po.id IS NULL THEN p.id END) as products_without_prices,
                    COUNT(DISTINCT pi.id) as total_images
                FROM products p
                LEFT JOIN price_offers po ON p.id = po.product_id
                LEFT JOIN product_images pi ON p.id = pi.product_id
            """)).fetchone()
            
            return stats

if __name__ == "__main__":
    import sys
    
    cleanup = ProductCleanup()
    
    # Проверяем аргументы командной строки
    execute_mode = "--execute" in sys.argv
    
    if execute_mode:
        print("⚠️  РЕЖИМ РЕАЛЬНОГО УДАЛЕНИЯ")
        print("=" * 50)
        
        # Показываем статистику до очистки
        stats_before = cleanup.get_statistics_after_cleanup()
        print(f"📊 СТАТИСТИКА ДО ОЧИСТКИ:")
        print(f"   • Товаров: {stats_before.total_products}")
        print(f"   • Ценовых предложений: {stats_before.total_price_offers}")
        print(f"   • Изображений: {stats_before.total_images}")
        
        # Выполняем очистку
        deleted_count = cleanup.delete_products_without_prices(dry_run=False)
        
        if deleted_count > 0:
            # Показываем статистику после очистки
            stats_after = cleanup.get_statistics_after_cleanup()
            print(f"\n📊 СТАТИСТИКА ПОСЛЕ ОЧИСТКИ:")
            print(f"   • Товаров: {stats_after.total_products} (было {stats_before.total_products})")
            print(f"   • Ценовых предложений: {stats_after.total_price_offers} (было {stats_before.total_price_offers})")
            print(f"   • Изображений: {stats_after.total_images} (было {stats_before.total_images})")
            
            print(f"\n🎯 РЕЗУЛЬТАТ: База данных очищена от {deleted_count} проблемных товаров!")
    else:
        # Режим предварительного просмотра
        cleanup.delete_products_without_prices(dry_run=True)



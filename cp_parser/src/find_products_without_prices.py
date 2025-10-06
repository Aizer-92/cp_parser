#!/usr/bin/env python3
"""
Поиск товаров без ценовых предложений.
Такие товары не должны существовать в системе.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from database import db_manager
from sqlalchemy import text
from loguru import logger

class ProductsWithoutPricesAnalyzer:
    """Анализатор товаров без ценовых предложений"""
    
    def __init__(self):
        self.logger = logger
        
    def find_products_without_prices(self):
        """Находит товары без ценовых предложений"""
        
        with db_manager.get_session() as session:
            # SQL запрос для поиска товаров без ценовых предложений
            query = text("""
                SELECT 
                    p.id,
                    p.name,
                    p.table_id,
                    p.row_number,
                    p.row_number_end,
                    proj.file_name,
                    COUNT(po.id) as price_offers_count
                FROM products p
                LEFT JOIN price_offers po ON p.id = po.product_id
                LEFT JOIN projects proj ON p.project_id = proj.id
                GROUP BY p.id, p.name, p.table_id, p.row_number, p.row_number_end, proj.file_name
                HAVING COUNT(po.id) = 0
                ORDER BY proj.file_name, p.row_number
            """)
            
            results = session.execute(query).fetchall()
            
            return results
    
    def find_products_with_few_prices(self, min_prices=2):
        """Находит товары с малым количеством ценовых предложений"""
        
        with db_manager.get_session() as session:
            # SQLite не поддерживает GROUP_CONCAT, используем альтернативный подход
            query = text("""
                SELECT 
                    p.id,
                    p.name,
                    p.table_id,
                    p.row_number,
                    proj.file_name,
                    COUNT(po.id) as price_offers_count
                FROM products p
                LEFT JOIN price_offers po ON p.id = po.product_id
                LEFT JOIN projects proj ON p.project_id = proj.id
                GROUP BY p.id, p.name, p.table_id, p.row_number, proj.file_name
                HAVING COUNT(po.id) > 0 AND COUNT(po.id) < :min_prices
                ORDER BY COUNT(po.id), proj.file_name, p.row_number
            """)
            
            results = session.execute(query, {"min_prices": min_prices}).fetchall()
            
            return results
    
    def get_general_statistics(self):
        """Получает общую статистику по товарам и ценам"""
        
        with db_manager.get_session() as session:
            stats_query = text("""
                SELECT 
                    COUNT(DISTINCT p.id) as total_products,
                    COUNT(DISTINCT po.id) as total_price_offers,
                    COUNT(DISTINCT CASE WHEN po.id IS NOT NULL THEN p.id END) as products_with_prices,
                    COUNT(DISTINCT CASE WHEN po.id IS NULL THEN p.id END) as products_without_prices,
                    ROUND(AVG(price_count.offers_per_product), 2) as avg_offers_per_product
                FROM products p
                LEFT JOIN price_offers po ON p.id = po.product_id
                LEFT JOIN (
                    SELECT product_id, COUNT(*) as offers_per_product
                    FROM price_offers
                    GROUP BY product_id
                ) price_count ON p.id = price_count.product_id
            """)
            
            stats = session.execute(stats_query).fetchone()
            
            return stats
    
    def print_analysis_report(self):
        """Выводит подробный отчет по товарам без цен"""
        
        print(f"\n🔍 АНАЛИЗ ТОВАРОВ БЕЗ ЦЕНОВЫХ ПРЕДЛОЖЕНИЙ")
        print(f"=" * 80)
        
        # Общая статистика
        stats = self.get_general_statistics()
        print(f"📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   • Всего товаров: {stats.total_products}")
        print(f"   • Всего ценовых предложений: {stats.total_price_offers}")
        print(f"   • Товаров с ценами: {stats.products_with_prices}")
        print(f"   • Товаров БЕЗ цен: {stats.products_without_prices}")
        print(f"   • Среднее предложений на товар: {stats.avg_offers_per_product}")
        
        # Товары без цен
        products_without_prices = self.find_products_without_prices()
        
        if products_without_prices:
            print(f"\n❌ ТОВАРЫ БЕЗ ЦЕНОВЫХ ПРЕДЛОЖЕНИЙ ({len(products_without_prices)} шт):")
            print(f"   ID  | Товар                          | Файл                     | Строка")
            print(f"   " + "-" * 75)
            
            for product in products_without_prices:
                product_name = product.name[:30] + "..." if len(product.name) > 30 else product.name
                file_name = product.file_name[:25] + "..." if len(product.file_name) > 25 else product.file_name
                row_info = f"{product.row_number}-{product.row_number_end}" if product.row_number_end != product.row_number else str(product.row_number)
                
                print(f"   {product.id:3d} | {product_name:30s} | {file_name:25s} | {row_info}")
        else:
            print(f"\n✅ Все товары имеют ценовые предложения!")
        
        # Товары с малым количеством цен
        products_with_few_prices = self.find_products_with_few_prices(min_prices=2)
        
        if products_with_few_prices:
            print(f"\n⚠️  ТОВАРЫ С МАЛЫМ КОЛИЧЕСТВОМ ЦЕНОВЫХ ПРЕДЛОЖЕНИЙ ({len(products_with_few_prices)} шт):")
            print(f"   ID  | Товар                          | Файл                     | Цены")
            print(f"   " + "-" * 75)
            
            for product in products_with_few_prices:
                product_name = product.name[:30] + "..." if len(product.name) > 30 else product.name
                file_name = product.file_name[:25] + "..." if len(product.file_name) > 25 else product.file_name
                
                print(f"   {product.id:3d} | {product_name:30s} | {file_name:25s} | {product.price_offers_count:4d} |")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        if products_without_prices:
            print(f"   1. ❌ Удалить {len(products_without_prices)} товаров без ценовых предложений")
            print(f"   2. 🔍 Проверить парсинг файлов, откуда эти товары")
            print(f"   3. 🛠️ Исправить логику парсера для предотвращения таких случаев")
        
        if products_with_few_prices:
            print(f"   4. ⚠️ Проверить {len(products_with_few_prices)} товаров с малым количеством предложений")
            print(f"   5. 📋 Убедиться, что все маршруты доставки парсятся корректно")
        
        if not products_without_prices and not products_with_few_prices:
            print(f"   ✅ Структура данных корректна - все товары имеют достаточно ценовых предложений")
        
        return len(products_without_prices), len(products_with_few_prices)

if __name__ == "__main__":
    analyzer = ProductsWithoutPricesAnalyzer()
    without_prices_count, few_prices_count = analyzer.print_analysis_report()
    
    if without_prices_count > 0:
        print(f"\n🚨 КРИТИЧЕСКАЯ ПРОБЛЕМА: Найдено {without_prices_count} товаров без цен!")
        print(f"   Запустите скрипт очистки для удаления проблемных товаров.")
    else:
        print(f"\n✅ Проблем не обнаружено - все товары имеют ценовые предложения.")

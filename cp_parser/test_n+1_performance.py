#!/usr/bin/env python3
"""
Тестирование производительности: проверка проблемы N+1
Замеряет количество запросов к БД и время выполнения
"""

import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text, event
from sqlalchemy.engine import Engine

# Счетчик запросов
query_count = 0
queries_log = []

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Перехватывает каждый SQL запрос"""
    global query_count, queries_log
    query_count += 1
    # Логируем только первые 100 символов запроса
    query_preview = statement.replace('\n', ' ')[:100]
    queries_log.append(f"Query #{query_count}: {query_preview}...")


def test_products_list_current():
    """Тестирует ТЕКУЩУЮ реализацию products_list (с N+1)"""
    global query_count, queries_log
    query_count = 0
    queries_log = []
    
    db = PostgreSQLManager()
    
    print("\n" + "="*80)
    print("📊 ТЕСТ: Текущая реализация products_list() [С ПРОБЛЕМОЙ N+1]")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    with db.get_session() as session:
        # Получаем 20 товаров (как на первой странице)
        products_sql = text("""
            SELECT id, name, description, article_number
            FROM products
            WHERE id IN (
                SELECT DISTINCT product_id 
                FROM product_images 
                WHERE product_id IS NOT NULL
            )
            LIMIT 20
        """)
        
        products = session.execute(products_sql).fetchall()
        
        # Для каждого товара делаем дополнительные запросы
        for product in products:
            product_id = product[0]
            
            # Запрос изображений (N+1)
            images_sql = text("""
                SELECT id, image_filename, is_main_image, image_url
                FROM product_images 
                WHERE product_id = :product_id 
                ORDER BY 
                    CASE WHEN is_main_image::text = 'true' THEN 0 ELSE 1 END,
                    cell_position,
                    display_order
                LIMIT 5
            """)
            session.execute(images_sql, {"product_id": product_id}).fetchall()
            
            # Запрос ценовых предложений (N+1)
            offers_sql = text("""
                SELECT id, quantity, price_usd, price_rub, delivery_time_days
                FROM price_offers 
                WHERE product_id = :product_id 
                ORDER BY quantity
                LIMIT 3
            """)
            session.execute(offers_sql, {"product_id": product_id}).fetchall()
    
    end_time = time.time()
    elapsed = (end_time - start_time) * 1000  # в миллисекундах
    
    print(f"⏱️  Время выполнения: {elapsed:.2f} мс")
    print(f"🔢 Количество запросов: {query_count}")
    print(f"📊 Формула: 1 (товары) + 20 (изображения) + 20 (цены) = {query_count}")
    print(f"\n💡 Проблема N+1 ПОДТВЕРЖДЕНА: {query_count - 1} лишних запросов!")
    
    return query_count, elapsed


def test_products_list_optimized():
    """Тестирует ОПТИМИЗИРОВАННУЮ реализацию (с подзапросами)"""
    global query_count, queries_log
    query_count = 0
    queries_log = []
    
    db = PostgreSQLManager()
    
    print("\n" + "="*80)
    print("📊 ТЕСТ: Оптимизированная реализация (с подзапросами)")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    with db.get_session() as session:
        # Один запрос со всеми данными
        optimized_sql = text("""
            SELECT 
                p.id,
                p.name,
                p.description,
                p.article_number,
                -- Главное изображение через подзапрос
                (SELECT pi.image_url
                 FROM product_images pi
                 WHERE pi.product_id = p.id
                 AND pi.is_main_image::text = 'true'
                 ORDER BY pi.cell_position
                 LIMIT 1) as main_image,
                -- Минимальная цена USD
                (SELECT MIN(po.price_usd)
                 FROM price_offers po
                 WHERE po.product_id = p.id) as min_price_usd,
                -- Максимальная цена USD
                (SELECT MAX(po.price_usd)
                 FROM price_offers po
                 WHERE po.product_id = p.id) as max_price_usd,
                -- Количество изображений
                (SELECT COUNT(*)
                 FROM product_images pi2
                 WHERE pi2.product_id = p.id) as images_count
            FROM products p
            WHERE p.id IN (
                SELECT DISTINCT product_id 
                FROM product_images 
                WHERE product_id IS NOT NULL
            )
            LIMIT 20
        """)
        
        products = session.execute(optimized_sql).fetchall()
    
    end_time = time.time()
    elapsed = (end_time - start_time) * 1000
    
    print(f"⏱️  Время выполнения: {elapsed:.2f} мс")
    print(f"🔢 Количество запросов: {query_count}")
    print(f"✅ Все данные в ОДНОМ запросе!")
    
    return query_count, elapsed


def main():
    """Главная функция"""
    print("\n" + "="*80)
    print("🔬 ТЕСТИРОВАНИЕ ПРОБЛЕМЫ N+1")
    print("="*80)
    print("\nЗамеряем производительность для страницы с 20 товарами")
    
    # Тест 1: Текущая реализация
    current_queries, current_time = test_products_list_current()
    
    # Тест 2: Оптимизированная реализация
    optimized_queries, optimized_time = test_products_list_optimized()
    
    # Сравнение
    print("\n" + "="*80)
    print("📈 СРАВНЕНИЕ РЕЗУЛЬТАТОВ")
    print("="*80 + "\n")
    
    print(f"{'Метрика':<30} | {'Текущая':<15} | {'Оптимизированная':<15} | Улучшение")
    print("-"*80)
    
    queries_improvement = ((current_queries - optimized_queries) / current_queries * 100)
    time_improvement = ((current_time - optimized_time) / current_time * 100)
    
    print(f"{'Количество запросов':<30} | {current_queries:<15} | {optimized_queries:<15} | -{queries_improvement:.1f}%")
    print(f"{'Время выполнения (мс)':<30} | {current_time:<15.2f} | {optimized_time:<15.2f} | -{time_improvement:.1f}%")
    print(f"{'Лишних запросов':<30} | {current_queries - 1:<15} | {optimized_queries - 1:<15} | ")
    
    print("\n" + "="*80)
    print("💡 ВЫВОД:")
    print("="*80)
    print(f"  Оптимизация убирает {current_queries - optimized_queries} запросов ({queries_improvement:.0f}%)")
    print(f"  Ускорение в {current_time / optimized_time:.1f}x раз")
    print(f"  Экономия времени: {current_time - optimized_time:.2f} мс на странице")
    
    # Экстраполяция на большие объемы
    print("\n📊 ЭКСТРАПОЛЯЦИЯ НА БОЛЬШИЕ ОБЪЕМЫ:")
    print("-"*80)
    
    for n_products in [50, 100, 200]:
        estimated_current = current_time * (n_products / 20)
        estimated_optimized = optimized_time * (n_products / 20)
        
        print(f"  {n_products} товаров:")
        print(f"    Текущая:          {estimated_current:6.0f} мс  ({1 + n_products * 2} запросов)")
        print(f"    Оптимизированная: {estimated_optimized:6.0f} мс  (1 запрос)")
        print(f"    Разница:          {estimated_current - estimated_optimized:6.0f} мс")
        print()
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()


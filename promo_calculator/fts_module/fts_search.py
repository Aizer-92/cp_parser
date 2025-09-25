#!/usr/bin/env python3
"""
Модуль полнотекстового поиска для PostgreSQL
Включает создание FTS индексов, весовые коэффициенты и ранжирование
"""

import psycopg2
import os
import logging
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class FullTextSearch:
    """Класс для работы с полнотекстовым поиском PostgreSQL"""
    
    def __init__(self, pg_config: Dict[str, str]):
        """
        Инициализация FTS модуля
        
        Args:
            pg_config: Конфигурация PostgreSQL
        """
        self.pg_config = pg_config
        self.weights = {
            'A': ['title', 'original_title'],  # Высокий вес - заголовки
            'B': ['brand', 'vendor'],          # Средний вес - бренды и поставщики
            'C': ['description']               # Низкий вес - описания
        }
    
    def get_connection(self):
        """Создание соединения с PostgreSQL"""
        conn = psycopg2.connect(**self.pg_config)
        conn.set_client_encoding('UTF8')
        return conn
    
    def create_fts_structure(self) -> bool:
        """
        Создание структуры для полнотекстового поиска
        
        Returns:
            bool: True если успешно создано
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            logger.info("🔍 Создание структуры FTS...")
            
            # 1. Добавляем search_vector колонку
            cursor.execute("""
                ALTER TABLE products 
                ADD COLUMN IF NOT EXISTS search_vector tsvector
            """)
            
            # 2. Создаем функцию для обновления search_vector с весами
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- Используем 'russian' конфигурацию для правильной морфологии
                    NEW.search_vector := 
                        setweight(to_tsvector('russian', COALESCE(NEW.title, '')), 'A') ||
                        setweight(to_tsvector('russian', COALESCE(NEW.original_title, '')), 'A') ||
                        setweight(to_tsvector('russian', COALESCE(NEW.brand, '')), 'B') ||
                        setweight(to_tsvector('russian', COALESCE(NEW.vendor, '')), 'B') ||
                        setweight(to_tsvector('russian', COALESCE(NEW.description, '')), 'C');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
            """)
            
            # 3. Создаем триггер для автоматического обновления
            cursor.execute("""
                DROP TRIGGER IF EXISTS update_products_search_vector ON products;
                CREATE TRIGGER update_products_search_vector
                    BEFORE INSERT OR UPDATE ON products
                    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
            """)
            
            # 4. Создаем GIN индекс для быстрого поиска
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_products_search_vector 
                ON products USING gin(search_vector)
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("✅ Структура FTS создана")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания структуры FTS: {e}")
            return False
    
    def populate_search_vectors(self) -> bool:
        """
        Заполнение search_vector для существующих записей
        
        Returns:
            bool: True если успешно заполнено
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            logger.info("📊 Заполнение search_vector для существующих записей...")
            
            cursor.execute("""
                UPDATE products SET search_vector = 
                    setweight(to_tsvector('russian', COALESCE(title, '')), 'A') ||
                    setweight(to_tsvector('russian', COALESCE(original_title, '')), 'A') ||
                    setweight(to_tsvector('russian', COALESCE(brand, '')), 'B') ||
                    setweight(to_tsvector('russian', COALESCE(vendor, '')), 'B') ||
                    setweight(to_tsvector('russian', COALESCE(description, '')), 'C')
            """)
            
            updated_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Обновлено {updated_count} записей")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка заполнения search_vector: {e}")
            return False
    
    def search_products(self, query: str, limit: int = 25, offset: int = 0) -> Tuple[List[Dict], int]:
        """
        Поиск товаров с ранжированием
        
        Args:
            query: Поисковый запрос
            limit: Количество результатов
            offset: Смещение для пагинации
            
        Returns:
            Tuple[List[Dict], int]: (список товаров, общее количество)
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Поиск с ранжированием (используем russian конфигурацию для правильной морфологии)
            search_query = """
                SELECT p.id, p.offer_id, p.title, p.original_title, p.vendor, 
                       p.has_specifications, p.has_images, p.moq_min, p.moq_max,
                       p.brand, p.description, p.lead_time, p.source_url, p.source_databases,
                       ts_rank_cd(p.search_vector, plainto_tsquery('russian', %s), 32) as rank
                FROM products p
                WHERE p.search_vector @@ plainto_tsquery('russian', %s)
                ORDER BY rank DESC, p.id DESC
                LIMIT %s OFFSET %s
            """
            
            cursor.execute(search_query, (query, query, limit, offset))
            products = cursor.fetchall()
            
            # Подсчет общего количества
            count_query = """
                SELECT COUNT(*) FROM products p
                WHERE p.search_vector @@ plainto_tsquery('russian', %s)
            """
            cursor.execute(count_query, (query,))
            total_count = cursor.fetchone()[0]
            
            # Обработка результатов
            result_products = []
            for product in products:
                product_dict = {
                    'id': product[0],
                    'offer_id': product[1],
                    'title': product[2],
                    'original_title': product[3],
                    'vendor': product[4],
                    'has_specifications': product[5],
                    'has_images': product[6],
                    'moq_min': product[7] or 0,
                    'moq_max': product[8] or 0,
                    'brand': product[9],
                    'description': product[10],
                    'lead_time': product[11],
                    'source_url': product[12],
                    'source_databases': product[13],
                    'search_rank': float(product[14]) if product[14] else 0.0
                }
                result_products.append(product_dict)
            
            cursor.close()
            conn.close()
            
            return result_products, total_count
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска: {e}")
            return [], 0
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """
        Получение предложений для автодополнения
        
        Args:
            query: Частичный запрос
            limit: Количество предложений
            
        Returns:
            List[str]: Список предложений
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Поиск похожих заголовков
            cursor.execute("""
                SELECT DISTINCT title
                FROM products 
                WHERE title ILIKE %s
                ORDER BY title
                LIMIT %s
            """, (f"%{query}%", limit))
            
            suggestions = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения предложений: {e}")
            return []
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики поиска
        
        Returns:
            Dict[str, Any]: Статистика
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Общее количество товаров
            cursor.execute("SELECT COUNT(*) FROM products")
            total_products = cursor.fetchone()[0]
            
            # Количество товаров с search_vector
            cursor.execute("SELECT COUNT(*) FROM products WHERE search_vector IS NOT NULL")
            products_with_fts = cursor.fetchone()[0]
            
            # Размер индекса
            cursor.execute("""
                SELECT pg_size_pretty(pg_relation_size('idx_products_search_vector'))
            """)
            index_size = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'total_products': total_products,
                'products_with_fts': products_with_fts,
                'fts_coverage': f"{(products_with_fts / total_products * 100):.1f}%" if total_products > 0 else "0%",
                'index_size': index_size,
                'weights': self.weights
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {}
    
    def test_search(self, test_queries: List[str] = None) -> Dict[str, Any]:
        """
        Тестирование поиска
        
        Args:
            test_queries: Список тестовых запросов
            
        Returns:
            Dict[str, Any]: Результаты тестирования
        """
        if test_queries is None:
            test_queries = ["телефон", "платье", "обувь", "часы", "сумка"]
        
        results = {}
        
        for query in test_queries:
            try:
                products, count = self.search_products(query, limit=5)
                results[query] = {
                    'count': count,
                    'top_results': [
                        {
                            'title': p['title'][:50],
                            'rank': p['search_rank']
                        } for p in products[:3]
                    ]
                }
            except Exception as e:
                results[query] = {'error': str(e)}
        
        return results

# Функция для инициализации FTS
def initialize_fts(pg_config: Dict[str, str]) -> bool:
    """
    Инициализация полнотекстового поиска
    
    Args:
        pg_config: Конфигурация PostgreSQL
        
    Returns:
        bool: True если успешно инициализировано
    """
    fts = FullTextSearch(pg_config)
    
    # Создаем структуру
    if not fts.create_fts_structure():
        return False
    
    # Заполняем search_vector
    if not fts.populate_search_vectors():
        return False
    
    # Тестируем
    test_results = fts.test_search()
    logger.info("🧪 Результаты тестирования:")
    for query, result in test_results.items():
        if 'error' not in result:
            logger.info(f"  {query}: {result['count']} товаров")
        else:
            logger.error(f"  {query}: {result['error']}")
    
    return True

if __name__ == "__main__":
    # Тестирование модуля
    pg_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'promo_calculator'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
    }
    
    logging.basicConfig(level=logging.INFO)
    
    if initialize_fts(pg_config):
        print("✅ FTS модуль успешно инициализирован")
    else:
        print("❌ Ошибка инициализации FTS модуля")

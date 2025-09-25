#!/usr/bin/env python3
"""
Скрипт для детального анализа итоговой БД
"""
import sqlite3
from pathlib import Path
from datetime import datetime

class FinalDatabaseAnalyzer:
    """Анализатор итоговой БД"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.db_path = self.results_dir / "all_chunks_database.db"
        
        # Статистика
        self.stats = {
            'total_products': 0,
            'total_images': 0,
            'total_specs': 0,
            'products_with_images': 0,
            'products_with_specs': 0,
            'products_with_descriptions': 0,
            'products_without_images': 0,
            'products_without_specs': 0,
            'products_without_descriptions': 0,
            'avg_images_per_product': 0,
            'avg_specs_per_product': 0,
            'avg_description_length': 0
        }
    
    def analyze_final_database(self):
        """Анализирует итоговую БД"""
        try:
            print("🔍 ДЕТАЛЬНЫЙ АНАЛИЗ ИТОГОВОЙ БД")
            print("=" * 60)
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика
            self.get_basic_stats(cursor)
            
            # Анализ покрытия данными
            self.analyze_data_coverage(cursor)
            
            # Анализ качества данных
            self.analyze_data_quality(cursor)
            
            # Анализ оставшихся проблем
            self.analyze_remaining_issues(cursor)
            
            # Анализ по типам chunks
            self.analyze_chunk_sources(cursor)
            
            conn.close()
            
            # Выводим итоговую статистику
            self.print_final_statistics()
            
            # Рекомендации
            self.print_recommendations()
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
    
    def get_basic_stats(self, cursor):
        """Получает базовую статистику"""
        print("📊 БАЗОВАЯ СТАТИСТИКА БД")
        print("-" * 40)
        
        # Общие количества
        cursor.execute('SELECT COUNT(*) FROM products')
        self.stats['total_products'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM images')
        self.stats['total_images'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM specifications')
        self.stats['total_specs'] = cursor.fetchone()[0]
        
        print(f"📦 Всего товаров: {self.stats['total_products']:,}")
        print(f"🖼️ Всего изображений: {self.stats['total_images']:,}")
        print(f"📋 Всего характеристик: {self.stats['total_specs']:,}")
        
        # Средние значения
        if self.stats['total_products'] > 0:
            self.stats['avg_images_per_product'] = self.stats['total_images'] / self.stats['total_products']
            self.stats['avg_specs_per_product'] = self.stats['total_specs'] / self.stats['total_products']
            
            print(f"📊 Среднее изображений на товар: {self.stats['avg_images_per_product']:.1f}")
            print(f"📊 Среднее характеристик на товар: {self.stats['avg_specs_per_product']:.1f}")
        
        print()
    
    def analyze_data_coverage(self, cursor):
        """Анализирует покрытие данными"""
        print("📈 АНАЛИЗ ПОКРЫТИЯ ДАННЫМИ")
        print("-" * 40)
        
        # Товары с изображениями
        cursor.execute('''
            SELECT COUNT(*) FROM products p
            WHERE EXISTS (SELECT 1 FROM images i WHERE i.item_id = p.item_id)
        ''')
        self.stats['products_with_images'] = cursor.fetchone()[0]
        self.stats['products_without_images'] = self.stats['total_products'] - self.stats['products_with_images']
        
        # Товары с характеристиками
        cursor.execute('''
            SELECT COUNT(*) FROM products p
            WHERE EXISTS (SELECT 1 FROM specifications s WHERE s.item_id = p.item_id)
        ''')
        self.stats['products_with_specs'] = cursor.fetchone()[0]
        self.stats['products_without_specs'] = self.stats['total_products'] - self.stats['products_with_specs']
        
        # Товары с описаниями
        cursor.execute('''
            SELECT COUNT(*) FROM products
            WHERE description IS NOT NULL AND description != '' AND description != 'Описание товара'
        ''')
        self.stats['products_with_descriptions'] = cursor.fetchone()[0]
        self.stats['products_without_descriptions'] = self.stats['total_products'] - self.stats['products_with_descriptions']
        
        # Проценты покрытия
        coverage_images = (self.stats['products_with_images'] / self.stats['total_products']) * 100
        coverage_specs = (self.stats['products_with_specs'] / self.stats['total_products']) * 100
        coverage_descriptions = (self.stats['products_with_descriptions'] / self.stats['total_products']) * 100
        
        print(f"🖼️ Покрытие изображениями:")
        print(f"   С изображениями: {self.stats['products_with_images']:,} ({coverage_images:.1f}%)")
        print(f"   Без изображений: {self.stats['products_without_images']:,} ({100-coverage_images:.1f}%)")
        
        print(f"\n📋 Покрытие характеристиками:")
        print(f"   С характеристиками: {self.stats['products_with_specs']:,} ({coverage_specs:.1f}%)")
        print(f"   Без характеристик: {self.stats['products_without_specs']:,} ({100-coverage_specs:.1f}%)")
        
        print(f"\n📝 Покрытие описаниями:")
        print(f"   С описаниями: {self.stats['products_with_descriptions']:,} ({coverage_descriptions:.1f}%)")
        print(f"   Без описаний: {self.stats['products_without_descriptions']:,} ({100-coverage_descriptions:.1f}%)")
        
        print()
    
    def analyze_data_quality(self, cursor):
        """Анализирует качество данных"""
        print("🔬 АНАЛИЗ КАЧЕСТВА ДАННЫХ")
        print("-" * 40)
        
        # Длина описаний
        cursor.execute('''
            SELECT 
                AVG(LENGTH(description)) as avg_length,
                MIN(LENGTH(description)) as min_length,
                MAX(LENGTH(description)) as max_length
            FROM products
            WHERE description IS NOT NULL AND description != '' AND description != 'Описание товара'
        ''')
        
        result = cursor.fetchone()
        if result and result[0]:
            avg_len, min_len, max_len = result
            self.stats['avg_description_length'] = avg_len
            
            print(f"📏 Длина описаний:")
            print(f"   Средняя: {avg_len:.1f} символов")
            print(f"   Минимальная: {min_len} символов")
            print(f"   Максимальная: {max_len:,} символов")
        
        # Распределение изображений
        cursor.execute('''
            SELECT 
                COUNT(*) as count,
                COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products) as percentage
            FROM products p
            WHERE (
                SELECT COUNT(*) FROM images i WHERE i.item_id = p.item_id
            ) = 0
        ''')
        
        result = cursor.fetchone()
        if result:
            print(f"\n🖼️ Товары без изображений: {result[0]:,} ({result[1]:.1f}%)")
        
        # Распределение характеристик
        cursor.execute('''
            SELECT 
                COUNT(*) as count,
                COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products) as percentage
            FROM products p
            WHERE (
                SELECT COUNT(*) FROM specifications s WHERE s.item_id = p.item_id
            ) = 0
        ''')
        
        result = cursor.fetchone()
        if result:
            print(f"📋 Товары без характеристик: {result[0]:,} ({result[1]:.1f}%)")
        
        print()
    
    def analyze_remaining_issues(self, cursor):
        """Анализирует оставшиеся проблемы"""
        print("🚨 АНАЛИЗ ОСТАВШИХСЯ ПРОБЛЕМ")
        print("-" * 40)
        
        # Товары без изображений
        if self.stats['products_without_images'] > 0:
            cursor.execute('''
                SELECT item_id, title, chunk_source, chunk_type
                FROM products p
                WHERE NOT EXISTS (SELECT 1 FROM images i WHERE i.item_id = p.item_id)
                LIMIT 10
            ''')
            
            items_without_images = cursor.fetchall()
            print(f"🖼️ ПРИМЕРЫ ТОВАРОВ БЕЗ ИЗОБРАЖЕНИЙ (первые 10):")
            for i, (item_id, title, chunk_source, chunk_type) in enumerate(items_without_images):
                print(f"   {i+1}. {item_id} - {title[:50]}... (источник: {chunk_source}/{chunk_type})")
        
        # Товары без характеристик
        if self.stats['products_without_specs'] > 0:
            cursor.execute('''
                SELECT item_id, title, chunk_source, chunk_type
                FROM products p
                WHERE NOT EXISTS (SELECT 1 FROM specifications s WHERE s.item_id = p.item_id)
                LIMIT 10
            ''')
            
            items_without_specs = cursor.fetchall()
            print(f"\n📋 ПРИМЕРЫ ТОВАРОВ БЕЗ ХАРАКТЕРИСТИК (первые 10):")
            for i, (item_id, title, chunk_source, chunk_type) in enumerate(items_without_specs):
                print(f"   {i+1}. {item_id} - {title[:50]}... (источник: {chunk_source}/{chunk_type})")
        
        print()
    
    def analyze_chunk_sources(self, cursor):
        """Анализирует источники chunks"""
        print("📁 АНАЛИЗ ИСТОЧНИКОВ CHUNKS")
        print("-" * 40)
        
        # Статистика по источникам
        cursor.execute('''
            SELECT 
                chunk_source,
                chunk_type,
                COUNT(*) as count,
                COUNT(*) * 100.0 / (SELECT COUNT(*) FROM products) as percentage
            FROM products
            GROUP BY chunk_source, chunk_type
            ORDER BY count DESC
        ''')
        
        sources = cursor.fetchall()
        print(f"📊 РАСПРЕДЕЛЕНИЕ ПО ИСТОЧНИКАМ:")
        for source, chunk_type, count, percentage in sources:
            print(f"   {source}/{chunk_type}: {count:,} ({percentage:.1f}%)")
        
        print()
    
    def print_final_statistics(self):
        """Выводит итоговую статистику"""
        print("=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА БД")
        print("=" * 60)
        
        print(f"📦 ВСЕГО ТОВАРОВ: {self.stats['total_products']:,}")
        print(f"🖼️ ВСЕГО ИЗОБРАЖЕНИЙ: {self.stats['total_images']:,}")
        print(f"📋 ВСЕГО ХАРАКТЕРИСТИК: {self.stats['total_specs']:,}")
        
        print(f"\n📈 ПОКРЫТИЕ ДАННЫМИ:")
        print(f"   Изображениями: {self.stats['products_with_images']:,} ({(self.stats['products_with_images']/self.stats['total_products'])*100:.1f}%)")
        print(f"   Характеристиками: {self.stats['products_with_specs']:,} ({(self.stats['products_with_specs']/self.stats['total_products'])*100:.1f}%)")
        print(f"   Описаниями: {self.stats['products_with_descriptions']:,} ({(self.stats['products_with_descriptions']/self.stats['total_products'])*100:.1f}%)")
        
        print(f"\n📊 СРЕДНИЕ ПОКАЗАТЕЛИ:")
        print(f"   Изображений на товар: {self.stats['avg_images_per_product']:.1f}")
        print(f"   Характеристик на товар: {self.stats['avg_specs_per_product']:.1f}")
        print(f"   Длина описания: {self.stats['avg_description_length']:.1f} символов")
        
        print(f"\n🚨 ПРОБЛЕМНЫЕ ТОВАРЫ:")
        print(f"   Без изображений: {self.stats['products_without_images']:,}")
        print(f"   Без характеристик: {self.stats['products_without_specs']:,}")
        print(f"   Без описаний: {self.stats['products_without_descriptions']:,}")
    
    def print_recommendations(self):
        """Выводит рекомендации"""
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        
        if self.stats['products_without_images'] > 0:
            print(f"   ⚠️  {self.stats['products_without_images']} товаров без изображений")
            if self.stats['products_without_images'] <= 100:
                print(f"      🎯 Можно допарсить вручную (небольшое количество)")
            else:
                print(f"      🎯 Нужен массовый парсинг")
        
        if self.stats['products_without_specs'] > 0:
            print(f"   ⚠️  {self.stats['products_without_specs']} товаров без характеристик")
            if self.stats['products_without_specs'] <= 1000:
                print(f"      🎯 Можно допарсить по частям")
            else:
                print(f"      🎯 Требуется массовый парсинг")
        
        if self.stats['products_without_descriptions'] > 0:
            print(f"   ⚠️  {self.stats['products_without_descriptions']} товаров без описаний")
        
        # Общая оценка
        image_coverage = (self.stats['products_with_images'] / self.stats['total_products']) * 100
        spec_coverage = (self.stats['products_with_specs'] / self.stats['total_products']) * 100
        
        print(f"\n🏆 ОБЩАЯ ОЦЕНКА КАЧЕСТВА:")
        if image_coverage >= 99 and spec_coverage >= 80:
            print(f"   🥇 ОТЛИЧНОЕ качество! БД готова к использованию")
        elif image_coverage >= 95 and spec_coverage >= 70:
            print(f"   🥈 ХОРОШЕЕ качество! Можно использовать")
        elif image_coverage >= 90 and spec_coverage >= 60:
            print(f"   🥉 УДОВЛЕТВОРИТЕЛЬНОЕ качество! Требует доработки")
        else:
            print(f"   ⚠️  НИЗКОЕ качество! Требует серьезной доработки")

def main():
    """Основная функция"""
    analyzer = FinalDatabaseAnalyzer()
    analyzer.analyze_final_database()

if __name__ == "__main__":
    main()

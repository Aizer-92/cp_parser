#!/usr/bin/env python3
"""
Скрипт для проверки описаний товаров в БД
"""
import sqlite3
from pathlib import Path
import re

class DescriptionChecker:
    """Проверяет описания товаров в БД"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.db_path = self.results_dir / "all_chunks_database.db"
        
        # Статистика
        self.stats = {
            'total_products': 0,
            'with_descriptions': 0,
            'without_descriptions': 0,
            'empty_descriptions': 0,
            'html_descriptions': 0,
            'long_descriptions': 0,
            'short_descriptions': 0,
            'avg_description_length': 0
        }
    
    def check_descriptions(self):
        """Проверяет описания товаров"""
        try:
            print("🔍 ПРОВЕРКА ОПИСАНИЙ ТОВАРОВ В БД")
            print("=" * 60)
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика
            self.get_basic_stats(cursor)
            
            # Анализ качества описаний
            self.analyze_description_quality(cursor)
            
            # Примеры описаний
            self.show_description_examples(cursor)
            
            # Анализ HTML в описаниях
            self.analyze_html_in_descriptions(cursor)
            
            conn.close()
            
            # Выводим итоговую статистику
            self.print_final_statistics()
            
        except Exception as e:
            print(f"❌ Ошибка проверки: {e}")
    
    def get_basic_stats(self, cursor):
        """Получает базовую статистику"""
        print("📊 БАЗОВАЯ СТАТИСТИКА ОПИСАНИЙ")
        print("-" * 40)
        
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        self.stats['total_products'] = total_products
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE description IS NOT NULL AND description != ""')
        with_descriptions = cursor.fetchone()[0]
        self.stats['with_descriptions'] = with_descriptions
        
        cursor.execute('SELECT COUNT(*) FROM products WHERE description IS NULL OR description = ""')
        without_descriptions = cursor.fetchone()[0]
        self.stats['without_descriptions'] = without_descriptions
        
        print(f"📦 Всего товаров: {total_products:,}")
        print(f"📝 С описаниями: {with_descriptions:,} ({with_descriptions/total_products*100:.1f}%)")
        print(f"❌ Без описаний: {without_descriptions:,} ({without_descriptions/total_products*100:.1f}%)")
        print()
    
    def analyze_description_quality(self, cursor):
        """Анализирует качество описаний"""
        print("📊 АНАЛИЗ КАЧЕСТВА ОПИСАНИЙ")
        print("-" * 40)
        
        # Длина описаний
        cursor.execute('''
            SELECT 
                COUNT(*) as total,
                AVG(LENGTH(description)) as avg_length,
                MIN(LENGTH(description)) as min_length,
                MAX(LENGTH(description)) as max_length
            FROM products 
            WHERE description IS NOT NULL AND description != ""
        ''')
        
        result = cursor.fetchone()
        if result and result[0] > 0:
            total, avg_len, min_len, max_len = result
            self.stats['avg_description_length'] = avg_len
            
            print(f"📏 Длина описаний:")
            print(f"   Средняя: {avg_len:.1f} символов")
            print(f"   Минимальная: {min_len} символов")
            print(f"   Максимальная: {max_len:,} символов")
            
            # Категории по длине
            cursor.execute('''
                SELECT 
                    CASE 
                        WHEN LENGTH(description) < 50 THEN 'Короткие (<50)'
                        WHEN LENGTH(description) < 200 THEN 'Средние (50-200)'
                        WHEN LENGTH(description) < 1000 THEN 'Длинные (200-1000)'
                        ELSE 'Очень длинные (>1000)'
                    END as category,
                    COUNT(*) as count
                FROM products 
                WHERE description IS NOT NULL AND description != ""
                GROUP BY category
                ORDER BY count DESC
            ''')
            
            categories = cursor.fetchall()
            print(f"\n📊 Распределение по длине:")
            for category, count in categories:
                print(f"   {category}: {count:,} ({count/total*100:.1f}%)")
                if 'Короткие' in category:
                    self.stats['short_descriptions'] = count
                elif 'Длинные' in category or 'Очень длинные' in category:
                    self.stats['long_descriptions'] += count
        
        print()
    
    def show_description_examples(self, cursor):
        """Показывает примеры описаний"""
        print("📋 ПРИМЕРЫ ОПИСАНИЙ")
        print("-" * 40)
        
        # Короткие описания
        cursor.execute('''
            SELECT title, description, LENGTH(description) as len
            FROM products 
            WHERE description IS NOT NULL AND description != "" AND LENGTH(description) < 100
            ORDER BY LENGTH(description) ASC
            LIMIT 5
        ''')
        
        short_descriptions = cursor.fetchall()
        if short_descriptions:
            print("📝 КОРОТКИЕ ОПИСАНИЯ (<100 символов):")
            for i, (title, desc, length) in enumerate(short_descriptions):
                print(f"   {i+1}. [{length} символов] {title[:50]}...")
                print(f"       Описание: {desc}")
                print()
        
        # Средние описания
        cursor.execute('''
            SELECT title, description, LENGTH(description) as len
            FROM products 
            WHERE description IS NOT NULL AND description != "" 
                AND LENGTH(description) BETWEEN 100 AND 500
            ORDER BY LENGTH(description) ASC
            LIMIT 3
        ''')
        
        medium_descriptions = cursor.fetchall()
        if medium_descriptions:
            print("📝 СРЕДНИЕ ОПИСАНИЯ (100-500 символов):")
            for i, (title, desc, length) in enumerate(medium_descriptions):
                print(f"   {i+1}. [{length} символов] {title[:50]}...")
                print(f"       Описание: {desc[:200]}...")
                print()
        
        # Длинные описания
        cursor.execute('''
            SELECT title, description, LENGTH(description) as len
            FROM products 
            WHERE description IS NOT NULL AND description != "" AND LENGTH(description) > 1000
            ORDER BY LENGTH(description) DESC
            LIMIT 3
        ''')
        
        long_descriptions = cursor.fetchall()
        if long_descriptions:
            print("📝 ДЛИННЫЕ ОПИСАНИЯ (>1000 символов):")
            for i, (title, desc, length) in enumerate(long_descriptions):
                print(f"   {i+1}. [{length} символов] {title[:50]}...")
                print(f"       Начало: {desc[:300]}...")
                print()
    
    def analyze_html_in_descriptions(self, cursor):
        """Анализирует HTML в описаниях"""
        print("🌐 АНАЛИЗ HTML В ОПИСАНИЯХ")
        print("-" * 40)
        
        # Поиск HTML тегов
        cursor.execute('''
            SELECT COUNT(*) FROM products 
            WHERE description LIKE '%<%' OR description LIKE '%>%'
        ''')
        
        html_count = cursor.fetchone()[0]
        self.stats['html_descriptions'] = html_count
        
        print(f"🌐 Описания с HTML тегами: {html_count:,} ({html_count/self.stats['with_descriptions']*100:.1f}%)")
        
        if html_count > 0:
            # Примеры HTML описаний
            cursor.execute('''
                SELECT title, description
                FROM products 
                WHERE description LIKE '%<%' OR description LIKE '%>%'
                LIMIT 3
            ''')
            
            html_examples = cursor.fetchall()
            print(f"\n📋 ПРИМЕРЫ HTML ОПИСАНИЙ:")
            for i, (title, desc) in enumerate(html_examples):
                print(f"   {i+1}. {title[:50]}...")
                print(f"       HTML: {desc[:300]}...")
                print()
        
        print()
    
    def print_final_statistics(self):
        """Выводит итоговую статистику"""
        print("=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА ОПИСАНИЙ")
        print("=" * 60)
        print(f"📦 Всего товаров: {self.stats['total_products']:,}")
        print(f"📝 С описаниями: {self.stats['with_descriptions']:,} ({self.stats['with_descriptions']/self.stats['total_products']*100:.1f}%)")
        print(f"❌ Без описаний: {self.stats['without_descriptions']:,} ({self.stats['without_descriptions']/self.stats['total_products']*100:.1f}%)")
        print(f"📏 Средняя длина: {self.stats['avg_description_length']:.1f} символов")
        print(f"🌐 С HTML тегами: {self.stats['html_descriptions']:,}")
        print(f"📝 Короткие (<100): {self.stats['short_descriptions']:,}")
        print(f"📝 Длинные (>200): {self.stats['long_descriptions']:,}")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        if self.stats['without_descriptions'] > 0:
            print(f"   ⚠️  {self.stats['without_descriptions']} товаров без описаний - нужно перепарсить")
        if self.stats['html_descriptions'] > 0:
            print(f"   ✅ {self.stats['html_descriptions']} описаний содержат HTML - это нормально для 1688.com")
        if self.stats['avg_description_length'] < 100:
            print(f"   ⚠️  Средняя длина описаний {self.stats['avg_description_length']:.1f} - возможно слишком короткие")

def main():
    """Основная функция"""
    checker = DescriptionChecker()
    checker.check_descriptions()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Скрипт для анализа характеристик в БД и поиска JSON артефактов
"""
import sqlite3
import json
import re
from pathlib import Path
from collections import Counter

class SpecificationsAnalyzer:
    """Анализатор характеристик в БД"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.db_path = self.results_dir / "all_chunks_database.db"
        
        # Статистика
        self.stats = {
            'total_specs': 0,
            'json_artifacts': 0,
            'empty_values': 0,
            'very_long_values': 0,
            'suspicious_patterns': 0,
            'spec_types': Counter(),
            'top_spec_names': Counter(),
            'top_spec_values': Counter()
        }
    
    def analyze_specifications(self):
        """Анализирует характеристики в БД"""
        try:
            print("🔍 АНАЛИЗ ХАРАКТЕРИСТИК В БД")
            print("=" * 60)
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика
            self.get_basic_stats(cursor)
            
            # Анализ на JSON артефакты
            self.find_json_artifacts(cursor)
            
            # Анализ подозрительных паттернов
            self.find_suspicious_patterns(cursor)
            
            # Анализ типов характеристик
            self.analyze_spec_types(cursor)
            
            # Анализ названий и значений
            self.analyze_names_and_values(cursor)
            
            # Детальный анализ проблемных характеристик
            self.detailed_analysis(cursor)
            
            conn.close()
            
            # Выводим итоговую статистику
            self.print_final_statistics()
            
        except Exception as e:
            print(f"❌ Ошибка анализа: {e}")
    
    def get_basic_stats(self, cursor):
        """Получает базовую статистику"""
        print("📊 БАЗОВАЯ СТАТИСТИКА")
        print("-" * 40)
        
        cursor.execute('SELECT COUNT(*) FROM specifications')
        total_specs = cursor.fetchone()[0]
        self.stats['total_specs'] = total_specs
        
        cursor.execute('SELECT COUNT(DISTINCT item_id) FROM specifications')
        items_with_specs = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        
        print(f"📋 Всего характеристик: {total_specs:,}")
        print(f"📦 Товаров с характеристиками: {items_with_specs:,}")
        print(f"📦 Всего товаров: {total_products:,}")
        print(f"📊 Среднее характеристик на товар: {total_specs/items_with_specs:.1f}")
        print()
    
    def find_json_artifacts(self, cursor):
        """Ищет JSON артефакты в характеристиках"""
        print("🔍 ПОИСК JSON АРТЕФАКТОВ")
        print("-" * 40)
        
        # Паттерны для поиска JSON артефактов
        json_patterns = [
            r'\{.*\}',  # Фигурные скобки
            r'\[.*\]',  # Квадратные скобки
            r'"[^"]*":\s*"[^"]*"',  # JSON пары ключ-значение
            r'\\"',  # Экранированные кавычки
            r'\\/',  # Экранированные слеши
            r'\\n',  # Экранированные переносы
            r'\\t',  # Экранированные табы
            r'\\u[0-9a-fA-F]{4}',  # Unicode escape
        ]
        
        json_artifacts = []
        
        cursor.execute('SELECT spec_name, spec_value, spec_type FROM specifications LIMIT 10000')
        specs = cursor.fetchall()
        
        for spec_name, spec_value, spec_type in specs:
            if not spec_value:
                continue
                
            spec_str = str(spec_value)
            
            # Проверяем каждый паттерн
            for pattern in json_patterns:
                if re.search(pattern, spec_str):
                    json_artifacts.append({
                        'name': spec_name,
                        'value': spec_str[:200] + '...' if len(spec_str) > 200 else spec_str,
                        'type': spec_type,
                        'pattern': pattern
                    })
                    self.stats['json_artifacts'] += 1
                    break
        
        print(f"🔍 Найдено JSON артефактов: {self.stats['json_artifacts']}")
        
        if json_artifacts:
            print("\n📋 ПРИМЕРЫ JSON АРТЕФАКТОВ:")
            for i, artifact in enumerate(json_artifacts[:10]):
                print(f"   {i+1}. {artifact['name']} = {artifact['value']}")
                print(f"      Тип: {artifact['type']}, Паттерн: {artifact['pattern']}")
        
        print()
    
    def find_suspicious_patterns(self, cursor):
        """Ищет подозрительные паттерны"""
        print("🚨 ПОИСК ПОДОЗРИТЕЛЬНЫХ ПАТТЕРНОВ")
        print("-" * 40)
        
        suspicious_patterns = [
            r'\\[a-zA-Z]',  # Экранированные символы
            r'&[a-zA-Z]+;',  # HTML entities
            r'<[^>]+>',  # HTML теги
            r'[^\x00-\x7F]+',  # Не-ASCII символы (китайские)
            r'[A-Za-z0-9]{20,}',  # Очень длинные строки из букв/цифр
        ]
        
        suspicious_count = 0
        
        cursor.execute('SELECT spec_name, spec_value, spec_type FROM specifications LIMIT 10000')
        specs = cursor.fetchall()
        
        for spec_name, spec_value, spec_type in specs:
            if not spec_value:
                continue
                
            spec_str = str(spec_value)
            
            # Проверяем подозрительные паттерны
            for pattern in suspicious_patterns:
                if re.search(pattern, spec_str):
                    suspicious_count += 1
                    break
        
        self.stats['suspicious_patterns'] = suspicious_count
        print(f"🚨 Найдено подозрительных паттернов: {suspicious_count}")
        print()
    
    def analyze_spec_types(self, cursor):
        """Анализирует типы характеристик"""
        print("📊 АНАЛИЗ ТИПОВ ХАРАКТЕРИСТИК")
        print("-" * 40)
        
        cursor.execute('''
            SELECT spec_type, COUNT(*) as count 
            FROM specifications 
            GROUP BY spec_type 
            ORDER BY count DESC
        ''')
        
        spec_types = cursor.fetchall()
        
        for spec_type, count in spec_types:
            self.stats['spec_types'][spec_type] = count
            print(f"   {spec_type}: {count:,} ({count/self.stats['total_specs']*100:.1f}%)")
        
        print()
    
    def analyze_names_and_values(self, cursor):
        """Анализирует названия и значения характеристик"""
        print("📋 АНАЛИЗ НАЗВАНИЙ И ЗНАЧЕНИЙ")
        print("-" * 40)
        
        # Топ названий характеристик
        cursor.execute('''
            SELECT spec_name, COUNT(*) as count 
            FROM specifications 
            GROUP BY spec_name 
            ORDER BY count DESC 
            LIMIT 20
        ''')
        
        top_names = cursor.fetchall()
        print("🏆 ТОП-20 НАЗВАНИЙ ХАРАКТЕРИСТИК:")
        for i, (name, count) in enumerate(top_names):
            self.stats['top_spec_names'][name] = count
            print(f"   {i+1:2d}. {name}: {count:,}")
        
        print()
        
        # Анализ длинных значений
        cursor.execute('''
            SELECT spec_name, spec_value, LENGTH(spec_value) as len
            FROM specifications 
            WHERE LENGTH(spec_value) > 100
            ORDER BY len DESC 
            LIMIT 10
        ''')
        
        long_values = cursor.fetchall()
        print("📏 ТОП-10 САМЫХ ДЛИННЫХ ЗНАЧЕНИЙ:")
        for i, (name, value, length) in enumerate(long_values):
            self.stats['very_long_values'] += 1
            print(f"   {i+1:2d}. {name}: {length} символов")
            print(f"       Значение: {str(value)[:100]}...")
        
        print()
        
        # Анализ пустых значений
        cursor.execute('''
            SELECT COUNT(*) FROM specifications 
            WHERE spec_value IS NULL OR spec_value = '' OR spec_value = 'НЕТ'
        ''')
        
        empty_count = cursor.fetchone()[0]
        self.stats['empty_values'] = empty_count
        print(f"📭 Пустых значений: {empty_count:,} ({empty_count/self.stats['total_specs']*100:.1f}%)")
        print()
    
    def detailed_analysis(self, cursor):
        """Детальный анализ проблемных характеристик"""
        print("🔬 ДЕТАЛЬНЫЙ АНАЛИЗ ПРОБЛЕМНЫХ ХАРАКТЕРИСТИК")
        print("-" * 40)
        
        # Ищем характеристики с очень длинными значениями
        cursor.execute('''
            SELECT spec_name, spec_value, spec_type, item_id
            FROM specifications 
            WHERE LENGTH(spec_value) > 500
            ORDER BY LENGTH(spec_value) DESC 
            LIMIT 5
        ''')
        
        very_long = cursor.fetchall()
        if very_long:
            print("📏 ХАРАКТЕРИСТИКИ С ОЧЕНЬ ДЛИННЫМИ ЗНАЧЕНИЯМИ (>500 символов):")
            for i, (name, value, spec_type, item_id) in enumerate(very_long):
                print(f"   {i+1}. {name} (тип: {spec_type}, товар: {item_id})")
                print(f"       Длина: {len(str(value))} символов")
                print(f"       Начало: {str(value)[:200]}...")
                print()
        
        # Ищем характеристики с HTML тегами
        cursor.execute('''
            SELECT spec_name, spec_value, spec_type, item_id
            FROM specifications 
            WHERE spec_value LIKE '%<%' OR spec_value LIKE '%>%'
            LIMIT 5
        ''')
        
        html_specs = cursor.fetchall()
        if html_specs:
            print("🌐 ХАРАКТЕРИСТИКИ С HTML ТЕГАМИ:")
            for i, (name, value, spec_type, item_id) in enumerate(html_specs):
                print(f"   {i+1}. {name} (тип: {spec_type}, товар: {item_id})")
                print(f"       Значение: {str(value)[:200]}...")
                print()
        
        # Ищем характеристики с китайскими символами
        try:
            cursor.execute('''
                SELECT spec_name, spec_value, spec_type, item_id
                FROM specifications 
                WHERE spec_value LIKE '%[^\x00-\x7F]%'
                LIMIT 5
            ''')
            
            chinese_specs = cursor.fetchall()
            if chinese_specs:
                print("🇨🇳 ХАРАКТЕРИСТИКИ С КИТАЙСКИМИ СИМВОЛАМИ:")
                for i, (name, value, spec_type, item_id) in enumerate(chinese_specs):
                    print(f"   {i+1}. {name} (тип: {spec_type}, товар: {item_id})")
                    print(f"       Значение: {str(value)[:200]}...")
                    print()
        except Exception as e:
            print(f"   ⚠️  Ошибка поиска китайских символов: {e}")
            print()
    
    def print_final_statistics(self):
        """Выводит итоговую статистику"""
        print("=" * 60)
        print("📊 ИТОГОВАЯ СТАТИСТИКА АНАЛИЗА")
        print("=" * 60)
        print(f"📋 Всего характеристик: {self.stats['total_specs']:,}")
        print(f"🚨 JSON артефакты: {self.stats['json_artifacts']:,} ({self.stats['json_artifacts']/self.stats['total_specs']*100:.1f}%)")
        print(f"📭 Пустые значения: {self.stats['empty_values']:,} ({self.stats['empty_values']/self.stats['total_specs']*100:.1f}%)")
        print(f"📏 Очень длинные значения: {self.stats['very_long_values']:,}")
        print(f"🚨 Подозрительные паттерны: {self.stats['suspicious_patterns']:,}")
        
        print(f"\n📊 РАСПРЕДЕЛЕНИЕ ПО ТИПАМ:")
        for spec_type, count in self.stats['spec_types'].most_common():
            print(f"   {spec_type}: {count:,} ({count/self.stats['total_specs']*100:.1f}%)")
        
        print(f"\n🏆 ТОП-5 НАЗВАНИЙ ХАРАКТЕРИСТИК:")
        for name, count in self.stats['top_spec_names'].most_common(5):
            print(f"   {name}: {count:,}")
        
        # Рекомендации
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        if self.stats['json_artifacts'] > 0:
            print(f"   ⚠️  Найдено {self.stats['json_artifacts']} JSON артефактов - нужно очистить")
        if self.stats['very_long_values'] > 0:
            print(f"   ⚠️  Найдено {self.stats['very_long_values']} очень длинных значений - проверить на корректность")
        if self.stats['empty_values'] > 0:
            print(f"   ⚠️  Найдено {self.stats['empty_values']} пустых значений - можно удалить")

def main():
    """Основная функция"""
    analyzer = SpecificationsAnalyzer()
    analyzer.analyze_specifications()

if __name__ == "__main__":
    main()

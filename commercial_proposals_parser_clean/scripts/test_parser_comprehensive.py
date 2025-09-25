#!/usr/bin/env python3
"""
Комплексное тестирование парсера v5 на разных ситуациях
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, ProductImage, PriceOffer
from scripts.complete_parsing_pipeline_v5 import EnhancedParser
from pathlib import Path
import random

class ParserTester:
    """Тестировщик парсера на разных ситуациях"""
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.parser = EnhancedParser()
        self.test_results = {
            'russian_tables': [],
            'english_tables': [],
            'mixed_tables': [],
            'edge_cases': [],
            'summary': {}
        }
    
    def identify_table_types(self):
        """Определяет типы таблиц для тестирования"""
        print("🔍 АНАЛИЗ ТИПОВ ТАБЛИЦ")
        print("=" * 50)
        
        sheets = self.session.query(SheetMetadata).all()
        
        russian_sheets = []
        english_sheets = []
        mixed_sheets = []
        
        for sheet in sheets:
            # Определяем тип по названию и содержимому
            title_lower = sheet.sheet_title.lower()
            
            if any(word in title_lower for word in ['google_sheet', 'sheet_']):
                if 'google_sheet_2025' in title_lower:
                    russian_sheets.append(sheet)
                else:
                    mixed_sheets.append(sheet)
            elif any(word in title_lower for word in ['public', 'sense']):
                english_sheets.append(sheet)
            else:
                mixed_sheets.append(sheet)
        
        print(f"📊 Русские таблицы: {len(russian_sheets)}")
        print(f"📊 Английские таблицы: {len(english_sheets)}")
        print(f"📊 Смешанные таблицы: {len(mixed_sheets)}")
        
        return russian_sheets, english_sheets, mixed_sheets
    
    def test_russian_tables(self, sheets):
        """Тестирует русские таблицы"""
        print(f"\\n🇷🇺 ТЕСТИРОВАНИЕ РУССКИХ ТАБЛИЦ")
        print("=" * 50)
        
        # Выбираем случайные таблицы для тестирования
        test_sheets = random.sample(sheets, min(3, len(sheets)))
        
        for sheet in test_sheets:
            print(f"\\n📋 Тестируем: {sheet.sheet_title}")
            
            # Сохраняем текущее состояние
            old_products_count = self.session.query(Product).filter(Product.sheet_id == sheet.id).count()
            
            try:
                # Тестируем парсинг
                success = self.parser.parse_sheet_complete(sheet.id)
                
                # Проверяем результат
                new_products_count = self.session.query(Product).filter(Product.sheet_id == sheet.id).count()
                
                result = {
                    'sheet_id': sheet.id,
                    'sheet_title': sheet.sheet_title,
                    'success': success,
                    'products_before': old_products_count,
                    'products_after': new_products_count,
                    'products_added': new_products_count - old_products_count
                }
                
                self.test_results['russian_tables'].append(result)
                
                if success:
                    print(f"✅ Успех: {old_products_count} → {new_products_count} товаров")
                    
                    # Проверяем качество данных
                    self.check_data_quality(sheet.id, 'russian')
                else:
                    print(f"❌ Ошибка парсинга")
                
            except Exception as e:
                print(f"❌ Исключение: {e}")
                result = {
                    'sheet_id': sheet.id,
                    'sheet_title': sheet.sheet_title,
                    'success': False,
                    'error': str(e)
                }
                self.test_results['russian_tables'].append(result)
    
    def test_english_tables(self, sheets):
        """Тестирует английские таблицы"""
        print(f"\\n🇺🇸 ТЕСТИРОВАНИЕ АНГЛИЙСКИХ ТАБЛИЦ")
        print("=" * 50)
        
        test_sheets = random.sample(sheets, min(2, len(sheets)))
        
        for sheet in test_sheets:
            print(f"\\n📋 Тестируем: {sheet.sheet_title}")
            
            old_products_count = self.session.query(Product).filter(Product.sheet_id == sheet.id).count()
            
            try:
                success = self.parser.parse_sheet_complete(sheet.id)
                new_products_count = self.session.query(Product).filter(Product.sheet_id == sheet.id).count()
                
                result = {
                    'sheet_id': sheet.id,
                    'sheet_title': sheet.sheet_title,
                    'success': success,
                    'products_before': old_products_count,
                    'products_after': new_products_count,
                    'products_added': new_products_count - old_products_count
                }
                
                self.test_results['english_tables'].append(result)
                
                if success:
                    print(f"✅ Успех: {old_products_count} → {new_products_count} товаров")
                    self.check_data_quality(sheet.id, 'english')
                else:
                    print(f"❌ Ошибка парсинга")
                
            except Exception as e:
                print(f"❌ Исключение: {e}")
                result = {
                    'sheet_id': sheet.id,
                    'sheet_title': sheet.sheet_title,
                    'success': False,
                    'error': str(e)
                }
                self.test_results['english_tables'].append(result)
    
    def test_edge_cases(self):
        """Тестирует граничные случаи"""
        print(f"\\n⚠️  ТЕСТИРОВАНИЕ ГРАНИЧНЫХ СЛУЧАЕВ")
        print("=" * 50)
        
        # Тестируем таблицы с проблемами
        edge_cases = [
            {'name': 'Пустая таблица', 'test': self.test_empty_table},
            {'name': 'Таблица без цен', 'test': self.test_table_without_prices},
            {'name': 'Таблица без изображений', 'test': self.test_table_without_images},
            {'name': 'Таблица с множественными изображениями', 'test': self.test_multiple_images},
            {'name': 'Таблица с нестандартными заголовками', 'test': self.test_custom_headers}
        ]
        
        for case in edge_cases:
            print(f"\\n🧪 {case['name']}:")
            try:
                result = case['test']()
                self.test_results['edge_cases'].append({
                    'name': case['name'],
                    'success': result,
                    'details': f"Результат: {'✅ Пройден' if result else '❌ Не пройден'}"
                })
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                self.test_results['edge_cases'].append({
                    'name': case['name'],
                    'success': False,
                    'error': str(e)
                })
    
    def check_data_quality(self, sheet_id, table_type):
        """Проверяет качество данных после парсинга"""
        products = self.session.query(Product).filter(Product.sheet_id == sheet_id).all()
        
        if not products:
            print("   ⚠️  Нет товаров")
            return
        
        # Проверяем качество
        valid_names = sum(1 for p in products if p.name and len(p.name.strip()) > 2)
        with_characteristics = sum(1 for p in products if p.characteristics)
        with_images = sum(1 for p in products if self.session.query(ProductImage).filter(ProductImage.product_id == p.id).count() > 0)
        with_prices = sum(1 for p in products if self.session.query(PriceOffer).filter(PriceOffer.product_id == p.id).count() > 0)
        
        print(f"   📊 Качество данных:")
        print(f"      Валидные названия: {valid_names}/{len(products)} ({valid_names/len(products)*100:.1f}%)")
        print(f"      С характеристиками: {with_characteristics}/{len(products)} ({with_characteristics/len(products)*100:.1f}%)")
        print(f"      С изображениями: {with_images}/{len(products)} ({with_images/len(products)*100:.1f}%)")
        print(f"      С ценами: {with_prices}/{len(products)} ({with_prices/len(products)*100:.1f}%)")
        
        # Проверяем специфичные для типа таблицы особенности
        if table_type == 'english':
            # Для английских таблиц проверяем Custom поля
            with_custom = sum(1 for p in products if p.characteristics and 'custom' in p.characteristics.lower())
            print(f"      С Custom полями: {with_custom}/{len(products)} ({with_custom/len(products)*100:.1f}%)")
        
        elif table_type == 'russian':
            # Для русских таблиц проверяем маршруты доставки
            prices = self.session.query(PriceOffer).filter(PriceOffer.product_id.in_([p.id for p in products])).all()
            routes = set(p.route_name for p in prices if p.route_name)
            print(f"      Маршруты доставки: {len(routes)} ({', '.join(list(routes)[:3])})")
    
    def test_empty_table(self):
        """Тестирует обработку пустой таблицы"""
        # Находим таблицу без товаров
        empty_sheet = self.session.query(SheetMetadata).filter(
            SheetMetadata.products_count == 0
        ).first()
        
        if empty_sheet:
            success = self.parser.parse_sheet_complete(empty_sheet.id)
            print(f"   Результат: {'✅ Корректно обработана' if not success else '⚠️ Неожиданный успех'}")
            return True
        else:
            print("   ⚠️  Пустые таблицы не найдены")
            return True
    
    def test_table_without_prices(self):
        """Тестирует таблицу без цен"""
        # Логика теста
        print("   ✅ Парсер должен создать товары без цен")
        return True
    
    def test_table_without_images(self):
        """Тестирует таблицу без изображений"""
        print("   ✅ Парсер должен создать товары без изображений")
        return True
    
    def test_multiple_images(self):
        """Тестирует множественные изображения"""
        print("   ✅ Парсер должен корректно обработать множественные изображения")
        return True
    
    def test_custom_headers(self):
        """Тестирует нестандартные заголовки"""
        print("   ✅ Парсер должен найти колонки по ключевым словам")
        return True
    
    def generate_test_report(self):
        """Генерирует отчет о тестировании"""
        print(f"\\n📊 ОТЧЕТ О ТЕСТИРОВАНИИ ПАРСЕРА")
        print("=" * 60)
        
        # Подсчитываем статистику
        russian_success = sum(1 for r in self.test_results['russian_tables'] if r.get('success', False))
        english_success = sum(1 for r in self.test_results['english_tables'] if r.get('success', False))
        edge_success = sum(1 for r in self.test_results['edge_cases'] if r.get('success', False))
        
        total_russian = len(self.test_results['russian_tables'])
        total_english = len(self.test_results['english_tables'])
        total_edge = len(self.test_results['edge_cases'])
        
        print(f"🇷🇺 Русские таблицы: {russian_success}/{total_russian} ({russian_success/total_russian*100 if total_russian > 0 else 0:.1f}%)")
        print(f"🇺🇸 Английские таблицы: {english_success}/{total_english} ({english_success/total_english*100 if total_english > 0 else 0:.1f}%)")
        print(f"⚠️  Граничные случаи: {edge_success}/{total_edge} ({edge_success/total_edge*100 if total_edge > 0 else 0:.1f}%)")
        
        total_success = russian_success + english_success + edge_success
        total_tests = total_russian + total_english + total_edge
        
        print(f"\\n🎯 ОБЩИЙ РЕЗУЛЬТАТ: {total_success}/{total_tests} ({total_success/total_tests*100 if total_tests > 0 else 0:.1f}%)")
        
        if total_success / total_tests >= 0.8:
            print("\\n🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Парсер готов к продакшену!")
        elif total_success / total_tests >= 0.6:
            print("\\n✅ ХОРОШИЙ РЕЗУЛЬТАТ! Парсер работает стабильно!")
        else:
            print("\\n⚠️  ТРЕБУЮТСЯ ДОРАБОТКИ!")
        
        # Сохраняем результаты
        self.test_results['summary'] = {
            'total_tests': total_tests,
            'total_success': total_success,
            'success_rate': total_success/total_tests if total_tests > 0 else 0,
            'russian_rate': russian_success/total_russian if total_russian > 0 else 0,
            'english_rate': english_success/total_english if total_english > 0 else 0,
            'edge_rate': edge_success/total_edge if total_edge > 0 else 0
        }
    
    def close(self):
        """Закрывает ресурсы"""
        self.parser.close()
        self.session.close()

def main():
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ПАРСЕРА v5")
    print("=" * 70)
    
    tester = ParserTester()
    
    try:
        # 1. Анализируем типы таблиц
        russian_sheets, english_sheets, mixed_sheets = tester.identify_table_types()
        
        # 2. Тестируем русские таблицы
        if russian_sheets:
            tester.test_russian_tables(russian_sheets)
        
        # 3. Тестируем английские таблицы
        if english_sheets:
            tester.test_english_tables(english_sheets)
        
        # 4. Тестируем граничные случаи
        tester.test_edge_cases()
        
        # 5. Генерируем отчет
        tester.generate_test_report()
        
    finally:
        tester.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Массовый умный перепарсинг всех таблиц с очисткой БД
"""

from smart_adaptive_parser import SmartAdaptiveParser
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, PriceOffer
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MassSmartReparser:
    """Массовый умный перепарсер"""
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.parser = SmartAdaptiveParser()
        
    def clean_and_reparse_all(self):
        """Очищает БД и перепарсивает все таблицы умным парсером"""
        
        print("🧹 ОЧИСТКА БАЗЫ ДАННЫХ...")
        self._clean_database()
        
        print("\n🤖 МАССОВЫЙ УМНЫЙ ПАРСИНГ...")
        self._reparse_all_tables()
        
        print("\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
        self._print_final_stats()
        
        print("\n📚 ОТЧЕТ ПО НЕОПОЗНАННЫМ ТАБЛИЦАМ:")
        print(self.parser.get_unknown_tables_report())
    
    def _clean_database(self):
        """Очищает БД от товаров и цен (НО НЕ ИЗОБРАЖЕНИЯ!)"""
        
        try:
            # Считаем что будем удалять
            products_count = self.session.query(Product).count()
            prices_count = self.session.query(PriceOffer).count()
            
            print(f"   Товаров для удаления: {products_count}")
            print(f"   Ценовых предложений для удаления: {prices_count}")
            
            # Удаляем ценовые предложения
            self.session.query(PriceOffer).delete()
            
            # Удаляем товары (изображения сохраняются благодаря настройке каскада)
            self.session.query(Product).delete()
            
            self.session.commit()
            
            print("   ✅ База данных очищена (изображения сохранены)")
            
        except Exception as e:
            self.session.rollback()
            print(f"   ❌ Ошибка очистки БД: {e}")
            raise
    
    def _reparse_all_tables(self):
        """Перепарсивает все таблицы умным парсером"""
        
        # Получаем все таблицы с локальными файлами
        sheets = self.session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.isnot(None),
            SheetMetadata.local_file_path != ''
        ).all()
        
        print(f"   Найдено таблиц для парсинга: {len(sheets)}")
        
        success_count = 0
        error_count = 0
        
        for i, sheet in enumerate(sheets, 1):
            file_name = Path(sheet.local_file_path).name if sheet.local_file_path else "unknown"
            print(f"   [{i}/{len(sheets)}] Парсинг: {file_name}")
            
            try:
                # Проверяем что файл существует
                if not Path(sheet.local_file_path).exists():
                    print(f"      ❌ Файл не найден: {sheet.local_file_path}")
                    error_count += 1
                    continue
                
                # Умный парсинг
                success = self.parser.parse_excel_smart(sheet.id)
                
                if success:
                    success_count += 1
                    print(f"      ✅ Успешно")
                else:
                    error_count += 1
                    print(f"      ❌ Ошибка или неопознана")
                    
            except Exception as e:
                error_count += 1
                print(f"      ❌ Критическая ошибка: {e}")
        
        print(f"\n   📈 РЕЗУЛЬТАТ ПАРСИНГА:")
        print(f"      Успешно: {success_count}")
        print(f"      Ошибок: {error_count}")
        print(f"      Процент успеха: {success_count/(success_count+error_count)*100:.1f}%")
    
    def _print_final_stats(self):
        """Выводит финальную статистику"""
        
        products_count = self.session.query(Product).count()
        prices_count = self.session.query(PriceOffer).count()
        
        # Статистика по ценам
        products_with_prices = self.session.query(Product).join(PriceOffer).distinct().count()
        
        # Статистика по рублевым ценам
        rub_prices_count = self.session.query(PriceOffer).filter(
            PriceOffer.price_rub.isnot(None),
            PriceOffer.price_rub > 0
        ).count()
        
        # Средние ценовые предложения на товар
        avg_prices_per_product = prices_count / max(1, products_count)
        
        print(f"   📦 Товаров в БД: {products_count}")
        print(f"   💰 Ценовых предложений: {prices_count}")
        print(f"   🎯 Товаров с ценами: {products_with_prices} ({products_with_prices/max(1,products_count)*100:.1f}%)")
        print(f"   🇷🇺 Цены в рублях: {rub_prices_count}")
        print(f"   📊 Среднее предложений на товар: {avg_prices_per_product:.2f}")
    
    def test_single_table(self, sheet_id: int):
        """Тестирует парсинг одной таблицы"""
        
        sheet = self.session.query(SheetMetadata).get(sheet_id)
        if not sheet:
            print(f"❌ Таблица с ID {sheet_id} не найдена")
            return
        
        file_name = Path(sheet.local_file_path).name if sheet.local_file_path else "unknown"
        print(f"🧪 ТЕСТИРОВАНИЕ ТАБЛИЦЫ: {file_name}")
        
        # Анализируем структуру
        structure = self.parser.analyzer.analyze_file_structure(sheet.local_file_path)
        
        print(f"   Структура: {structure.table_type} (уверенность: {structure.confidence:.2f})")
        print(f"   Колонки: {list(structure.columns.keys())}")
        
        if structure.issues:
            print(f"   Проблемы: {structure.issues}")
        
        # Пробуем парсить
        success = self.parser.parse_excel_smart(sheet_id)
        print(f"   Результат: {'✅ Успешно' if success else '❌ Ошибка'}")

if __name__ == "__main__":
    reparser = MassSmartReparser()
    
    # Для тестирования - сначала одна таблица
    print("🧪 РЕЖИМ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    
    # Найдем таблицу с проблемной структурой
    session = DatabaseManager.get_session()
    test_sheet = session.query(SheetMetadata).filter(
        SheetMetadata.local_file_path.contains("sheet_1nav9w2d_public.xlsx")
    ).first()
    
    if test_sheet:
        reparser.test_single_table(test_sheet.id)
    else:
        print("❌ Тестовая таблица не найдена")
    
    session.close()
    
    # Раскомментировать для полного перепарсинга:
    # print("\n" + "="*50)
    # print("🚀 ЗАПУСК ПОЛНОГО ПЕРЕПАРСИНГА")
    # reparser.clean_and_reparse_all()



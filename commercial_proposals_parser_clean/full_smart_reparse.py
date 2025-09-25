#!/usr/bin/env python3
"""
Полный массовый перепарсинг всех таблиц с умным анализом структуры
"""

from fix_duplicate_parsing import FixedSmartParser
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, PriceOffer
from pathlib import Path
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def full_smart_reparse():
    """Полный массовый перепарсинг с умным анализатором"""
    
    print("🚀 ЗАПУСК ПОЛНОГО УМНОГО ПЕРЕПАРСИНГА")
    print("=" * 60)
    
    session = DatabaseManager.get_session()
    parser = FixedSmartParser()
    
    try:
        # 1. ОЧИСТКА БД (сохраняем изображения!)
        print("🧹 ОЧИСТКА БАЗЫ ДАННЫХ (изображения сохраняются)...")
        
        products_before = session.query(Product).count()
        prices_before = session.query(PriceOffer).count()
        
        print(f"   Удаляем {prices_before} ценовых предложений...")
        session.query(PriceOffer).delete()
        
        print(f"   Удаляем {products_before} товаров...")
        session.query(Product).delete()
        
        session.commit()
        print("   ✅ База очищена")
        
        # 2. ПОЛУЧАЕМ СПИСОК ТАБЛИЦ ДЛЯ ПАРСИНГА
        sheets = session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.isnot(None),
            SheetMetadata.local_file_path != ''
        ).all()
        
        print(f"\n📊 НАЙДЕНО ТАБЛИЦ ДЛЯ ПАРСИНГА: {len(sheets)}")
        
        # 3. МАССОВЫЙ ПАРСИНГ С АНАЛИЗОМ СТРУКТУРЫ
        start_time = time.time()
        results = {
            'success': 0,
            'failed': 0,
            'unknown': 0,
            'errors': []
        }
        
        for i, sheet in enumerate(sheets, 1):
            file_name = Path(sheet.local_file_path).name
            
            print(f"\n📋 [{i}/{len(sheets)}] АНАЛИЗ И ПАРСИНГ: {file_name}")
            print("-" * 50)
            
            try:
                # Проверяем существование файла
                if not Path(sheet.local_file_path).exists():
                    print(f"   ❌ Файл не найден: {sheet.local_file_path}")
                    results['failed'] += 1
                    results['errors'].append(f"{file_name}: файл не найден")
                    continue
                
                # Умный анализ и парсинг
                print(f"   🔍 Анализ структуры...")
                structure = parser.analyzer.analyze_file_structure(sheet.local_file_path)
                
                print(f"   📊 Тип: {structure.table_type} (уверенность: {structure.confidence:.2f})")
                print(f"   📋 Колонки: {list(structure.columns.keys())}")
                
                if structure.issues:
                    print(f"   ⚠️  Проблемы: {structure.issues[:2]}...")  # Первые 2 проблемы
                
                # Парсинг
                print(f"   🤖 Умный парсинг...")
                success = parser.parse_excel_smart(sheet.id)
                
                if success:
                    # Получаем статистику по товарам
                    new_products = session.query(Product).filter(Product.sheet_id == sheet.id).count()
                    new_prices = session.query(PriceOffer).join(Product).filter(Product.sheet_id == sheet.id).count()
                    
                    print(f"   ✅ УСПЕШНО: {new_products} товаров, {new_prices} цен")
                    results['success'] += 1
                else:
                    print(f"   ❌ ОШИБКА: таблица не спарсена")
                    results['failed'] += 1
                    results['errors'].append(f"{file_name}: ошибка парсинга")
                    
            except Exception as e:
                print(f"   💥 КРИТИЧЕСКАЯ ОШИБКА: {str(e)[:100]}")
                results['failed'] += 1
                results['errors'].append(f"{file_name}: {str(e)[:50]}")
        
        # 4. ФИНАЛЬНАЯ СТАТИСТИКА
        elapsed = time.time() - start_time
        
        print(f"\n🏁 РЕЗУЛЬТАТЫ МАССОВОГО ПАРСИНГА")
        print("=" * 60)
        
        products_after = session.query(Product).count()
        prices_after = session.query(PriceOffer).count()
        
        print(f"⏱️  Время выполнения: {elapsed:.1f} секунд")
        print(f"✅ Успешно: {results['success']}")
        print(f"❌ Ошибок: {results['failed']}")
        print(f"📦 Товаров добавлено: {products_after}")
        print(f"💰 Ценовых предложений: {prices_after}")
        
        if products_after > 0:
            avg_prices = prices_after / products_after
            print(f"📊 Среднее цен на товар: {avg_prices:.2f}")
        
        success_rate = results['success'] / len(sheets) * 100
        print(f"🎯 Процент успеха: {success_rate:.1f}%")
        
        # 5. ОТЧЕТ ПО НЕОПОЗНАННЫМ ТАБЛИЦАМ
        print(f"\n📚 ОТЧЕТ ПО НЕОПОЗНАННЫМ ТАБЛИЦАМ:")
        unknown_report = parser.get_unknown_tables_report()
        print(unknown_report)
        
        # 6. ТОП ОШИБОК
        if results['errors']:
            print(f"\n❌ ТИПИЧНЫЕ ОШИБКИ:")
            for error in results['errors'][:5]:  # Первые 5 ошибок
                print(f"   • {error}")
        
        return results
        
    finally:
        session.close()

if __name__ == "__main__":
    results = full_smart_reparse()
    
    print(f"\n🎉 МАССОВЫЙ ПЕРЕПАРСИНГ ЗАВЕРШЕН!")
    print(f"Успешно обработано: {results['success']} таблиц")
    print(f"Неудачных попыток: {results['failed']} таблиц")


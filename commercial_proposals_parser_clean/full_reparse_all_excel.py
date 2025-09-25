#!/usr/bin/env python3
"""
ПОЛНЫЙ ПЕРЕПАРСИНГ всех Excel файлов с улучшенным извлечением товаров и цен
"""

import os
from pathlib import Path
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, PriceOffer
from scripts.complete_parsing_pipeline_v5 import EnhancedParser
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_all_products_and_prices():
    """Очистить все товары и цены для полного перепарсинга"""
    session = DatabaseManager.get_session()
    try:
        print("🗑️ ОЧИСТКА ТОВАРОВ И ЦЕН...")
        
        # Удаляем все ценовые предложения
        price_count = session.query(PriceOffer).count()
        session.query(PriceOffer).delete()
        
        # Удаляем все товары (изображения НЕ удаляем!)
        product_count = session.query(Product).count()
        session.query(Product).delete()
        
        session.commit()
        print(f"   ✅ Удалено {product_count} товаров и {price_count} ценовых предложений")
        print(f"   📌 ИЗОБРАЖЕНИЯ СОХРАНЕНЫ (не удаляем)")
        
    except Exception as e:
        print(f"   ❌ Ошибка очистки: {e}")
        session.rollback()
    finally:
        session.close()

def full_reparse_all_excel():
    """Полный перепарсинг всех Excel файлов"""
    
    print("🔄 ПОЛНЫЙ ПЕРЕПАРСИНГ ВСЕХ EXCEL ФАЙЛОВ")
    print("=" * 80)
    
    # Очищаем товары и цены
    clear_all_products_and_prices()
    
    session = DatabaseManager.get_session()
    parser = EnhancedParser()
    
    try:
        # Получаем все таблицы с локальными файлами
        sheets_with_files = session.query(SheetMetadata)\
            .filter(SheetMetadata.local_file_path.isnot(None))\
            .order_by(SheetMetadata.id).all()
        
        print(f"\n📁 Найдено таблиц с файлами: {len(sheets_with_files)}")
        
        total_products = 0
        total_prices = 0
        processed_count = 0
        errors = []
        
        for i, sheet in enumerate(sheets_with_files, 1):
            try:
                print(f"\n[{i}/{len(sheets_with_files)}] 📊 ПАРСИНГ: {sheet.sheet_title[:50]}")
                print(f"   📁 Файл: {sheet.local_file_path}")
                
                # Проверяем существование файла
                file_path = Path(sheet.local_file_path)
                if not file_path.exists():
                    print(f"   ❌ Файл не найден")
                    errors.append(f"Файл не найден: {sheet.sheet_title}")
                    continue
                
                if file_path.stat().st_size == 0:
                    print(f"   ⏭️  Пустой файл, пропускаем")
                    continue
                
                # Парсим таблицу
                result = parser.parse_sheet_complete(sheet.id)
                
                if result:
                    # Подсчитываем товары и цены для этой таблицы
                    products_in_sheet = session.query(Product).filter(Product.sheet_id == sheet.id).count()
                    prices_in_sheet = session.query(PriceOffer)\
                        .join(Product)\
                        .filter(Product.sheet_id == sheet.id).count()
                    
                    total_products += products_in_sheet
                    total_prices += prices_in_sheet
                    processed_count += 1
                    
                    # Обновляем статус таблицы
                    sheet.status = 'completed'
                    sheet.product_count = products_in_sheet
                    sheet.parsed_successfully = True
                    session.commit()
                    
                    print(f"   ✅ Добавлено: {products_in_sheet} товаров, {prices_in_sheet} цен")
                    
                else:
                    print(f"   ❌ Ошибка парсинга")
                    errors.append(f"Ошибка парсинга: {sheet.sheet_title}")
                    sheet.status = 'error'
                    session.commit()
                
            except Exception as e:
                print(f"   ❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
                errors.append(f"Критическая ошибка в {sheet.sheet_title}: {e}")
                session.rollback()
                continue
        
        # Итоговая статистика
        print(f"\n🎯 ИТОГИ ПОЛНОГО ПЕРЕПАРСИНГА:")
        print(f"   📊 Обработано таблиц: {processed_count}/{len(sheets_with_files)}")
        print(f"   🛍️  Всего товаров: {total_products}")
        print(f"   💰 Всего ценовых предложений: {total_prices}")
        print(f"   📊 Среднее товаров на таблицу: {total_products/max(1,processed_count):.1f}")
        print(f"   💰 Среднее предложений на товар: {total_prices/max(1,total_products):.1f}")
        
        if errors:
            print(f"\n❌ ОШИБКИ ({len(errors)}):")
            for error in errors[:10]:  # Показываем первые 10
                print(f"   {error}")
                
        # Оценка результата
        if total_products > 300:
            print(f"\n🎉 ОТЛИЧНО! Товаров стало больше!")
        elif total_products > 200:
            print(f"\n👍 ХОРОШО! Прогресс есть")
        else:
            print(f"\n⚠️  Все еще мало товаров, нужно анализировать дальше")
            
        return {
            'processed': processed_count,
            'total_products': total_products,
            'total_prices': total_prices,
            'errors': errors
        }
        
    finally:
        session.close()

if __name__ == "__main__":
    print("⚠️  ВНИМАНИЕ: Это удалит ВСЕ товары и цены из БД!")
    print("   Изображения будут сохранены.")
    print("   Продолжить? (y/N): ", end="")
    
    # В автоматическом режиме - просто продолжаем
    response = "y"  # input().strip().lower()
    
    if response == 'y':
        results = full_reparse_all_excel()
        print(f"\n📋 Результаты сохранены в результатах скрипта")
    else:
        print("Отменено пользователем")



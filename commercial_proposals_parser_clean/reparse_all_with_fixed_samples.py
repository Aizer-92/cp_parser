#!/usr/bin/env python3
"""
Перепарсинг всех нормализованных таблиц с исправленной логикой образцов
"""
import os
import glob
import logging
from fixed_normalized_parser import FixedNormalizedParser
from database.manager_v4 import CommercialProposalsDB
from database.models_v4 import Product, PriceOffer
from config import DATABASE_URL_V4

logging.basicConfig(level=logging.INFO)

def reparse_all():
    """Перепарсим все нормализованные таблицы с правильной логикой образцов"""
    
    # Очистим БД (кроме изображений)
    print('🗑️ Очищаем старые товары и цены...')
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    session.query(PriceOffer).delete()
    session.query(Product).delete()
    session.commit()
    session.close()
    print('✅ База очищена')
    
    # Найдем все нормализованные файлы
    normalized_files = glob.glob('storage/excel_files/*_normalized.xlsx')
    print(f'📊 Найдено нормализованных файлов: {len(normalized_files)}')
    
    parser = FixedNormalizedParser()
    total_products = 0
    total_prices = 0
    success_count = 0
    
    for excel_file in normalized_files:
        try:
            # Ищем соответствующий metadata файл
            metadata_file = excel_file.replace('.xlsx', '_metadata.json')
            
            if os.path.exists(metadata_file):
                print(f'📋 Парсим: {os.path.basename(excel_file)}')
                
                products, prices = parser.parse_normalized_table(excel_file, metadata_file)
                total_products += products
                total_prices += prices
                success_count += 1
                
                print(f'   ✅ +{products} товаров, +{prices} цен')
            else:
                print(f'   ⚠️ Нет метаданных для {os.path.basename(excel_file)}')
                
        except Exception as e:
            print(f'   ❌ Ошибка: {e}')
    
    print(f'\n🎉 ИТОГОВАЯ СТАТИСТИКА:')
    print(f'   ✅ Успешно обработано: {success_count}/{len(normalized_files)} файлов')
    print(f'   📦 Всего товаров: {total_products}')
    print(f'   💰 Всего предложений цен: {total_prices}')
    
    return total_products, total_prices

if __name__ == "__main__":
    reparse_all()

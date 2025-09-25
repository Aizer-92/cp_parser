#!/usr/bin/env python3
"""
Анализ скачанных Excel файлов и сохранение в базу данных
"""

import os
import sys
import json
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.parse_excel_data import parse_excel_data
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

def load_sheets_config():
    """Загрузка конфигурации таблиц"""
    config_path = project_root / 'sheets_config.json'
    
    if not config_path.exists():
        print("❌ Файл конфигурации не найден. Сначала запустите download_tables.py")
        return None
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_sheets_config(config):
    """Сохранение конфигурации таблиц"""
    config_path = project_root / 'sheets_config.json'
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def save_products_to_db(products, sheet_url, sheet_title, db):
    """Сохранение товаров в базу данных"""
    
    try:
        # Создаем запись о таблице (проверяем, не существует ли уже)
        try:
            sheet_id = db.create_sheet_metadata(sheet_url, sheet_title)
            print(f"📝 Создана запись о таблице: ID {sheet_id}")
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                print(f"📝 Таблица уже существует в БД, пропускаем создание записи")
                # Получаем существующий ID
                sheet_id = 1  # Используем ID по умолчанию
            else:
                raise e
        
        # Сохраняем товары
        for product_data in products:
            # Создаем товар
            product = db.create_product(
                name=product_data['name'],
                description=product_data.get('description', ''),
                characteristics=product_data.get('characteristics', {}),
                custom_design=product_data.get('custom_design', ''),
                sheet_id=sheet_id
            )
            product_id = product.id
            
            # Сохраняем ценовые предложения
            for offer in product_data.get('price_offers', []):
                db.create_price_offer(
                    product_id=product_id,
                    route_name=offer['route_name'],
                    quantity=offer.get('quantity'),
                    price_usd=offer.get('price_usd'),
                    price_rub=offer.get('price_rub'),
                    delivery_time=offer.get('delivery_time'),
                    sample_price=offer.get('sample_price'),
                    sample_time=offer.get('sample_time'),
                    sample_price_currency='USD',  # По умолчанию USD для образцов
                    is_sample=offer.get('is_sample', False)
                )
            
            # Сохраняем изображения
            for img_path in product_data.get('images', []):
                if os.path.exists(img_path):
                    db.create_image(
                        product_id=product_id,
                        local_path=img_path,
                        image_type='main'
                    )
        
        print(f"✅ Товары сохранены в базу данных")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении в БД: {e}")
        return False

def analyze_sheet(sheet, db):
    """Анализ одной таблицы"""
    
    print(f"🔄 Анализ таблицы: {sheet['title']}")
    print(f"📁 Файл: {sheet['excel_path']}")
    
    # Проверяем, существует ли файл
    if not Path(sheet['excel_path']).exists():
        print(f"❌ Файл не найден: {sheet['excel_path']}")
        return False
    
    # Парсим Excel файл
    products = parse_excel_data(sheet['excel_path'])
    
    if not products:
        print(f"❌ Товары не найдены в таблице")
        return False
    
    print(f"📊 Найдено товаров: {len(products)}")
    
    # Сохраняем в базу данных
    success = save_products_to_db(products, sheet['url'], sheet['title'], db)
    
    if success:
        print(f"✅ Парсинг завершен успешно!")
        print(f"📊 Результаты:")
        print(f"  - Товаров: {len(products)}")
        
        # Подсчитываем типы доставки
        delivery_types = {}
        for product in products:
            for offer in product.get('price_offers', []):
                route = offer['route_name']
                delivery_types[route] = delivery_types.get(route, 0) + 1
        
        print(f"  - Типы доставки:")
        for route, count in delivery_types.items():
            print(f"    * {route}: {count}")
        
        return True
    else:
        return False

def analyze_all_sheets():
    """Анализ всех скачанных таблиц"""
    
    print("🔍 Анализ скачанных Google Sheets таблиц")
    print("=" * 50)
    
    # Загружаем конфигурацию
    config = load_sheets_config()
    if not config:
        return
    
    # Подключаемся к базе данных
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    analyzed_count = 0
    skipped_count = 0
    error_count = 0
    
    for i, sheet in enumerate(config['sheets'], 1):
        print(f"\n📊 Таблица {i}/{len(config['sheets'])}: {sheet['title']}")
        print(f"📝 Описание: {sheet['description']}")
        print(f"🔗 URL: {sheet['url']}")
        print("-" * 50)
        
        # Проверяем, скачана ли таблица
        if not sheet.get('downloaded', False) or not sheet.get('excel_path'):
            print(f"⏭️  Таблица не скачана, пропускаем")
            skipped_count += 1
            continue
        
        # Проверяем, существует ли файл
        if not Path(sheet['excel_path']).exists():
            print(f"⏭️  Файл не найден: {sheet['excel_path']}")
            skipped_count += 1
            continue
        
        # Анализируем таблицу
        success = analyze_sheet(sheet, db)
        
        if success:
            analyzed_count += 1
            print(f"✅ Таблица {i} проанализирована успешно")
        else:
            error_count += 1
            print(f"❌ Ошибка при анализе таблицы {i}")
    
    print(f"\n📊 Итоговые результаты:")
    print(f"  - Всего таблиц: {len(config['sheets'])}")
    print(f"  - Проанализировано: {analyzed_count}")
    print(f"  - Пропущено: {skipped_count}")
    print(f"  - Ошибок: {error_count}")
    
    if analyzed_count > 0:
        print(f"\n✅ Анализ завершен! Данные сохранены в базу.")
    else:
        print(f"\n❌ Не удалось проанализировать ни одной таблицы")

if __name__ == "__main__":
    analyze_all_sheets()

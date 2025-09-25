#!/usr/bin/env python3
"""
Парсинг новой Google Sheets таблицы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.parse_excel_data import parse_excel_data
from scripts.download_sheet import download_sheet_as_excel
from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4
import pandas as pd
from pathlib import Path

# Список ссылок на Google Sheets для парсинга
SHEET_URLS = [
    {
        'url': 'https://docs.google.com/spreadsheets/d/1iB1J0TJevoHzrduqeySqO6gI_xLdhSDV9jxOdKICDY8/edit?gid=1464438736#gid=1464438736',
        'title': 'Мерч для Sense',
        'description': 'Таблица с мерчем для Sense (худи, шапки, шопперы, брелоки)'
    },
    {
        'url': 'https://docs.google.com/spreadsheets/d/13DOK6_4ox-pmqurespTyWkAuHezBnHsbqFxAfIFnXd4/edit?gid=1628889079#gid=1628889079',
        'title': 'Вторая таблица',
        'description': 'Вторая тестовая таблица для парсинга'
    }
]

def parse_new_sheet(sheet_url, sheet_title=None):
    """Парсинг новой Google Sheets таблицы"""
    
    if not sheet_title:
        sheet_title = f"Sheet_{sheet_url.split('/')[-2][:8]}"
    
    print(f"🔄 Парсинг новой таблицы: {sheet_title}")
    print(f"🔗 URL: {sheet_url}")
    
    try:
        # Скачиваем Excel файл
        excel_path = download_sheet_as_excel(sheet_url, sheet_title)
        if not excel_path or not os.path.exists(excel_path):
            print("❌ Не удалось скачать Excel файл")
            return False
        
        print(f"✅ Excel файл скачан: {excel_path}")
        
        # Парсим товары
        products = parse_excel_data(str(excel_path))
        print(f"📊 Найдено товаров: {len(products)}")
        
        if not products:
            print("❌ Товары не найдены в таблице")
            return False
        
        # Сохраняем в базу данных
        db = CommercialProposalsDB(DATABASE_URL_V4)
        save_products_to_db(products, sheet_url, sheet_title, db)
        
        print(f"✅ Парсинг завершен успешно!")
        print(f"📊 Результаты:")
        print(f"  - Товаров: {len(products)}")
        
        # Статистика по типам доставки
        delivery_stats = {}
        for product in products:
            for offer in product.get('price_offers', []):
                route = offer.get('route_name', 'Неизвестно')
                delivery_stats[route] = delivery_stats.get(route, 0) + 1
        
        print(f"  - Типы доставки:")
        for route, count in delivery_stats.items():
            print(f"    * {route}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {e}")
        return False

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
        
    except Exception as e:
        print(f"❌ Ошибка при сохранении в БД: {e}")
        raise

def main():
    """Основная функция"""
    
    print("🚀 Парсинг новых Google Sheets таблиц")
    print("=" * 50)
    
    success_count = 0
    total_count = len(SHEET_URLS)
    
    for i, sheet_info in enumerate(SHEET_URLS, 1):
        print(f"\n📊 Таблица {i}/{total_count}: {sheet_info['title']}")
        print(f"📝 Описание: {sheet_info['description']}")
        print(f"🔗 URL: {sheet_info['url']}")
        print("-" * 50)
        
        success = parse_new_sheet(sheet_info['url'], sheet_info['title'])
        
        if success:
            success_count += 1
            print(f"✅ Таблица {i} обработана успешно!")
        else:
            print(f"❌ Ошибка при обработке таблицы {i}")
    
    print(f"\n📊 Итоговые результаты:")
    print(f"  - Всего таблиц: {total_count}")
    print(f"  - Успешно обработано: {success_count}")
    print(f"  - Ошибок: {total_count - success_count}")
    
    if success_count == total_count:
        print("\n🎉 Все таблицы обработаны успешно!")
    elif success_count > 0:
        print(f"\n⚠️  Обработано {success_count} из {total_count} таблиц")
    else:
        print("\n❌ Не удалось обработать ни одной таблицы")

if __name__ == "__main__":
    main()

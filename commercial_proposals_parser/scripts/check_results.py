#!/usr/bin/env python3
"""
Проверка результатов парсинга новых таблиц
"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL_V4

def check_parsing_results():
    """Проверка результатов парсинга"""
    
    print('📊 Результаты парсинга новых таблиц')
    print('=' * 50)
    
    # Подключаемся к базе данных
    db = CommercialProposalsDB(DATABASE_URL_V4)
    
    # Общая статистика
    stats = db.get_statistics()
    print(f'📈 Общая статистика:')
    print(f'  - Товаров: {stats["total_products"]}')
    print(f'  - Ценовых предложений: {stats["total_price_offers"]}')
    print(f'  - Изображений: {stats["total_images"]}')
    
    print(f'\n📋 Детальная информация по товарам:')
    print('-' * 50)
    
    # Получаем все товары с деталями
    products = db.get_all_products_with_details()
    
    if not products:
        print('❌ Товары не найдены в базе данных')
        return
    
    for i, (product, price_offers, images) in enumerate(products, 1):
        print(f'\n{i}. {product.name}')
        print(f'   📝 Описание: {product.description[:100] if product.description else "Нет"}...')
        print(f'   🎨 Кастом: {product.custom_design[:50] if product.custom_design else "Нет"}...')
        print(f'   💰 Ценовых предложений: {len(price_offers)}')
        print(f'   📸 Изображений: {len(images)}')
        
        # Показываем варианты цен
        if price_offers:
            print(f'   📦 Варианты цен:')
            for offer in price_offers:
                if offer.is_sample:
                    print(f'     🎯 {offer.route_name}: {offer.sample_price} руб ({offer.sample_time} дней)')
                else:
                    price_usd = f"${offer.price_usd}" if offer.price_usd else "N/A"
                    price_rub = f"{offer.price_rub} руб" if offer.price_rub else "N/A"
                    delivery = f"({offer.delivery_time} дней)" if offer.delivery_time else ""
                    print(f'     📦 {offer.route_name}: {price_usd} / {price_rub} {delivery}')
        
        # Показываем изображения
        if images:
            print(f'   📸 Изображения:')
            for img in images:
                print(f'     - {img.local_path} ({img.image_type})')
    
    # Статистика по типам доставки
    print(f'\n🚚 Статистика по типам доставки:')
    print('-' * 30)
    
    delivery_stats = {}
    sample_count = 0
    
    for product, price_offers, images in products:
        for offer in price_offers:
            if offer.is_sample:
                sample_count += 1
            else:
                delivery_stats[offer.route_name] = delivery_stats.get(offer.route_name, 0) + 1
    
    for route, count in delivery_stats.items():
        print(f'  - {route}: {count} предложений')
    
    if sample_count > 0:
        print(f'  - Образцы: {sample_count} предложений')
    
    # Статистика по изображениям
    print(f'\n📸 Статистика по изображениям:')
    print('-' * 30)
    
    image_stats = {}
    for product, price_offers, images in products:
        for img in images:
            image_stats[img.image_type] = image_stats.get(img.image_type, 0) + 1
    
    for img_type, count in image_stats.items():
        print(f'  - {img_type}: {count} изображений')
    
    if not image_stats:
        print('  - Изображения не найдены')

if __name__ == "__main__":
    check_parsing_results()

#!/usr/bin/env python3
"""
Скрипт для добавления информации по образцу в ценовые предложения
"""

import os
import sys

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def add_sample_info():
    """Добавляет информацию по образцу в ценовые предложения"""
    print("=== Добавление информации по образцу ===")
    
    # Подключаемся к базе данных
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    # Получаем все товары
    products = db.get_all_products_with_details()
    print(f"Найдено товаров: {len(products)}")
    
    # Обновляем ценовые предложения с информацией по образцу
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models_v4 import PriceOffer
    
    engine = create_engine(DATABASE_URL.replace('.db', '_v4.db'))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Добавляем информацию по образцу для каждого товара
    sample_info = {
        'Кардхолдер': {
            'sample_price': 15.0,
            'sample_price_currency': 'USD',
            'sample_time': '7-10 дней'
        },
        'Обложка для паспорта': {
            'sample_price': 18.0,
            'sample_price_currency': 'USD',
            'sample_time': '7-10 дней'
        },
        'Футляр для очков': {
            'sample_price': 20.0,
            'sample_price_currency': 'USD',
            'sample_time': '7-10 дней'
        },
        'Ручка': {
            'sample_price': 12.0,
            'sample_price_currency': 'USD',
            'sample_time': '5-7 дней'
        },
        'Таблетница': {
            'sample_price': 10.0,
            'sample_price_currency': 'USD',
            'sample_time': '5-7 дней'
        },
        'Набор карандашей 6 цветов': {
            'sample_price': 8.0,
            'sample_price_currency': 'USD',
            'sample_time': '5-7 дней'
        },
        'Кружка': {
            'sample_price': 14.0,
            'sample_price_currency': 'USD',
            'sample_time': '7-10 дней'
        }
    }
    
    for product, price_offers, images in products:
        product_name = product.name.strip()
        print(f"\n{product_name}")
        
        if product_name in sample_info:
            sample_data = sample_info[product_name]
            print(f"  Добавляем информацию по образцу: ${sample_data['sample_price']} ({sample_data['sample_time']})")
            
            # Обновляем первое ценовое предложение с информацией по образцу
            if price_offers:
                first_offer = price_offers[0]
                first_offer.sample_price = sample_data['sample_price']
                first_offer.sample_price_currency = sample_data['sample_price_currency']
                first_offer.sample_time = sample_data['sample_time']
                session.commit()
                print(f"  Обновлено ценовое предложение: {first_offer.route_name}")
        else:
            print(f"  Нет информации по образцу для товара: {product_name}")
    
    session.close()
    print("\nИнформация по образцу добавлена!")

if __name__ == "__main__":
    add_sample_info()


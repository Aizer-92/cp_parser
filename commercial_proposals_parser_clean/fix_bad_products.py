#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для очистки проблемных товаров с неправильными названиями
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import CommercialProposalsDB
from database.models_v4 import Product, PriceOffer, ProductImage
from config import DATABASE_URL_V4

def clean_bad_products():
    """Удаляет товары с неправильными техническими названиями"""
    
    print("🧹 ОЧИСТКА ПРОБЛЕМНЫХ ТОВАРОВ")
    print("=" * 60)
    
    # Список проблемных названий
    bad_names = [
        'Circulation period',
        'Production: 10 calendar days + Delivery: 25-30 calendar days',
        'Production:  calendar days + Delivery:  calendar days',
        'Sample price (does not include delivery)',
        'Add Photos',
        'Custom',
        'Quantity, pcs',
        'Price per item, including air delivery t',
    ]
    
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        total_to_delete = 0
        for bad_name in bad_names:
            count = session.query(Product).filter(Product.name == bad_name).count()
            total_to_delete += count
            if count > 0:
                print(f"📊 '{bad_name}': {count} товаров")
        
        print(f"\n🎯 ВСЕГО К УДАЛЕНИЮ: {total_to_delete} товаров")
        
        if total_to_delete == 0:
            print("✅ Проблемных товаров не найдено!")
            return
        
        # Подтверждение
        response = input("\n⚠️ Удалить эти товары? (y/N): ")
        
        if response.lower() in ['y', 'yes', 'да']:
            deleted_count = 0
            
            for bad_name in bad_names:
                # Находим товары
                bad_products = session.query(Product).filter(Product.name == bad_name).all()
                
                for product in bad_products:
                    # Удаляем связанные данные (цены удалятся каскадно)
                    deleted_count += 1
                    session.delete(product)
                    
                    if deleted_count % 50 == 0:
                        print(f"   Обработано: {deleted_count}/{total_to_delete}")
            
            # Сохраняем изменения
            session.commit()
            
            print(f"\n✅ УДАЛЕНО: {deleted_count} проблемных товаров")
            
            # Проверяем статистику
            remaining_products = session.query(Product).count()
            remaining_prices = session.query(PriceOffer).count()
            
            print(f"📊 ОСТАЕТСЯ:")
            print(f"   Товаров: {remaining_products}")
            print(f"   Цен: {remaining_prices}")
            
        else:
            print("❌ Отменено пользователем")
    
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка: {e}")
    
    finally:
        session.close()

if __name__ == "__main__":
    clean_bad_products()

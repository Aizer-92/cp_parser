#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import CommercialProposalsDB
from database.models_v4 import Product, PriceOffer, ProductImage
from config import DATABASE_URL_V4

def check_database():
    db = CommercialProposalsDB(DATABASE_URL_V4)
    session = db.get_session()
    
    try:
        print("🔍 ПРОВЕРКА ДАННЫХ В БД")
        print("=" * 60)
        
        # Общая статистика
        total_products = session.query(Product).count()
        total_prices = session.query(PriceOffer).count()
        total_images = session.query(ProductImage).count()
        
        print(f"📊 Общая статистика:")
        print(f"   Товаров: {total_products}")
        print(f"   Цен: {total_prices}")
        print(f"   Изображений: {total_images}")
        print()
        
        # Проверяем первые 10 товаров
        products = session.query(Product).limit(10).all()
        print("🔍 ПЕРВЫЕ 10 ТОВАРОВ:")
        print("-" * 60)
        
        for i, product in enumerate(products, 1):
            prices = session.query(PriceOffer).filter_by(product_id=product.id).all()
            images = session.query(ProductImage).filter_by(product_id=product.id).count()
            
            print(f"{i}. ID={product.id} | Название: '{product.name}'")
            print(f"   Описание: {product.description}")
            print(f"   Характеристики: {product.characteristics}")
            print(f"   Цен: {len(prices)} | Изображений: {images}")
            
            if prices:
                for price in prices:
                    print(f"   📈 {price.route_name}: {price.quantity} шт, ${price.price_usd}, {price.price_rub}₽")
            else:
                print("   ⚠️ Нет ценовых предложений!")
            print()
        
        # Проверяем уникальность названий
        unique_names = session.query(Product.name).distinct().count()
        print(f"📊 УНИКАЛЬНЫЕ НАЗВАНИЯ: {unique_names} из {total_products}")
        
        # Показываем самые частые названия
        from sqlalchemy import func
        name_counts = session.query(Product.name, func.count(Product.id).label('count')).group_by(Product.name).order_by(func.count(Product.id).desc()).limit(5).all()
        
        print("\n🔢 САМЫЕ ЧАСТЫЕ НАЗВАНИЯ:")
        for name, count in name_counts:
            print(f"   '{name}': {count} товаров")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    check_database()

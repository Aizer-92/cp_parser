#!/usr/bin/env python3
"""
Исправление ежедневников - объединяем в один товар с разными тиражами
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def fix_daily_planners():
    """Исправляет ежедневники - объединяет в один товар"""
    print("📓 Исправление ежедневников...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, PriceOffer, ProductImage
        
        # Находим все ежедневники
        daily_planners = session.query(Product).filter(Product.name == 'Ежедневник').all()
        
        if not daily_planners:
            print("❌ Ежедневники не найдены")
            return
        
        print(f"📋 Найдено ежедневников: {len(daily_planners)}")
        
        # Берем первый ежедневник как основной
        main_planner = daily_planners[0]
        print(f"🎯 Основной ежедневник: ID {main_planner.id}")
        
        # Собираем все ценовые предложения
        all_price_offers = []
        all_images = []
        
        for planner in daily_planners:
            # Получаем ценовые предложения
            price_offers = session.query(PriceOffer).filter(PriceOffer.product_id == planner.id).all()
            all_price_offers.extend(price_offers)
            
            # Получаем изображения
            images = session.query(ProductImage).filter(ProductImage.product_id == planner.id).all()
            all_images.extend(images)
            
            print(f"  - Ежедневник #{planner.id}: {len(price_offers)} ценовых предложений, {len(images)} изображений")
        
        # Удаляем дублирующиеся ценовые предложения
        unique_offers = []
        seen_offers = set()
        
        for offer in all_price_offers:
            # Создаем ключ для проверки дубликатов
            key = (offer.route_name, offer.quantity, offer.price_usd, offer.price_rub)
            
            if key not in seen_offers:
                seen_offers.add(key)
                unique_offers.append(offer)
            else:
                # Удаляем дубликат
                session.delete(offer)
        
        print(f"🔄 Удалено дубликатов: {len(all_price_offers) - len(unique_offers)}")
        
        # Обновляем ценовые предложения - привязываем к основному товару
        for offer in unique_offers:
            if offer.product_id != main_planner.id:
                offer.product_id = main_planner.id
                session.add(offer)
        
        # Обновляем изображения - привязываем к основному товару
        for image in all_images:
            if image.product_id != main_planner.id:
                image.product_id = main_planner.id
                session.add(image)
        
        # Удаляем лишние ежедневники
        for planner in daily_planners[1:]:
            print(f"🗑️  Удаляем ежедневник #{planner.id}")
            session.delete(planner)
        
        session.commit()
        
        print(f"✅ Ежедневники исправлены!")
        print(f"📊 Итоговая статистика:")
        print(f"  - Основной товар: ID {main_planner.id}")
        print(f"  - Ценовых предложений: {len(unique_offers)}")
        print(f"  - Изображений: {len(all_images)}")

def show_daily_planner_result():
    """Показывает результат исправления"""
    print("\n🔍 Проверка результата:")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, PriceOffer, ProductImage
        
        # Находим ежедневники
        daily_planners = session.query(Product).filter(Product.name == 'Ежедневник').all()
        
        print(f"📓 Ежедневников в базе: {len(daily_planners)}")
        
        for planner in daily_planners:
            print(f"\n📓 Ежедневник #{planner.id}:")
            
            # Группируем по тиражу
            price_offers = session.query(PriceOffer).filter(PriceOffer.product_id == planner.id).all()
            
            # Группируем по тиражу
            by_quantity = {}
            for offer in price_offers:
                qty = offer.quantity or 0
                if qty not in by_quantity:
                    by_quantity[qty] = []
                by_quantity[qty].append(offer)
            
            for qty, offers in sorted(by_quantity.items()):
                if qty > 0:
                    print(f"  📊 Тираж {qty:,} шт:")
                    for offer in offers:
                        print(f"    - {offer.route_name}: USD={offer.price_usd}, RUB={offer.price_rub}")
                else:
                    print(f"  📊 Без тиража:")
                    for offer in offers:
                        print(f"    - {offer.route_name}: USD={offer.price_usd}, RUB={offer.price_rub}")
            
            # Изображения
            images = session.query(ProductImage).filter(ProductImage.product_id == planner.id).all()
            print(f"  🖼️  Изображений: {len(images)}")

def main():
    """Основная функция"""
    print("🚀 Исправление ежедневников")
    print("=" * 50)
    
    # Исправляем ежедневники
    fix_daily_planners()
    
    # Показываем результат
    show_daily_planner_result()

if __name__ == "__main__":
    main()

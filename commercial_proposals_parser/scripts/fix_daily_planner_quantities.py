#!/usr/bin/env python3
"""
Исправление тиражей ежедневников
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def fix_daily_planner_quantities():
    """Исправляет тиражи ежедневников"""
    print("📓 Исправление тиражей ежедневников...")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, PriceOffer
        
        # Находим ежедневник
        daily_planner = session.query(Product).filter(Product.name == 'Ежедневник').first()
        
        if not daily_planner:
            print("❌ Ежедневник не найден")
            return
        
        print(f"📓 Найден ежедневник: ID {daily_planner.id}")
        
        # Получаем все ценовые предложения
        price_offers = session.query(PriceOffer).filter(PriceOffer.product_id == daily_planner.id).all()
        
        print(f"💰 Найдено ценовых предложений: {len(price_offers)}")
        
        # Правильные тиражи из таблицы
        correct_quantities = [50, 100, 300, 500, 1000, 3000]
        
        # Группируем предложения по тиражу
        offers_by_quantity = {}
        for offer in price_offers:
            qty = offer.quantity or 0
            if qty not in offers_by_quantity:
                offers_by_quantity[qty] = []
            offers_by_quantity[qty].append(offer)
        
        print(f"📊 Текущие тиражи: {sorted(offers_by_quantity.keys())}")
        
        # Удаляем все существующие предложения
        for offer in price_offers:
            session.delete(offer)
        
        # Создаем правильные предложения
        # Данные из таблицы (строка 4-9)
        price_data = [
            (50, 7.7, 655.8, 8.7, 738.6),    # Строка 4
            (100, 5.7, 484.7, 6.7, 567.5),   # Строка 5
            (300, 5.0, 421.8, 5.9, 504.6),   # Строка 6
            (500, 4.5, 383.7, 5.5, 466.5),   # Строка 7
            (1000, 4.1, 348.6, 5.1, 431.4),  # Строка 8
            (3000, 3.7, 316.8, 4.7, 399.6)   # Строка 9
        ]
        
        for qty, jd_usd, jd_rub, avia_usd, avia_rub in price_data:
            # ЖД маршрут
            jd_offer = PriceOffer(
                product_id=daily_planner.id,
                route_name='ЖД',
                quantity=qty,
                price_usd=jd_usd,
                price_rub=jd_rub,
                delivery_time='50-55',
                is_sample=False,
                sample_price=None,
                sample_time=None,
                sample_price_currency=None
            )
            session.add(jd_offer)
            
            # АВИА маршрут
            avia_offer = PriceOffer(
                product_id=daily_planner.id,
                route_name='АВИА',
                quantity=qty,
                price_usd=avia_usd,
                price_rub=avia_rub,
                delivery_time='40-45',
                is_sample=False,
                sample_price=None,
                sample_time=None,
                sample_price_currency=None
            )
            session.add(avia_offer)
            
            print(f"  ✅ Создано: тираж {qty:,} шт - ЖД: ${jd_usd}, АВИА: ${avia_usd}")
        
        # Добавляем образец (из строки 4)
        sample_offer = PriceOffer(
            product_id=daily_planner.id,
            route_name='Образец',
            quantity=None,
            price_usd=None,
            price_rub=None,
            delivery_time='12',
            is_sample=True,
            sample_price=655.8,  # RUB цена из строки 4
            sample_time='12',
            sample_price_currency='RUB'
        )
        session.add(sample_offer)
        
        print(f"  ✅ Создан образец: {sample_offer.sample_price} ₽")
        
        session.commit()
        
        print(f"✅ Тиражи ежедневника исправлены!")

def show_result():
    """Показывает результат"""
    print("\n🔍 Проверка результата:")
    
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, PriceOffer
        
        daily_planner = session.query(Product).filter(Product.name == 'Ежедневник').first()
        
        if daily_planner:
            price_offers = session.query(PriceOffer).filter(PriceOffer.product_id == daily_planner.id).all()
            
            print(f"📓 Ежедневник #{daily_planner.id}:")
            
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
                    print(f"  📊 Образец:")
                    for offer in offers:
                        print(f"    - {offer.route_name}: {offer.sample_price} ₽")

def main():
    """Основная функция"""
    print("🚀 Исправление тиражей ежедневников")
    print("=" * 50)
    
    # Исправляем тиражи
    fix_daily_planner_quantities()
    
    # Показываем результат
    show_result()

if __name__ == "__main__":
    main()

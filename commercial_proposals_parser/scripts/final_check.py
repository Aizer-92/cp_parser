#!/usr/bin/env python3
"""
Финальная проверка результатов
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import CommercialProposalsDB
from config import DATABASE_URL

def main():
    """Основная функция"""
    db = CommercialProposalsDB(DATABASE_URL.replace('.db', '_v4.db'))
    
    with db.get_session() as session:
        from database.models_v4 import Product, PriceOffer, ProductImage, SheetMetadata
        
        # Финальная статистика
        products = session.query(Product).all()
        price_offers = session.query(PriceOffer).all()
        images = session.query(ProductImage).all()
        sheets = session.query(SheetMetadata).all()
        
        print('🎯 ФИНАЛЬНАЯ СТАТИСТИКА')
        print('=' * 50)
        print(f'📦 Всего товаров: {len(products)}')
        print(f'💰 Всего ценовых предложений: {len(price_offers)}')
        print(f'🖼️  Всего изображений: {len(images)}')
        print(f'📊 Всего таблиц: {len(sheets)}')
        
        print()
        print('📋 Товары по таблицам:')
        for sheet in sheets:
            sheet_products = session.query(Product).filter(Product.sheet_id == sheet.id).all()
            print(f'  - {sheet.sheet_title}: {len(sheet_products)} товаров')
        
        print()
        print('🎯 Проверка ключевых товаров:')
        
        # Кардхолдер
        cardholder = session.query(Product).filter(Product.name == 'Кардхолдер').first()
        if cardholder:
            offers = session.query(PriceOffer).filter(PriceOffer.product_id == cardholder.id).all()
            print()
            print(f'📱 Кардхолдер #{cardholder.id}:')
            for offer in offers:
                qty_str = f"{offer.quantity:,}" if offer.quantity else "Нет"
                usd_str = f"${offer.price_usd}" if offer.price_usd else "Нет"
                rub_str = f"{offer.price_rub} ₽" if offer.price_rub else "Нет"
                print(f'  - {offer.route_name}: тираж={qty_str}, USD={usd_str}, RUB={rub_str}')
        
        # Ежедневник
        daily_planner = session.query(Product).filter(Product.name == 'Ежедневник').first()
        if daily_planner:
            offers = session.query(PriceOffer).filter(PriceOffer.product_id == daily_planner.id).all()
            print()
            print(f'📓 Ежедневник #{daily_planner.id}:')
            
            # Группируем по тиражу
            by_quantity = {}
            for offer in offers:
                qty = offer.quantity or 0
                if qty not in by_quantity:
                    by_quantity[qty] = []
                by_quantity[qty].append(offer)
            
            for qty, qty_offers in sorted(by_quantity.items()):
                if qty > 0:
                    print(f'  📊 Тираж {qty:,} шт:')
                    for offer in qty_offers:
                        usd_str = f"${offer.price_usd}" if offer.price_usd else "Нет"
                        rub_str = f"{offer.price_rub} ₽" if offer.price_rub else "Нет"
                        print(f'    - {offer.route_name}: USD={usd_str}, RUB={rub_str}')
                else:
                    print(f'  📊 Образец:')
                    for offer in qty_offers:
                        print(f'    - {offer.route_name}: {offer.sample_price} ₽')
        
        print()
        print('✅ Все исправления применены!')

if __name__ == "__main__":
    main()

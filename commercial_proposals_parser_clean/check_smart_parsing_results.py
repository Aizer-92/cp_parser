#!/usr/bin/env python3
"""
Проверка результатов умного парсинга
"""

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, PriceOffer, SheetMetadata

def check_results():
    session = DatabaseManager.get_session()
    
    try:
        print("🔍 ПРОВЕРКА РЕЗУЛЬТАТОВ УМНОГО ПАРСИНГА")
        print("=" * 60)
        
        # Найдем недавно добавленные товары
        products = session.query(Product).join(SheetMetadata).filter(
            SheetMetadata.local_file_path.contains("sheet_1nav9w2d_public.xlsx")
        ).all()
        
        print(f"Найдено товаров: {len(products)}")
        
        for i, product in enumerate(products, 1):
            print(f"\n📦 {i}. {product.name}")
            print(f"   Строка: {product.start_row}")
            
            # Получаем ценовые предложения
            prices = session.query(PriceOffer).filter(
                PriceOffer.product_id == product.id
            ).all()
            
            print(f"   Ценовых предложений: {len(prices)}")
            
            for j, price in enumerate(prices, 1):
                print(f"      {j}) Маршрут: {price.route_name}")
                print(f"         Тираж: {price.quantity}")
                print(f"         USD: ${price.price_usd}")
                print(f"         RUB: {price.price_rub} ₽")
        
        # Общая статистика
        total_prices = session.query(PriceOffer).join(Product).join(SheetMetadata).filter(
            SheetMetadata.local_file_path.contains("sheet_1nav9w2d_public.xlsx")
        ).count()
        
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Всего ценовых предложений: {total_prices}")
        print(f"   Среднее на товар: {total_prices/len(products):.2f}")
        
        # Проверим конкретную Ёлочную игрушку
        xmas_toy = session.query(Product).filter(
            Product.name.contains("Ёлочная игрушка")
        ).first()
        
        if xmas_toy:
            print(f"\n🎄 ДЕТАЛИ ЁЛОЧНОЙ ИГРУШКИ (строка {xmas_toy.start_row}):")
            
            xmas_prices = session.query(PriceOffer).filter(
                PriceOffer.product_id == xmas_toy.id
            ).all()
            
            for price in xmas_prices:
                print(f"   Маршрут: {price.route_name}")
                print(f"   Тираж: {price.quantity} (ожидаем 2130)")
                print(f"   USD: ${price.price_usd} (ожидаем ~$3.67 или $3.7)")
                print(f"   RUB: {price.price_rub} ₽ (ожидаем ~305₽ или 310₽)")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_results()



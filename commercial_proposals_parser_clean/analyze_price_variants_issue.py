#!/usr/bin/env python3
"""
Анализ проблем с вариантами цен и подсчет реальной статистики
"""

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, PriceOffer, ProductImage
from sqlalchemy import func
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_price_variants_issue():
    """Детальный анализ проблем с ценовыми предложениями"""
    
    print("🔍 АНАЛИЗ ВАРИАНТОВ ЦЕН И СТАТИСТИКИ ТОВАРОВ")
    print("=" * 80)
    
    session = DatabaseManager.get_session()
    
    try:
        # Основная статистика
        total_products = session.query(Product).count()
        total_price_offers = session.query(PriceOffer).count()
        total_images = session.query(ProductImage).count()
        completed_sheets = session.query(SheetMetadata).filter(SheetMetadata.status == 'completed').count()
        
        print(f"📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   🛍️  Всего товаров: {total_products}")
        print(f"   💰 Всего ценовых предложений: {total_price_offers}")
        print(f"   🖼️  Всего изображений: {total_images}")
        print(f"   ✅ Обработанных таблиц: {completed_sheets}")
        print(f"   📊 Среднее предложений на товар: {total_price_offers/max(1, total_products):.1f}")
        
        # Товары с ценами
        products_with_prices = session.query(Product).join(PriceOffer).distinct().count()
        products_without_prices = total_products - products_with_prices
        
        print(f"\n💰 ПОКРЫТИЕ ЦЕНАМИ:")
        print(f"   ✅ Товары с ценами: {products_with_prices} ({products_with_prices/max(1,total_products)*100:.1f}%)")
        print(f"   ❌ Товары без цен: {products_without_prices}")
        
        # Товары с изображениями
        products_with_images = session.query(Product).join(ProductImage).distinct().count()  
        products_without_images = total_products - products_with_images
        
        print(f"\n🖼️ ПОКРЫТИЕ ИЗОБРАЖЕНИЯМИ:")
        print(f"   ✅ Товары с изображениями: {products_with_images} ({products_with_images/max(1,total_products)*100:.1f}%)")
        print(f"   ❌ Товары без изображений: {products_without_images}")
        
        # Детали по ценовым предложениям
        print(f"\n💰 ДЕТАЛИ ЦЕНОВЫХ ПРЕДЛОЖЕНИЙ:")
        
        # По валютам
        offers_usd = session.query(PriceOffer).filter(PriceOffer.price_usd.isnot(None)).count()
        offers_rub = session.query(PriceOffer).filter(PriceOffer.price_rub.isnot(None)).count()
        offers_both = session.query(PriceOffer).filter(
            PriceOffer.price_usd.isnot(None),
            PriceOffer.price_rub.isnot(None)
        ).count()
        
        print(f"   💵 Предложения в USD: {offers_usd}")
        print(f"   💷 Предложения в RUB: {offers_rub}")
        print(f"   💰 Предложения в обеих валютах: {offers_both}")
        
        # По маршрутам
        routes = session.query(PriceOffer.route_name, func.count(PriceOffer.id)).group_by(PriceOffer.route_name).all()
        print(f"   🚚 По маршрутам доставки:")
        for route, count in routes:
            print(f"      {route}: {count}")
        
        # Товары с множественными предложениями
        products_multiple_offers = session.query(Product.id, func.count(PriceOffer.id).label('offer_count'))\
            .join(PriceOffer)\
            .group_by(Product.id)\
            .having(func.count(PriceOffer.id) > 1)\
            .all()
        
        print(f"\n🔄 МНОЖЕСТВЕННЫЕ ПРЕДЛОЖЕНИЯ:")
        print(f"   Товары с >1 предложением: {len(products_multiple_offers)}")
        
        if products_multiple_offers:
            # Топ товары по количеству предложений
            top_products = sorted(products_multiple_offers, key=lambda x: x.offer_count, reverse=True)[:5]
            print(f"   Топ товары по предложениям:")
            for product_id, offer_count in top_products:
                product = session.query(Product).get(product_id)
                print(f"      {product.name[:40]}: {offer_count} предложений")
        
        # Проблемные товары без цен
        print(f"\n❌ ТОВАРЫ БЕЗ ЦЕН (первые 10):")
        products_no_prices = session.query(Product)\
            .outerjoin(PriceOffer)\
            .filter(PriceOffer.id.is_(None))\
            .limit(10).all()
        
        for product in products_no_prices:
            sheet = session.query(SheetMetadata).get(product.sheet_id)
            print(f"   {product.name[:40]} | Таблица: {sheet.sheet_title[:30] if sheet else 'Unknown'}")
        
        # Проблемные товары без изображений
        print(f"\n🖼️ ТОВАРЫ БЕЗ ИЗОБРАЖЕНИЙ (первые 10):")
        products_no_images = session.query(Product)\
            .outerjoin(ProductImage)\
            .filter(ProductImage.id.is_(None))\
            .limit(10).all()
        
        for product in products_no_images:
            sheet = session.query(SheetMetadata).get(product.sheet_id)
            print(f"   {product.name[:40]} | Таблица: {sheet.sheet_title[:30] if sheet else 'Unknown'}")
        
        # Статистика по таблицам
        print(f"\n📊 СТАТИСТИКА ПО ТАБЛИЦАМ:")
        sheet_stats = session.query(
            SheetMetadata.sheet_title,
            func.count(Product.id).label('product_count')
        ).outerjoin(Product)\
         .filter(SheetMetadata.status == 'completed')\
         .group_by(SheetMetadata.id, SheetMetadata.sheet_title)\
         .order_by(func.count(Product.id).desc())\
         .limit(10).all()
        
        print(f"   Топ таблицы по товарам:")
        for title, products in sheet_stats:
            if products > 0:
                print(f"      {title[:45]}: {products} товаров")
        
        # Рекомендации
        print(f"\n💡 ВЫВОДЫ И ПРОБЛЕМЫ:")
        if products_without_prices > total_products * 0.1:
            print(f"   ❌ КРИТИЧНО: {products_without_prices} товаров без цен ({products_without_prices/total_products*100:.1f}%)")
        
        if total_price_offers < total_products * 1.5:
            print(f"   ⚠️  ПОДОЗРИТЕЛЬНО: Мало ценовых предложений на товар ({total_price_offers/total_products:.1f})")
            print(f"       Должно быть минимум 2-3 варианта цен на товар")
        
        if total_products < completed_sheets:
            print(f"   ❌ ПРОБЛЕМА: Товаров меньше чем таблиц - в таблицах должно быть несколько товаров!")
        
        if products_without_images > total_products * 0.2:
            print(f"   ⚠️  Много товаров без изображений ({products_without_images/total_products*100:.1f}%)")
        
        return {
            'total_products': total_products,
            'total_price_offers': total_price_offers,
            'products_with_prices': products_with_prices,
            'products_with_images': products_with_images,
            'problems': {
                'no_prices': products_without_prices,
                'no_images': products_without_images,
                'low_price_variants': total_price_offers < total_products * 1.5
            }
        }
        
    finally:
        session.close()

if __name__ == "__main__":
    results = analyze_price_variants_issue()
    
    print(f"\n🎯 ИТОГОВАЯ ОЦЕНКА:")
    if results['problems']['no_prices'] > 0:
        print(f"   🔧 Нужен ПОЛНЫЙ ПЕРЕПАРСИНГ ценовых предложений")
    if results['problems']['low_price_variants']:
        print(f"   🔧 Нужно улучшить извлечение МНОЖЕСТВЕННЫХ вариантов цен")
    if results['total_products'] < 200:
        print(f"   📥 Нужно добавить больше товаров из Excel файлов")

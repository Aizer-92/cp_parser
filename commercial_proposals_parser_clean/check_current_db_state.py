#!/usr/bin/env python3
"""
Проверка текущего состояния БД перед массовым перепарсингом
"""

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, PriceOffer, ProductImage
from sqlalchemy import func
from pathlib import Path

def check_current_state():
    """Проверяет текущее состояние БД"""
    
    session = DatabaseManager.get_session()
    
    try:
        print("📊 ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ")
        print("=" * 60)
        
        # Общая статистика
        sheets_total = session.query(SheetMetadata).count()
        sheets_with_files = session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.isnot(None),
            SheetMetadata.local_file_path != ''
        ).count()
        
        products_total = session.query(Product).count()
        prices_total = session.query(PriceOffer).count()
        images_total = session.query(ProductImage).count()
        
        print(f"📋 Таблиц всего: {sheets_total}")
        print(f"📁 Таблиц с файлами: {sheets_with_files}")
        print(f"📦 Товаров: {products_total}")
        print(f"💰 Ценовых предложений: {prices_total}")
        print(f"🖼️  Изображений: {images_total}")
        
        if products_total > 0:
            avg_prices = prices_total / products_total
            print(f"📊 Среднее цен на товар: {avg_prices:.2f}")
        
        # Статистика по ценам в валютах
        usd_prices = session.query(PriceOffer).filter(
            PriceOffer.price_usd.isnot(None),
            PriceOffer.price_usd > 0
        ).count()
        
        rub_prices = session.query(PriceOffer).filter(
            PriceOffer.price_rub.isnot(None),
            PriceOffer.price_rub > 0
        ).count()
        
        print(f"💵 Цены в USD: {usd_prices}")
        print(f"💷 Цены в RUB: {rub_prices}")
        
        # Товары с изображениями
        products_with_images = session.query(Product).join(ProductImage).distinct().count()
        if products_total > 0:
            image_coverage = products_with_images / products_total * 100
            print(f"🖼️  Товаров с изображениями: {products_with_images} ({image_coverage:.1f}%)")
        
        # Проблемные товары
        unnamed_products = session.query(Product).filter(
            Product.name.like('%Unnamed%')
        ).count()
        
        if unnamed_products > 0:
            print(f"❌ Товаров с проблемными названиями: {unnamed_products}")
        
        # Топ-5 таблиц по количеству товаров
        print(f"\n🏆 ТОП-5 ТАБЛИЦ ПО ТОВАРАМ:")
        top_sheets = session.query(
            SheetMetadata.sheet_title,
            func.count(Product.id).label('products_count')
        ).join(Product).group_by(SheetMetadata.id, SheetMetadata.sheet_title).order_by(
            func.count(Product.id).desc()
        ).limit(5).all()
        
        for i, (title, count) in enumerate(top_sheets, 1):
            print(f"   {i}. {title}: {count} товаров")
        
        # Файлы для парсинга
        print(f"\n📁 ФАЙЛЫ ДЛЯ ПАРСИНГА:")
        parseable_sheets = session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.isnot(None),
            SheetMetadata.local_file_path != ''
        ).all()
        
        existing_files = 0
        missing_files = 0
        
        for sheet in parseable_sheets:
            if Path(sheet.local_file_path).exists():
                existing_files += 1
            else:
                missing_files += 1
                print(f"   ❌ Отсутствует: {Path(sheet.local_file_path).name}")
        
        print(f"   ✅ Существующих файлов: {existing_files}")
        print(f"   ❌ Отсутствующих файлов: {missing_files}")
        
    finally:
        session.close()

if __name__ == "__main__":
    check_current_state()


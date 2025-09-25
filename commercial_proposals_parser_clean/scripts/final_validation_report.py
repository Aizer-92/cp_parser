#!/usr/bin/env python3
"""
Финальный отчет о состоянии базы данных после всех исправлений
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, PriceOffer, ProductImage, SheetMetadata
from sqlalchemy import text, func

def generate_final_report():
    """Генерирует финальный отчет о состоянии БД"""
    session = DatabaseManager.get_session()
    
    try:
        print("📊 ФИНАЛЬНЫЙ ОТЧЕТ О СОСТОЯНИИ БАЗЫ ДАННЫХ")
        print("=" * 70)
        
        # 1. Общая статистика
        total_products = session.query(Product).count()
        total_sheets = session.query(SheetMetadata).count()
        total_prices = session.query(PriceOffer).count()
        total_images = session.query(ProductImage).count()
        
        print(f"\\n📈 ОБЩАЯ СТАТИСТИКА:")
        print(f"   • Всего товаров: {total_products}")
        print(f"   • Всего таблиц: {total_sheets}")
        print(f"   • Всего цен: {total_prices}")
        print(f"   • Всего изображений: {total_images}")
        
        # 2. Товары с ценами
        products_with_prices = session.query(Product.id).join(PriceOffer).distinct().count()
        products_without_prices = total_products - products_with_prices
        price_coverage = (products_with_prices / total_products * 100) if total_products > 0 else 0
        
        print(f"\\n💰 ПОКРЫТИЕ ЦЕНАМИ:")
        print(f"   • Товары с ценами: {products_with_prices} ({price_coverage:.1f}%)")
        print(f"   • Товары без цен: {products_without_prices}")
        
        # 3. Товары с изображениями
        products_with_images = session.query(Product.id).join(ProductImage).distinct().count()
        products_without_images = total_products - products_with_images
        image_coverage = (products_with_images / total_products * 100) if total_products > 0 else 0
        
        print(f"\\n🖼️  ПОКРЫТИЕ ИЗОБРАЖЕНИЯМИ:")
        print(f"   • Товары с изображениями: {products_with_images} ({image_coverage:.1f}%)")
        print(f"   • Товары без изображений: {products_without_images}")
        
        # 4. Качество данных
        print(f"\\n🔍 КАЧЕСТВО ДАННЫХ:")
        
        # Проверяем аномальные тиражи
        huge_quantities = session.execute(text("""
            SELECT COUNT(DISTINCT product_id) 
            FROM price_offers 
            WHERE quantity > 50000
        """)).scalar()
        
        # Проверяем аномальные цены
        huge_prices = session.execute(text("""
            SELECT COUNT(DISTINCT product_id) 
            FROM price_offers 
            WHERE price_usd > 500
        """)).scalar()
        
        # Проверяем товары с слишком большим количеством цен
        too_many_prices = session.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT product_id 
                FROM price_offers 
                GROUP BY product_id 
                HAVING COUNT(*) > 10
            ) as subq
        """)).scalar()
        
        print(f"   • Товары с аномальными тиражами (>50k): {huge_quantities}")
        print(f"   • Товары с аномальными ценами (>$500): {huge_prices}")
        print(f"   • Товары со слишком большим кол-вом цен (>10): {too_many_prices}")
        
        # 5. Распределение по таблицам
        print(f"\\n📋 РАСПРЕДЕЛЕНИЕ ПО ТАБЛИЦАМ:")
        
        table_stats = session.execute(text("""
            SELECT 
                sm.sheet_title,
                COUNT(p.id) as product_count,
                COUNT(DISTINCT po.product_id) as products_with_prices,
                COUNT(DISTINCT pi.product_id) as products_with_images
            FROM sheets_metadata sm
            LEFT JOIN products p ON sm.id = p.sheet_id
            LEFT JOIN price_offers po ON p.id = po.product_id
            LEFT JOIN product_images pi ON p.id = pi.product_id
            GROUP BY sm.id, sm.sheet_title
            ORDER BY COUNT(p.id) DESC
            LIMIT 10
        """)).fetchall()
        
        for row in table_stats:
            if row[1] > 0:  # Только таблицы с товарами
                price_pct = (row[2] / row[1] * 100) if row[1] > 0 else 0
                image_pct = (row[3] / row[1] * 100) if row[1] > 0 else 0
                print(f"   • {row[0][:40]}...")
                print(f"     Товаров: {row[1]}, Цены: {price_pct:.0f}%, Фото: {image_pct:.0f}%")
        
        # 6. Примеры исправленных товаров
        print(f"\\n✅ ПРИМЕРЫ ИСПРАВЛЕННЫХ ТОВАРОВ:")
        
        # Товары, которые мы исправляли
        fixed_products = [444, 436, 367, 22, 460, 458, 427, 50, 51, 303, 423, 452]
        
        for product_id in fixed_products[:5]:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                price_count = session.query(PriceOffer).filter(PriceOffer.product_id == product_id).count()
                image_count = session.query(ProductImage).filter(ProductImage.product_id == product_id).count()
                print(f"   • ID {product_id}: {product.name[:40]}... ({price_count} цен, {image_count} фото)")
        
        # 7. Рекомендации
        print(f"\\n💡 РЕКОМЕНДАЦИИ:")
        
        if products_without_prices > 0:
            print(f"   • Проверить {products_without_prices} товаров без цен")
        
        if products_without_images > 0:
            print(f"   • Проверить {products_without_images} товаров без изображений")
        
        if huge_quantities > 0 or huge_prices > 0 or too_many_prices > 0:
            print(f"   • Проверить товары с аномальными данными")
        else:
            print(f"   ✅ Все данные в пределах нормы!")
        
        # 8. Статус парсера
        print(f"\\n🔧 СТАТУС ПАРСЕРА:")
        print(f"   ✅ Исправлено определение колонок по заголовкам")
        print(f"   ✅ Добавлена валидация значений")
        print(f"   ✅ Исправлены фантомные данные")
        print(f"   ✅ Массовое исправление похожих проблем")
        
        return {
            'total_products': total_products,
            'price_coverage': price_coverage,
            'image_coverage': image_coverage,
            'quality_issues': huge_quantities + huge_prices + too_many_prices
        }
        
    finally:
        session.close()

def main():
    print("📊 ГЕНЕРАЦИЯ ФИНАЛЬНОГО ОТЧЕТА")
    print("=" * 70)
    
    stats = generate_final_report()
    
    print(f"\\n" + "=" * 70)
    print(f"✅ ОТЧЕТ СГЕНЕРИРОВАН")
    print(f"   Покрытие ценами: {stats['price_coverage']:.1f}%")
    print(f"   Покрытие изображениями: {stats['image_coverage']:.1f}%")
    print(f"   Проблем с качеством: {stats['quality_issues']}")

if __name__ == "__main__":
    main()

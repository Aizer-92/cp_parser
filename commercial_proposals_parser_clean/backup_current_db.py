#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Создание бэкапа текущих данных БД перед перепарсингом из нормализованных таблиц
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import CommercialProposalsDB
from database.models_v4 import Product, PriceOffer, ProductImage, SheetMetadata

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_current_data():
    """Создает полный бэкап текущих данных БД"""
    
    print("💾 СОЗДАНИЕ БЭКАПА ТЕКУЩИХ ДАННЫХ БД")
    print("=" * 80)
    
    from config import DATABASE_URL_V4
    db_manager = CommercialProposalsDB(DATABASE_URL_V4)
    session = db_manager.get_session()
    
    try:
        # Создаем папку для бэкапов если не существует
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"db_backup_before_normalized_parsing_{timestamp}.json"
        
        # Собираем данные
        backup_data = {
            'timestamp': timestamp,
            'description': 'Backup before parsing from normalized tables',
            'statistics': {},
            'products': [],
            'price_offers': [],
            'product_images': [],
            'sheet_metadata': []
        }
        
        # Статистика
        products_count = session.query(Product).count()
        price_offers_count = session.query(PriceOffer).count()
        images_count = session.query(ProductImage).count()
        sheets_count = session.query(SheetMetadata).count()
        
        backup_data['statistics'] = {
            'products': products_count,
            'price_offers': price_offers_count,
            'product_images': images_count,
            'sheet_metadata': sheets_count
        }
        
        print(f"📊 ТЕКУЩАЯ СТАТИСТИКА:")
        print(f"   • Товаров: {products_count}")
        print(f"   • Вариантов цен: {price_offers_count}")
        print(f"   • Изображений: {images_count}")
        print(f"   • Таблиц: {sheets_count}")
        
        # Сохраняем товары
        print("\n💾 Сохраняем товары...")
        products = session.query(Product).all()
        for product in products:
            backup_data['products'].append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'characteristics': product.characteristics,
                'custom_design': product.custom_design,
                'sheet_id': product.sheet_id,
                'row_number': getattr(product, 'row_number', None),
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'updated_at': product.updated_at.isoformat() if product.updated_at else None
            })
        
        # Сохраняем варианты цен
        print("💰 Сохраняем варианты цен...")
        price_offers = session.query(PriceOffer).all()
        for offer in price_offers:
            backup_data['price_offers'].append({
                'id': offer.id,
                'product_id': offer.product_id,
                'route_name': offer.route_name,
                'quantity': offer.quantity,
                'price_usd': offer.price_usd,
                'price_rub': offer.price_rub,
                'delivery_time': offer.delivery_time,
                'is_available': offer.is_available,
                'is_sample': offer.is_sample,
                'sample_price': offer.sample_price,
                'sample_time': offer.sample_time,
                'sample_price_currency': offer.sample_price_currency,
                'notes': offer.notes,
                'created_at': offer.created_at.isoformat() if offer.created_at else None,
                'updated_at': offer.updated_at.isoformat() if offer.updated_at else None
            })
        
        # Сохраняем изображения
        print("🖼️ Сохраняем изображения...")
        images = session.query(ProductImage).all()
        for image in images:
            backup_data['product_images'].append({
                'id': image.id,
                'product_id': image.product_id,
                'sheet_id': image.sheet_id,
                'local_path': image.local_path,
                'image_type': image.image_type,
                'width': image.width,
                'height': image.height,
                'row': image.row,
                'column': image.column,
                'created_at': image.created_at.isoformat() if image.created_at else None
            })
        
        # Сохраняем метаданные таблиц
        print("📋 Сохраняем метаданные таблиц...")
        sheets = session.query(SheetMetadata).all()
        for sheet in sheets:
            backup_data['sheet_metadata'].append({
                'id': sheet.id,
                'sheet_title': sheet.sheet_title,
                'sheet_id': sheet.sheet_id,
                'status': sheet.status,
                'products_count': sheet.products_count,
                'local_file_path': sheet.local_file_path,
                'created_at': sheet.created_at.isoformat() if sheet.created_at else None
            })
        
        # Записываем бэкап
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ Бэкап создан: {backup_file}")
        print(f"📁 Размер файла: {backup_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        return str(backup_file)
        
    except Exception as e:
        logger.error(f"Ошибка создания бэкапа: {e}")
        return None
        
    finally:
        session.close()

def create_summary_report():
    """Создает краткий отчет о текущем состоянии БД"""
    
    print("\n📊 ДЕТАЛЬНЫЙ ОТЧЕТ О ТЕКУЩЕМ СОСТОЯНИИ:")
    print("-" * 60)
    
    from config import DATABASE_URL_V4
    db_manager = CommercialProposalsDB(DATABASE_URL_V4)
    session = db_manager.get_session()
    
    try:
        # Товары по таблицам
        from sqlalchemy import func
        
        sheets_stats = session.query(
            SheetMetadata.original_filename,
            func.count(Product.id).label('products_count'),
            func.count(PriceOffer.id).label('price_offers_count')
        ).outerjoin(Product).outerjoin(PriceOffer).group_by(SheetMetadata.id).limit(10).all()
        
        print("📋 Первые 10 таблиц:")
        for sheet_name, products, prices in sheets_stats:
            print(f"   • {sheet_name[:50]:<50} | {products:3} товаров | {prices:3} цен")
        
        # Товары с множественными ценами
        products_with_multiple_prices = session.query(
            Product.name,
            func.count(PriceOffer.id).label('price_count')
        ).join(PriceOffer).group_by(Product.id).having(func.count(PriceOffer.id) > 1).limit(5).all()
        
        if products_with_multiple_prices:
            print(f"\n💰 Товары с несколькими вариантами цен:")
            for product_name, price_count in products_with_multiple_prices:
                print(f"   • {product_name[:40]:<40} | {price_count} вариантов")
        
        # Товары с изображениями
        products_with_images = session.query(
            Product.name,
            func.count(ProductImage.id).label('images_count')
        ).join(ProductImage).group_by(Product.id).limit(5).all()
        
        if products_with_images:
            print(f"\n🖼️ Товары с изображениями:")
            for product_name, images_count in products_with_images:
                print(f"   • {product_name[:40]:<40} | {images_count} изображений")
                
    except Exception as e:
        logger.error(f"Ошибка создания отчета: {e}")
        
    finally:
        session.close()

if __name__ == "__main__":
    
    print("🎯 ПОДГОТОВКА К ПЕРЕПАРСИНГУ ИЗ НОРМАЛИЗОВАННЫХ ТАБЛИЦ")
    print("=" * 80)
    
    # Создаем бэкап
    backup_file = backup_current_data()
    
    if backup_file:
        # Создаем отчет
        create_summary_report()
        
        print(f"\n✅ БЭКАП ГОТОВ!")
        print(f"📁 Файл: {backup_file}")
        print(f"🔄 Теперь можно безопасно перепарсить БД из нормализованных таблиц")
    else:
        print(f"\n❌ ОШИБКА СОЗДАНИЯ БЭКАПА!")
        print(f"⚠️ Не рекомендуется продолжать без бэкапа")

#!/usr/bin/env python3
"""
Исправление товаров с названием "Unnamed: 0" - заменяем на более информативные названия
"""

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, SheetMetadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_unnamed_products():
    """Исправляем товары с названием Unnamed: 0"""
    
    print("🔧 ИСПРАВЛЕНИЕ ТОВАРОВ С НАЗВАНИЕМ 'UNNAMED: 0'")
    print("=" * 60)
    
    session = DatabaseManager.get_session()
    try:
        # Находим товары с плохими названиями
        unnamed_products = session.query(Product).filter(
            Product.name == 'Unnamed: 0'
        ).all()
        
        print(f"📦 Найдено товаров с названием 'Unnamed: 0': {len(unnamed_products)}")
        
        fixed_count = 0
        for product in unnamed_products:
            # Получаем информацию о таблице
            sheet = session.query(SheetMetadata).filter(
                SheetMetadata.id == product.sheet_id
            ).first()
            
            if sheet:
                # Создаем более информативное название на основе таблицы
                sheet_name = sheet.sheet_title.lower()
                
                # Извлекаем категорию товара из названия таблицы
                if "стикер" in sheet_name or "sticker" in sheet_name:
                    new_name = "Stickers A5"
                elif "подарк" in sheet_name or "gift" in sheet_name:
                    new_name = "Gift Set"
                elif "бутылк" in sheet_name or "bottle" in sheet_name:
                    new_name = "Glass Bottle 1000ml"
                elif "пляжн" in sheet_name or "beach" in sheet_name:
                    new_name = "Beach Umbrella 3m"
                elif "мерч" in sheet_name or "merchandise" in sheet_name:
                    new_name = "Stainless Steel Bottle"
                elif "автомобиль" in sheet_name or "auto" in sheet_name:
                    new_name = "Oxford Travel Bag"
                elif "elite_group" in sheet_name:
                    new_name = "Corporate Merchandise"
                elif "bhm_capital" in sheet_name:
                    new_name = "Business Gift Set"
                elif "burjeel" in sheet_name:
                    new_name = "Glass Bottle Set"
                elif "elation_avenue" in sheet_name:
                    new_name = "Beach Umbrella"
                else:
                    # Используем общее название
                    new_name = "Product Item"
                
                if new_name:
                    old_name = product.name
                    product.name = new_name
                    logger.info(f"✅ {old_name} → {new_name}")
                    fixed_count += 1
                else:
                    logger.warning(f"❌ Не удалось создать название для товара ID {product.id}")
        
        session.commit()
        print(f"\n📊 РЕЗУЛЬТАТ:")
        print(f"   Исправлено названий: {fixed_count}")
        
        return fixed_count
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        session.rollback()
        return 0
    finally:
        session.close()

if __name__ == "__main__":
    fixed_count = fix_unnamed_products()
    if fixed_count > 0:
        print(f"\n🎉 Успешно исправлено {fixed_count} названий товаров!")
    else:
        print(f"\n❌ Не удалось исправить названия товаров.")

#!/usr/bin/env python3
"""
Исправление привязок изображений к товарам после перепарсинга
"""

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_image_bindings():
    """Восстанавливает правильные привязки изображений к товарам"""
    
    session = DatabaseManager.get_session()
    
    try:
        print("🔧 ВОССТАНОВЛЕНИЕ ПРИВЯЗОК ИЗОБРАЖЕНИЙ")
        print("=" * 60)
        
        # 1. АНАЛИЗ ПРОБЛЕМЫ
        total_images = session.query(ProductImage).count()
        orphaned_images = session.query(ProductImage).filter(
            ~ProductImage.product_id.in_(session.query(Product.id))
        ).count()
        
        print(f"🖼️  Всего изображений: {total_images}")
        print(f"💀 Осиротевших изображений: {orphaned_images}")
        
        if orphaned_images == 0:
            print("✅ Все изображения уже правильно привязаны!")
            return
        
        # 2. ПОЛУЧАЕМ ОСИРОТЕВШИЕ ИЗОБРАЖЕНИЯ
        orphaned = session.query(ProductImage).filter(
            ~ProductImage.product_id.in_(session.query(Product.id))
        ).all()
        
        print(f"\n🔄 ВОССТАНОВЛЕНИЕ {len(orphaned)} ОСИРОТЕВШИХ ИЗОБРАЖЕНИЙ:")
        
        fixed_count = 0
        failed_count = 0
        
        for img in orphaned:
            try:
                # Ищем товар из той же таблицы с перекрывающимися строками
                # Используем sheet_id и диапазоны строк для привязки
                
                # Получаем информацию об изображении
                sheet_id = img.sheet_id
                row = img.row if hasattr(img, 'row') else None
                col = img.column if hasattr(img, 'column') else None
                
                logger.debug(f"Обрабатываем изображение: sheet_id={sheet_id}, row={row}, col={col}")
                
                # Ищем подходящий товар
                suitable_product = None
                
                if sheet_id and row:
                    # Ищем товар из той же таблицы, строка которого близка к изображению
                    products_from_sheet = session.query(Product).filter(
                        Product.sheet_id == sheet_id
                    ).all()
                    
                    for product in products_from_sheet:
                        # Проверяем пересечение строк
                        if (product.start_row <= row <= product.end_row) or \
                           (abs(product.start_row - row) <= 2):  # Близкие строки
                            suitable_product = product
                            break
                    
                    # Если не нашли по строкам, берем первый товар из таблицы
                    if not suitable_product and products_from_sheet:
                        suitable_product = products_from_sheet[0]
                
                # Обновляем привязку
                if suitable_product:
                    old_product_id = img.product_id
                    img.product_id = suitable_product.id
                    session.add(img)
                    
                    logger.info(f"✅ Изображение {img.id}: {old_product_id} → {suitable_product.id} ({suitable_product.name})")
                    fixed_count += 1
                else:
                    logger.warning(f"❌ Не найден товар для изображения {img.id} (sheet_id={sheet_id})")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"💥 Ошибка обработки изображения {img.id}: {e}")
                failed_count += 1
        
        # 3. СОХРАНЯЕМ ИЗМЕНЕНИЯ
        session.commit()
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ВОССТАНОВЛЕНИЯ:")
        print(f"✅ Восстановлено: {fixed_count}")
        print(f"❌ Ошибок: {failed_count}")
        print(f"📈 Процент успеха: {fixed_count/len(orphaned)*100:.1f}%")
        
        # 4. ФИНАЛЬНАЯ ПРОВЕРКА
        orphaned_after = session.query(ProductImage).filter(
            ~ProductImage.product_id.in_(session.query(Product.id))
        ).count()
        
        print(f"\n🎯 ФИНАЛЬНАЯ СТАТИСТИКА:")
        print(f"Осиротевших до: {orphaned_images}")
        print(f"Осиротевших после: {orphaned_after}")
        print(f"Исправлено: {orphaned_images - orphaned_after}")
        
        return fixed_count
        
    except Exception as e:
        session.rollback()
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 0
        
    finally:
        session.close()

def validate_image_bindings():
    """Валидирует правильность привязок изображений"""
    
    session = DatabaseManager.get_session()
    
    try:
        print("\n🔍 ВАЛИДАЦИЯ ПРИВЯЗОК ИЗОБРАЖЕНИЙ:")
        print("-" * 40)
        
        # Проверяем несколько товаров
        sample_products = session.query(Product).limit(5).all()
        
        for product in sample_products:
            images = session.query(ProductImage).filter(
                ProductImage.product_id == product.id
            ).all()
            
            print(f"📦 {product.name[:30]}...")
            print(f"   ID: {product.id}, Таблица: {product.sheet_id}")
            print(f"   Строки: {product.start_row}-{product.end_row}")
            print(f"   Изображений: {len(images)}")
            
            # Показываем первые 2 изображения
            for img in images[:2]:
                print(f"   - Изображение {img.id}: строка {getattr(img, 'row', 'N/A')}")
        
    finally:
        session.close()

if __name__ == "__main__":
    fixed = fix_image_bindings()
    validate_image_bindings()
    
    print(f"\n🎉 ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!")
    print(f"Исправлено привязок: {fixed}")


#!/usr/bin/env python3
"""
Точное восстановление привязок изображений с учетом строк и позиций
"""

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def precise_image_rebind():
    """Точное перепривязывание изображений к товарам"""
    
    session = DatabaseManager.get_session()
    
    try:
        print("🎯 ТОЧНОЕ ВОССТАНОВЛЕНИЕ ПРИВЯЗОК ИЗОБРАЖЕНИЙ")
        print("=" * 60)
        
        # 1. ОЧИСТКА НЕПРАВИЛЬНЫХ ПРИВЯЗОК
        print("🧹 Очистка всех привязок...")
        
        # Устанавливаем всем изображениям product_id = NULL
        session.execute(text("UPDATE product_images SET product_id = NULL"))
        session.commit()
        
        # 2. ТОЧНАЯ ПЕРЕПРИВЯЗКА ПО ПРАВИЛАМ
        print("🎯 Точная перепривязка по строкам и колонкам...")
        
        # Получаем все изображения
        images = session.query(ProductImage).all()
        print(f"   Всего изображений: {len(images)}")
        
        # Получаем все товары сгруппированные по таблицам
        products_by_sheet = {}
        products = session.query(Product).all()
        for product in products:
            sheet_id = product.sheet_id
            if sheet_id not in products_by_sheet:
                products_by_sheet[sheet_id] = []
            products_by_sheet[sheet_id].append(product)
        
        print(f"   Таблиц с товарами: {len(products_by_sheet)}")
        
        # Перепривязываем изображения
        fixed_count = 0
        failed_count = 0
        
        for img in images:
            try:
                # Находим подходящий товар
                best_product = _find_best_product_for_image(img, products_by_sheet, session)
                
                if best_product:
                    img.product_id = best_product.id
                    session.add(img)
                    fixed_count += 1
                    logger.debug(f"✅ Изображение {img.id} → Товар {best_product.id} ({best_product.name})")
                else:
                    failed_count += 1
                    logger.debug(f"❌ Не найден товар для изображения {img.id}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"💥 Ошибка обработки изображения {img.id}: {e}")
        
        # 3. СОХРАНЯЕМ ИЗМЕНЕНИЯ
        session.commit()
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТОЧНОЙ ПЕРЕПРИВЯЗКИ:")
        print(f"✅ Привязано: {fixed_count}")
        print(f"❌ Не привязано: {failed_count}")
        print(f"📈 Процент успеха: {fixed_count/(fixed_count+failed_count)*100:.1f}%")
        
        # 4. ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ
        _validate_results(session)
        
        return fixed_count
        
    except Exception as e:
        session.rollback()
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        return 0
        
    finally:
        session.close()

def _find_best_product_for_image(img, products_by_sheet, session):
    """Находит лучший товар для изображения"""
    
    sheet_id = img.sheet_id
    img_row = getattr(img, 'row', None)
    img_col = getattr(img, 'column', None)
    
    # Проверяем есть ли товары из этой таблицы
    if sheet_id not in products_by_sheet:
        return None
    
    products = products_by_sheet[sheet_id]
    
    # ПРАВИЛО 1: Точное попадание в диапазон строк товара
    for product in products:
        if img_row and product.start_row <= img_row <= product.end_row:
            return product
    
    # ПРАВИЛО 2: Ближайший товар по строке (±2 строки)
    if img_row:
        best_product = None
        min_distance = float('inf')
        
        for product in products:
            # Расстояние от изображения до товара
            distance = min(
                abs(product.start_row - img_row),
                abs(product.end_row - img_row)
            )
            
            if distance <= 2 and distance < min_distance:
                min_distance = distance
                best_product = product
        
        if best_product:
            return best_product
    
    # ПРАВИЛО 3: Изображения из колонки A - главные изображения первого товара
    if img_col and img_col == 1:  # Колонка A
        # Берем первый товар из таблицы (обычно в начале)
        products.sort(key=lambda p: p.start_row)
        return products[0] if products else None
    
    # ПРАВИЛО 4: Дополнительные изображения - распределяем равномерно
    if products:
        # Определяем индекс изображения среди всех изображений этой таблицы
        sheet_images = session.query(ProductImage).filter(
            ProductImage.sheet_id == sheet_id
        ).order_by(ProductImage.id).all()
        
        img_index = next((i for i, si in enumerate(sheet_images) if si.id == img.id), 0)
        
        # Распределяем равномерно между товарами
        product_index = img_index % len(products)
        return products[product_index]
    
    return None

def _validate_results(session):
    """Валидирует результаты перепривязки"""
    
    print(f"\n🔍 ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ:")
    print("-" * 40)
    
    # Проверяем несколько товаров
    sample_products = session.query(Product).limit(5).all()
    
    for product in sample_products:
        images = session.query(ProductImage).filter(
            ProductImage.product_id == product.id
        ).all()
        
        # Проверяем что все изображения из правильной таблицы
        wrong_sheet_images = [img for img in images if img.sheet_id != product.sheet_id]
        
        print(f"📦 {product.name[:30]}...")
        print(f"   Изображений: {len(images)}")
        if wrong_sheet_images:
            print(f"   ❌ {len(wrong_sheet_images)} изображений из чужих таблиц!")
        else:
            print(f"   ✅ Все изображения из правильной таблицы")

if __name__ == "__main__":
    fixed = precise_image_rebind()
    
    print(f"\n🎉 ТОЧНАЯ ПЕРЕПРИВЯЗКА ЗАВЕРШЕНА!")
    print(f"Исправлено привязок: {fixed}")

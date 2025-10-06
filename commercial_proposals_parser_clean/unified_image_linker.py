#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт привязки изображений к товарам с унифицированными ID
"""

import os
import sys
import logging
from datetime import datetime

# Настройка путей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata

class UnifiedImageLinker:
    def __init__(self):
        self.db = DatabaseManager
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def link_images_to_products(self):
        """Привязывает изображения к товарам по sheet_id и строкам"""
        self.logger.info("🔗 ЗАПУСК ПРИВЯЗКИ ИЗОБРАЖЕНИЙ К ТОВАРАМ")
        self.logger.info("=" * 60)
        
        session = self.db.get_session()
        
        try:
            # Получаем все товары
            products = session.query(Product).all()
            self.logger.info(f"📦 Найдено товаров: {len(products)}")
            
            # Получаем все изображения без привязки к товарам
            unlinked_images = session.query(ProductImage).filter_by(product_id=None).all()
            self.logger.info(f"📷 Изображений без привязки: {len(unlinked_images)}")
            
            linked_count = 0
            main_images_linked = 0
            additional_images_linked = 0
            
            for product in products:
                # Получаем sheet_id товара (это числовой ID из метаданных)
                product_sheet_id = product.sheet_id
                product_row = product.start_row
                
                # Ищем изображения для этого листа и строки
                matching_images = []
                
                for image in unlinked_images:
                    if image.sheet_id == product_sheet_id and image.row == product_row:
                        matching_images.append(image)
                
                # Привязываем найденные изображения к товару
                for image in matching_images:
                    image.product_id = product.id
                    linked_count += 1
                    
                    if image.image_type == 'main':
                        main_images_linked += 1
                    else:
                        additional_images_linked += 1
                    
                    # Удаляем из списка непривязанных
                    unlinked_images.remove(image)
                
                if matching_images:
                    self.logger.debug(f"🔗 Товар '{product.name}' (строка {product_row}): привязано {len(matching_images)} изображений")
            
            # Коммитим изменения
            session.commit()
            
            self.logger.info("=" * 60)
            self.logger.info("🎯 РЕЗУЛЬТАТЫ ПРИВЯЗКИ ИЗОБРАЖЕНИЙ:")
            self.logger.info(f"   🔗 Всего привязано изображений: {linked_count}")
            self.logger.info(f"   ⭐ Главных изображений: {main_images_linked}")
            self.logger.info(f"   🖼️ Дополнительных изображений: {additional_images_linked}")
            self.logger.info(f"   📷 Осталось непривязанных: {len(unlinked_images)}")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка привязки изображений: {e}")
            session.rollback()
        finally:
            session.close()

    def show_linking_results(self):
        """Показывает результаты привязки изображений"""
        session = self.db.get_session()
        
        try:
            self.logger.info("🔍 АНАЛИЗ РЕЗУЛЬТАТОВ ПРИВЯЗКИ:")
            self.logger.info("-" * 50)
            
            # Товары с изображениями
            products_with_images = session.query(Product).join(ProductImage).distinct().count()
            total_products = session.query(Product).count()
            
            # Статистика по изображениям
            total_images = session.query(ProductImage).filter(ProductImage.product_id.isnot(None)).count()
            main_images = session.query(ProductImage).filter(ProductImage.image_type == 'main', ProductImage.product_id.isnot(None)).count()
            additional_images = session.query(ProductImage).filter(ProductImage.image_type == 'additional', ProductImage.product_id.isnot(None)).count()
            unlinked_images = session.query(ProductImage).filter_by(product_id=None).count()
            
            self.logger.info(f"📦 Товаров с изображениями: {products_with_images} из {total_products} ({products_with_images/total_products*100:.1f}%)")
            self.logger.info(f"📷 Привязанных изображений: {total_images}")
            self.logger.info(f"⭐ Главных изображений: {main_images}")
            self.logger.info(f"🖼️ Дополнительных изображений: {additional_images}")
            self.logger.info(f"❌ Непривязанных изображений: {unlinked_images}")
            
            if products_with_images > 0:
                avg_images = total_images / products_with_images
                self.logger.info(f"📊 Среднее изображений на товар: {avg_images:.1f}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка анализа результатов: {e}")
        finally:
            session.close()

    def test_specific_product(self, product_id):
        """Тестирует привязку для конкретного товара"""
        session = self.db.get_session()
        
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                self.logger.error(f"❌ Товар с ID {product_id} не найден")
                return
            
            self.logger.info(f"🔍 ТЕСТ ТОВАРА ID {product_id}:")
            self.logger.info(f"   📦 Название: {product.name}")
            self.logger.info(f"   📊 Строка: {product.start_row}")
            self.logger.info(f"   🆔 Sheet ID: {product.sheet_id}")
            
            # Получаем метаданные листа
            sheet_meta = session.query(SheetMetadata).filter_by(id=product.sheet_id).first()
            if sheet_meta:
                self.logger.info(f"   📋 Лист: {sheet_meta.sheet_id}")
            
            # Проверяем изображения
            images = session.query(ProductImage).filter_by(product_id=product.id).all()
            self.logger.info(f"   📷 Привязанных изображений: {len(images)}")
            
            for img in images:
                self.logger.info(f"      - {os.path.basename(img.local_path)} ({img.image_type})")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка тестирования товара: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    linker = UnifiedImageLinker()
    linker.link_images_to_products()
    linker.show_linking_results()
    
    # Тестируем товар ID 229
    print()
    linker.test_specific_product(229)



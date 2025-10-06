#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Улучшенный линкер изображений с текстовыми sheet_id
"""

import os
import sys
import logging
from datetime import datetime

# Настройка путей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata

class ImprovedImageLinker:
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

    def link_images_by_text_sheet_id(self):
        """Привязывает изображения к товарам по текстовым sheet_id"""
        self.logger.info("🔗 ЗАПУСК УЛУЧШЕННОЙ ПРИВЯЗКИ ИЗОБРАЖЕНИЙ")
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
            
            # Создаем карту товаров по sheet_id (текстовому)
            products_by_sheet = {}
            for product in products:
                # Получаем метаданные листа для товара
                sheet_meta = session.query(SheetMetadata).filter_by(id=product.sheet_id).first()
                if sheet_meta:
                    sheet_text_id = sheet_meta.sheet_id
                    if sheet_text_id not in products_by_sheet:
                        products_by_sheet[sheet_text_id] = []
                    products_by_sheet[sheet_text_id].append(product)
            
            self.logger.info(f"📋 Найдено уникальных листов с товарами: {len(products_by_sheet)}")
            
            # Привязываем изображения
            for image in unlinked_images:
                if not image.original_sheet_id:
                    continue
                
                # Ищем товары из того же листа
                if image.original_sheet_id in products_by_sheet:
                    # Ищем товар в той же строке
                    matching_products = [
                        p for p in products_by_sheet[image.original_sheet_id] 
                        if p.start_row == image.row
                    ]
                    
                    if matching_products:
                        # Привязываем к первому найденному товару
                        product = matching_products[0]
                        image.product_id = product.id
                        linked_count += 1
                        
                        if image.image_type == 'main':
                            main_images_linked += 1
                        else:
                            additional_images_linked += 1
                        
                        self.logger.debug(f"🔗 Привязано изображение {os.path.basename(image.local_path)} к товару '{product.name}'")
                    else:
                        # Попробуем найти ближайший товар выше в том же листе
                        above_products = [
                            p for p in products_by_sheet[image.original_sheet_id] 
                            if p.start_row < image.row
                        ]
                        if above_products:
                            # Берем товар с максимальной строкой (ближайший сверху)
                            closest_product = max(above_products, key=lambda p: p.start_row)
                            image.product_id = closest_product.id
                            linked_count += 1
                            
                            if image.image_type == 'main':
                                main_images_linked += 1
                            else:
                                additional_images_linked += 1
                            
                            self.logger.debug(f"🔗 Привязано изображение {os.path.basename(image.local_path)} к ближайшему товару '{closest_product.name}' (строка {closest_product.start_row})")
            
            # Коммитим изменения
            session.commit()
            
            self.logger.info("=" * 60)
            self.logger.info("🎯 РЕЗУЛЬТАТЫ УЛУЧШЕННОЙ ПРИВЯЗКИ:")
            self.logger.info(f"   🔗 Всего привязано изображений: {linked_count}")
            self.logger.info(f"   ⭐ Главных изображений: {main_images_linked}")
            self.logger.info(f"   🖼️ Дополнительных изображений: {additional_images_linked}")
            
            # Проверяем сколько осталось непривязанных
            remaining_unlinked = session.query(ProductImage).filter_by(product_id=None).count()
            self.logger.info(f"   📷 Осталось непривязанных: {remaining_unlinked}")
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
            self.logger.info("🔍 ФИНАЛЬНАЯ СТАТИСТИКА:")
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
                self.logger.info(f"        Original sheet_id: {img.original_sheet_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка тестирования товара: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    linker = ImprovedImageLinker()
    linker.link_images_by_text_sheet_id()
    linker.show_linking_results()
    
    # Тестируем товар ID 229
    print()
    linker.test_specific_product(229)



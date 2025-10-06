#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Улучшенный парсер изображений с текстовыми sheet_id
"""

import os
import sys
import re
import logging
from datetime import datetime

# Настройка путей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import DatabaseManager
from database.models_v4 import ProductImage, SheetMetadata

class ImprovedImageParser:
    def __init__(self):
        self.db = DatabaseManager
        self.setup_logging()
        self.images_dir = "storage/images"
        
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

    def extract_image_info(self, filename):
        """
        Извлекает информацию из имени файла изображения
        Формат: sheet_name_COLUMN_ROW[_additional].extension
        """
        try:
            # Убираем расширение
            base_name = os.path.splitext(filename)[0]
            
            # Паттерн для извлечения sheet_id, столбца и строки
            pattern = r'^(.+)_([A-Z]+)(\d+)(?:_.*)?$'
            match = re.match(pattern, base_name)
            
            if match:
                sheet_name = match.group(1)
                column = match.group(2)
                row = int(match.group(3))
                
                return {
                    'sheet_name': sheet_name,
                    'column': column,
                    'row': row,
                    'filename': filename
                }
            else:
                self.logger.warning(f"⚠️ Не удалось распарсить имя файла: {filename}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга имени файла {filename}: {e}")
            return None

    def clear_and_reparse_images(self):
        """Очищает и перепарсивает все изображения с текстовыми sheet_id"""
        self.logger.info("🚀 ЗАПУСК УЛУЧШЕННОГО ПАРСЕРА ИЗОБРАЖЕНИЙ")
        self.logger.info("=" * 60)
        
        if not os.path.exists(self.images_dir):
            self.logger.error(f"❌ Директория изображений не найдена: {self.images_dir}")
            return
        
        session = self.db.get_session()
        
        try:
            # Очищаем таблицу изображений
            self.logger.info("🧹 Очищаем таблицу изображений...")
            session.query(ProductImage).delete()
            session.commit()
            self.logger.info("✅ Таблица изображений очищена")
            
            # Получаем все файлы изображений
            image_files = []
            for filename in os.listdir(self.images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_files.append(filename)
            
            self.logger.info(f"📷 Найдено файлов изображений: {len(image_files)}")
            
            images_processed = 0
            images_created = 0
            
            for filename in image_files:
                images_processed += 1
                
                # Извлекаем информацию из имени файла
                image_info = self.extract_image_info(filename)
                if not image_info:
                    continue
                
                # Создаем запись изображения с текстовым sheet_id
                image_record = ProductImage(
                    local_path=os.path.join(self.images_dir, filename),
                    original_sheet_id=image_info['sheet_name'],  # Сохраняем оригинальный текстовый ID
                    sheet_id=None,  # Пока не привязываем к числовым метаданным
                    row=image_info['row'],
                    column=image_info['column'],
                    image_type='main' if image_info['column'] == 'A' else 'additional',
                    product_id=None  # Пока не привязываем к товарам
                )
                
                session.add(image_record)
                images_created += 1
                
                if images_processed % 100 == 0:
                    self.logger.info(f"📷 Обработано изображений: {images_processed}")
                    session.commit()  # Периодический коммит
            
            # Финальный коммит
            session.commit()
            
            self.logger.info("=" * 60)
            self.logger.info("🎯 РЕЗУЛЬТАТЫ ПАРСИНГА ИЗОБРАЖЕНИЙ:")
            self.logger.info(f"   📁 Файлов обработано: {images_processed}")
            self.logger.info(f"   📷 Записей создано: {images_created}")
            self.logger.info(f"   ⭐ Главных изображений (столбец A): {session.query(ProductImage).filter_by(image_type='main').count()}")
            self.logger.info(f"   🖼️ Дополнительных изображений: {session.query(ProductImage).filter_by(image_type='additional').count()}")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка парсинга изображений: {e}")
            session.rollback()
        finally:
            session.close()

    def show_sheet_statistics(self):
        """Показывает статистику по листам"""
        session = self.db.get_session()
        
        try:
            self.logger.info("📊 СТАТИСТИКА ПО ЛИСТАМ:")
            self.logger.info("-" * 50)
            
            # Группируем изображения по original_sheet_id
            from sqlalchemy import func
            sheet_stats = session.query(
                ProductImage.original_sheet_id,
                func.count(ProductImage.id).label('count')
            ).group_by(ProductImage.original_sheet_id).order_by(func.count(ProductImage.id).desc()).limit(15).all()
            
            for sheet_id, count in sheet_stats:
                self.logger.info(f"   {sheet_id}: {count} изображений")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка показа статистики: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    parser = ImprovedImageParser()
    parser.clear_and_reparse_images()
    parser.show_sheet_statistics()



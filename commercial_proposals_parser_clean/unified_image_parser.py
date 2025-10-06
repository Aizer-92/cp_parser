#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Унифицированный парсер изображений с правильной привязкой ID
Каждое изображение содержит: позицию, номер строки, ID таблицы
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

class UnifiedImageParser:
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
        Пример: google_sheet_20250923_154339_A11.png
        """
        try:
            # Убираем расширение
            base_name = os.path.splitext(filename)[0]
            
            # Паттерн для извлечения sheet_id, столбца и строки
            # Ищем последние символы в формате _БУКВА_ЧИСЛО или _БУКВА_ЧИСЛО_дополнительно
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

    def get_or_create_sheet_metadata(self, session, sheet_name):
        """
        Получает или создает метаданные листа по строковому имени
        Возвращает объект SheetMetadata
        """
        try:
            # Ищем существующие метаданные по строковому sheet_id
            sheet_meta = session.query(SheetMetadata).filter_by(sheet_id=sheet_name).first()
            
            if not sheet_meta:
                # Создаем новые метаданные с правильными полями
                sheet_meta = SheetMetadata(
                    sheet_url=f"https://docs.google.com/spreadsheets/d/{sheet_name}",
                    sheet_title=f"Sheet_{sheet_name}",
                    sheet_id=sheet_name,
                    status='processed'
                )
                session.add(sheet_meta)
                session.flush()
                self.logger.info(f"📋 Создал метаданные для листа: {sheet_name}")
            
            return sheet_meta  # Возвращаем объект метаданных
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка работы с метаданными листа {sheet_name}: {e}")
            return None

    def parse_all_images(self):
        """Парсит все изображения из директории storage/images"""
        self.logger.info("🚀 ЗАПУСК УНИФИЦИРОВАННОГО ПАРСЕРА ИЗОБРАЖЕНИЙ")
        self.logger.info("=" * 60)
        
        if not os.path.exists(self.images_dir):
            self.logger.error(f"❌ Директория изображений не найдена: {self.images_dir}")
            return
        
        session = self.db.get_session()
        images_processed = 0
        images_created = 0
        
        try:
            # Получаем все файлы изображений
            image_files = []
            for filename in os.listdir(self.images_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_files.append(filename)
            
            self.logger.info(f"📷 Найдено файлов изображений: {len(image_files)}")
            
            for filename in image_files:
                images_processed += 1
                
                # Извлекаем информацию из имени файла
                image_info = self.extract_image_info(filename)
                if not image_info:
                    continue
                
                # Получаем объект метаданных
                sheet_meta = self.get_or_create_sheet_metadata(session, image_info['sheet_name'])
                if not sheet_meta:
                    continue
                
                # Создаем запись изображения
                image_record = ProductImage(
                    local_path=os.path.join(self.images_dir, filename),
                    sheet_id=sheet_meta.id,  # Используем числовой ID из метаданных
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

    def show_sample_results(self):
        """Показывает примеры результатов парсинга"""
        session = self.db.get_session()
        
        try:
            self.logger.info("🔍 ПРИМЕРЫ РЕЗУЛЬТАТОВ:")
            self.logger.info("-" * 40)
            
            # Показываем первые 10 изображений
            images = session.query(ProductImage).limit(10).all()
            for img in images:
                self.logger.info(f"📷 {os.path.basename(img.local_path)}")
                self.logger.info(f"   Sheet ID: {img.sheet_id}")
                self.logger.info(f"   Позиция: {img.column}{img.row}")
                self.logger.info(f"   Тип: {img.image_type}")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка показа результатов: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    parser = UnifiedImageParser()
    parser.parse_all_images()
    parser.show_sample_results()

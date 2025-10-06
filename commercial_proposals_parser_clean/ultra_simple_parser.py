#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
УЛЬТРА-ПРОСТОЙ ПАРСЕР КОММЕРЧЕСКИХ ПРЕДЛОЖЕНИЙ
============================================

ЛОГИКА:
- 1 строка с названием товара = 1 товар в базе
- Нет названия = пропускаем строку
- Все данные из строки сохраняем как есть (неструктурно)
- Привязываем фотографии по позиции строки
"""

import os
import sys
import pandas as pd
import logging
from datetime import datetime

# Настройка путей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Product, ProductImage, SheetMetadata, PriceOffer

class UltraSimpleParser:
    def __init__(self):
        self.db = DatabaseManager  # Используем готовый экземпляр
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ultra_simple_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def find_excel_files(self):
        """Поиск ТОЛЬКО оригинальных Excel файлов (без normalized)"""
        excel_files = []
        storage_path = os.path.join(os.path.dirname(__file__), 'storage', 'excel_files')
        
        if not os.path.exists(storage_path):
            self.logger.error(f"❌ Папка {storage_path} не найдена!")
            return []
            
        for file in os.listdir(storage_path):
            if (file.endswith('.xlsx') and 
                not file.startswith('~') and 
                'normalized' not in file):  # Исключаем нормализованные
                full_path = os.path.join(storage_path, file)
                excel_files.append(full_path)
                
        self.logger.info(f"🔍 Найдено {len(excel_files)} оригинальных Excel файлов")
        return excel_files

    def extract_sheet_id(self, filename):
        """Извлечение sheet_id из имени файла"""
        basename = os.path.basename(filename)
        # Убираем расширение и суффиксы
        sheet_id = basename.replace('.xlsx', '').replace('_normalized', '')
        return sheet_id

    def parse_single_file(self, file_path):
        """Парсинг одного Excel файла - ТОЛЬКО основной лист с товарами"""
        self.logger.info(f"📄 Парсим файл: {os.path.basename(file_path)}")
        
        try:
            # Читаем файл - ТОЛЬКО первый лист (основной)
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Получаем sheet_id и метаданные
            sheet_id = self.extract_sheet_id(file_path)
            session = self.db.get_session()
            
            sheet_metadata = session.query(SheetMetadata).filter_by(sheet_id=sheet_id).first()
            if not sheet_metadata:
                self.logger.warning(f"⚠️ Метаданные для {sheet_id} не найдены, создаем новые")
                sheet_metadata = SheetMetadata(
                    sheet_id=sheet_id,
                    sheet_name=f"Sheet_{sheet_id}",
                    total_rows=len(df),
                    total_columns=len(df.columns)
                )
                session.add(sheet_metadata)
                session.flush()

            products_created = 0
            
            # УЛУЧШЕННАЯ ЛОГИКА: ищем столбец с названиями товаров
            product_column = None
            
            # Ищем столбец, который содержит ключевые слова в заголовке или в первой строке
            for col in df.columns:
                col_name = str(col).lower()
                first_row_value = str(df[col].iloc[0]).lower() if len(df) > 0 else ""
                
                # Точные совпадения для ключевых слов (избегаем ложных срабатываний)
                if (('наименование' in col_name or 'наименование' in first_row_value) or
                    ('товар' in col_name or 'товар' in first_row_value) or
                    ('продукт' in col_name or 'продукт' in first_row_value) or
                    (first_row_value == 'name') or  # Точное совпадение для "name"
                    ('product name' in col_name or 'product name' in first_row_value) or
                    (col_name == 'name') or  # Точное совпадение для заголовка
                    ('item' in col_name or first_row_value == 'item')):
                    product_column = col
                    break
            
            # Если не нашли по ключевым словам, ищем столбец с наибольшим количеством непустых значений
            if product_column is None:
                max_non_empty = 0
                for col in df.columns:
                    non_empty_count = df[col].notna().sum() - (df[col] == '').sum()
                    if non_empty_count > max_non_empty and col != df.columns[0]:  # Исключаем первый столбец (Фото)
                        max_non_empty = non_empty_count
                        product_column = col
            
            # Если все еще не нашли, используем второй столбец
            if product_column is None and len(df.columns) > 1:
                product_column = df.columns[1]
            
            self.logger.info(f"🔍 Используем столбец для товаров: {product_column}")
            
            # Проходим по всем строкам и ищем товары
            for index, row in df.iterrows():
                if product_column and product_column in row.index:
                    product_name = str(row[product_column]).strip()
                    
                    # СТРОГАЯ ПРОВЕРКА: пропускаем если нет названия, или это заголовок, или пустое значение
                    if (not product_name or 
                        product_name == 'nan' or 
                        product_name == '' or
                        product_name == 'None' or
                        # Заголовки таблиц
                        product_name.lower() == 'name' or
                        product_name.lower() == 'наименование' or
                        product_name.lower() == 'название' or
                        product_name.lower() == 'товар' or
                        product_name.lower() == 'product' or
                        product_name.lower() == 'item' or
                        'наименование' in product_name.lower() or
                        'название' in product_name.lower() or
                        'товар' in product_name.lower() or
                        'manager' in product_name.lower() or
                        'менеджер' in product_name.lower() or
                        'email' in product_name.lower() or
                        'телефон' in product_name.lower() or
                        'phone' in product_name.lower() or
                        # Служебные заголовки из Excel
                        'circulation period' in product_name.lower() or
                        'price per item' in product_name.lower() or
                        'price per pcs' in product_name.lower() or
                        'sea delivery' in product_name.lower() or
                        'production:' in product_name.lower() or
                        'delivery:' in product_name.lower() or
                        'calendar days' in product_name.lower() or
                        'столбец' in product_name.lower() or
                        'unnamed:' in product_name.lower() or
                        # Проверяем что это не цена (только цифры и точка)
                        product_name.replace('.', '').replace(',', '').replace('$', '').replace(' ', '').isdigit() or
                        len(product_name) < 3):  # Минимум 3 символа для названия
                        continue
                        
                    # Создаем товар
                    product = Product(
                        name=product_name,
                        description=self.extract_description(row),
                        characteristics=self.format_characteristics(row),  # Форматированные данные
                        sheet_id=sheet_metadata.id,
                        start_row=index + 1,  # +1 потому что Excel считает с 1
                        end_row=index + 1  # Одна строка = один товар
                    )
                    
                    session.add(product)
                    session.flush()  # Получаем ID товара
                    
                    # НЕ создаем ценовые предложения - только товары!
                    # Все данные уже сохранены в characteristics
                    
                    products_created += 1
                    self.logger.debug(f"✅ Создан товар: {product_name} (строка {index + 1})")

            session.commit()
            self.logger.info(f"✅ Создано товаров из файла {os.path.basename(file_path)}: {products_created}")
            session.close()
            return products_created
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при парсинге файла {file_path}: {e}")
            if 'session' in locals():
                session.rollback()
                session.close()
            return 0

    def extract_description(self, row):
        """Извлечение описания из строки"""
        try:
            # Ищем столбцы с описанием
            description_parts = []
            for col_name in row.index:
                col_name_lower = str(col_name).lower()
                if any(keyword in col_name_lower for keyword in ['описание', 'характеристик', 'дизайн', 'особенност']):
                    value = str(row[col_name]).strip()
                    if value and value != 'nan':
                        description_parts.append(f"{col_name}: {value}")
            
            return ' | '.join(description_parts) if description_parts else ''
        except:
            return ''

    def format_characteristics(self, row):
        """Форматирование характеристик товара в читаемом виде"""
        try:
            formatted_data = []
            
            for col_name, value in row.items():
                if pd.isna(value) or str(value).strip() == '' or str(value) == 'nan':
                    continue
                    
                # Очищаем название столбца
                clean_col_name = str(col_name).strip()
                if 'Unnamed:' in clean_col_name:
                    clean_col_name = f"Столбец {clean_col_name.split(':')[1].strip()}"
                
                # Очищаем значение
                clean_value = str(value).strip()
                
                # Пропускаем слишком длинные значения (возможно это мусор)
                if len(clean_value) > 200:
                    clean_value = clean_value[:200] + "..."
                
                # Форматируем как "Название: Значение"
                if len(clean_value) > 0:
                    formatted_data.append(f"**{clean_col_name}**: {clean_value}")
            
            # Объединяем все характеристики
            if formatted_data:
                return "\n".join(formatted_data)
            else:
                return "Характеристики не указаны"
                
        except Exception as e:
            self.logger.error(f"Ошибка форматирования характеристик: {e}")
            return "Ошибка обработки характеристик"

    def row_to_json(self, row):
        """Преобразование строки в JSON для сохранения всех данных"""
        try:
            import json
            row_dict = {}
            for col_name, value in row.items():
                # Преобразуем в строку и очищаем
                str_value = str(value).strip()
                if str_value and str_value != 'nan':
                    row_dict[str(col_name)] = str_value
            return json.dumps(row_dict, ensure_ascii=False)
        except:
            return '{}'

    def attach_images(self, session, product, sheet_metadata, row_number):
        """Привязка изображений к товару по позиции строки"""
        try:
            # Ищем изображения для данного листа и строки
            images = session.query(ProductImage).filter_by(
                sheet_id=sheet_metadata.id,
                row=row_number
            ).all()
            
            if images:
                for img in images:
                    img.product_id = product.id
                    # Первое изображение в строке делаем главным
                    if img == images[0]:
                        img.image_type = 'main'
                
                self.logger.debug(f"🖼️ Привязано {len(images)} изображений к товару '{product.name}' (строка {row_number})")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка привязки изображений: {e}")

    def clear_database(self):
        """Очистка базы данных перед парсингом"""
        self.logger.info("🧹 Очищаем базу данных...")
        session = self.db.get_session()
        try:
            # Очищаем привязки изображений
            session.query(ProductImage).update({'product_id': None, 'image_type': 'additional'})
            # Удаляем все ценовые предложения
            session.query(PriceOffer).delete()
            # Удаляем все товары
            session.query(Product).delete()
            session.commit()
            self.logger.info("✅ База данных очищена (товары + ценовые предложения)")
        except Exception as e:
            self.logger.error(f"❌ Ошибка очистки БД: {e}")
            session.rollback()
        finally:
            session.close()

    def run_full_parsing(self):
        """Запуск полного парсинга"""
        self.logger.info("🚀 ЗАПУСК УЛЬТРА-ПРОСТОГО ПАРСЕРА")
        self.logger.info("=" * 50)
        
        # Очищаем БД
        self.clear_database()
        
        # Находим файлы
        files = self.find_excel_files()
        if not files:
            self.logger.error("❌ Файлы для парсинга не найдены!")
            return
        
        total_products = 0
        processed_files = 0
        
        # Парсим каждый файл
        for file_path in files:
            products = self.parse_single_file(file_path)
            total_products += products
            if products > 0:
                processed_files += 1
        
        # Финальная статистика
        self.logger.info("=" * 50)
        self.logger.info(f"🎯 РЕЗУЛЬТАТЫ ПАРСИНГА:")
        self.logger.info(f"   📁 Обработано файлов: {processed_files}/{len(files)}")
        self.logger.info(f"   📦 Создано товаров: {total_products}")
        
        # Проверяем привязку изображений
        session = self.db.get_session()
        products_with_images = session.query(Product).join(ProductImage).distinct().count()
        total_images = session.query(ProductImage).filter(ProductImage.product_id.isnot(None)).count()
        session.close()
        
        self.logger.info(f"   🖼️ Товаров с изображениями: {products_with_images}")
        self.logger.info(f"   📷 Всего привязано изображений: {total_images}")
        self.logger.info("=" * 50)
        
        return total_products

if __name__ == "__main__":
    parser = UltraSimpleParser()
    parser.run_full_parsing()

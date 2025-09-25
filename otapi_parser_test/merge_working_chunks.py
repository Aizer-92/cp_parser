#!/usr/bin/env python3
"""
Скрипт для объединения РАБОЧИХ chunks (25-117) в БД
Эти chunks содержат реальные данные с характеристиками
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WorkingChunksMerger:
    """Объединяет рабочие chunks в БД"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.chunk_dir = self.results_dir / "chunks"
        self.db_path = self.results_dir / "all_chunks_database.db"
        
        # Статистика
        self.stats = {
            'total_chunks': 0,
            'total_products': 0,
            'products_added': 0,
            'products_updated': 0,
            'images_added': 0,
            'specs_added': 0,
            'errors': 0
        }
    
    def merge_working_chunks(self):
        """Объединяет рабочие chunks в БД"""
        try:
            print("🔧 ОБЪЕДИНЕНИЕ РАБОЧИХ CHUNKS В БД")
            print("=" * 60)
            
            # Получаем список рабочих chunks (25-117)
            working_chunks = self.get_working_chunks()
            
            if not working_chunks:
                print("❌ Не найдено рабочих chunks!")
                return False
            
            print(f"📁 НАЙДЕНО РАБОЧИХ CHUNKS: {len(working_chunks)}")
            for chunk_file in working_chunks:
                print(f"   {chunk_file.name}")
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Обрабатываем каждый рабочий chunk
            for chunk_file in working_chunks:
                self.process_working_chunk(cursor, chunk_file)
            
            # Сохраняем изменения
            conn.commit()
            conn.close()
            
            # Выводим статистику
            self.print_statistics()
            
            return True
            
        except Exception as e:
            logging.error(f"Ошибка объединения: {e}")
            return False
    
    def get_working_chunks(self):
        """Получает список рабочих chunks (25-117)"""
        chunk_files = list(self.chunk_dir.glob("fast_chunk_*.json"))
        chunk_files.sort(key=lambda x: x.stat().st_mtime)
        
        working_chunks = []
        
        for chunk_file in chunk_files:
            try:
                # Извлекаем номер chunk из имени
                chunk_name = chunk_file.name
                if 'fast_chunk_' in chunk_name:
                    # Ищем номер в формате fast_chunk_XXX_...
                    import re
                    match = re.search(r'fast_chunk_(\d+)_', chunk_name)
                    if match:
                        chunk_num = int(match.group(1))
                        # Берем chunks с 25 по 117 (рабочие)
                        if 25 <= chunk_num <= 117:
                            working_chunks.append(chunk_file)
                            print(f"   Найден рабочий chunk: {chunk_name} (номер: {chunk_num})")
            except Exception as e:
                print(f"   Ошибка парсинга {chunk_file.name}: {e}")
                continue
        
        return working_chunks
    
    def process_working_chunk(self, cursor, chunk_file):
        """Обрабатывает один рабочий chunk"""
        try:
            with open(chunk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                logging.warning(f"Файл {chunk_file.name} не содержит список товаров")
                return
            
            print(f"\n📊 Обработка {chunk_file.name}: {len(data)} товаров")
            
            self.stats['total_chunks'] += 1
            self.stats['total_products'] += len(data)
            
            for product in data:
                try:
                    self.process_working_product(cursor, product)
                except Exception as e:
                    logging.error(f"Ошибка обработки товара: {e}")
                    self.stats['errors'] += 1
                    
        except Exception as e:
            logging.error(f"Ошибка чтения {chunk_file.name}: {e}")
    
    def process_working_product(self, cursor, product):
        """Обрабатывает один товар из рабочего chunk"""
        try:
            # Извлекаем ID
            item_id = product.get('id', '') or product.get('item_id', '')
            if not item_id:
                return
            
            # Убираем префикс abb- если есть
            if str(item_id).startswith('abb-'):
                item_id = str(item_id)[4:]
            
            # Проверяем есть ли товар в БД
            cursor.execute('SELECT item_id FROM products WHERE item_id = ?', (item_id,))
            if cursor.fetchone():
                # Товар есть - обновляем данные
                self.update_working_product(cursor, item_id, product)
                self.stats['products_updated'] += 1
            else:
                # Товара нет - добавляем новый
                self.add_working_product(cursor, item_id, product)
                self.stats['products_added'] += 1
                
        except Exception as e:
            logging.error(f"Ошибка обработки товара {item_id}: {e}")
    
    def update_working_product(self, cursor, item_id, product):
        """Обновляет существующий товар данными из рабочего chunk"""
        try:
            raw_data = product.get('raw_data', {})
            item_data = raw_data.get('Item', {})
            
            if not isinstance(item_data, dict):
                return
            
            # Обновляем основную информацию
            title = item_data.get('Title', '')
            description = item_data.get('Description', '')
            brand = item_data.get('BrandName', '')
            vendor = item_data.get('VendorName', '')
            
            cursor.execute('''
                UPDATE products 
                SET title = ?, description = ?, brand = ?, vendor = ?, 
                    parsed_at = datetime('now')
                WHERE item_id = ?
            ''', (
                title, description, brand, vendor, item_id
            ))
            
            # Обновляем изображения
            self.update_images(cursor, item_id, item_data)
            
            # Обновляем характеристики
            self.update_specifications(cursor, item_id, item_data)
            
        except Exception as e:
            logging.error(f"Ошибка обновления товара {item_id}: {e}")
    
    def add_working_product(self, cursor, item_id, product):
        """Добавляет новый товар из рабочего chunk"""
        try:
            raw_data = product.get('raw_data', {})
            item_data = raw_data.get('Item', {})
            
            if not isinstance(item_data, dict):
                return
            
            # Извлекаем данные
            title = item_data.get('Title', '')
            description = item_data.get('Description', '')
            brand = item_data.get('BrandName', '')
            vendor = item_data.get('VendorName', '')
            category_id = item_data.get('CategoryId', '')
            external_category_id = item_data.get('ExternalCategoryId', '')
            
            # Добавляем товар
            cursor.execute('''
                INSERT INTO products (
                    item_id, title, description, brand, vendor,
                    category_id, external_category_id,
                    parsed_at, chunk_source, chunk_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'working', 'original')
            ''', (
                item_id, title, description, brand, vendor,
                category_id, external_category_id
            ))
            
            # Добавляем изображения и характеристики
            self.update_images(cursor, item_id, item_data)
            self.update_specifications(cursor, item_id, item_data)
            
        except Exception as e:
            logging.error(f"Ошибка добавления товара {item_id}: {e}")
    
    def update_images(self, cursor, item_id, item_data):
        """Обновляет изображения товара"""
        try:
            # Удаляем старые изображения
            cursor.execute('DELETE FROM images WHERE item_id = ?', (item_id,))
            
            # Главное изображение
            main_image = item_data.get('MainPictureUrl', '')
            if main_image:
                cursor.execute('''
                    INSERT INTO images (item_id, image_url, image_type, is_main, width, height)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (item_id, main_image, 'main', True, None, None))
                self.stats['images_added'] += 1
            
            # Дополнительные изображения
            pictures = item_data.get('Pictures', [])
            if isinstance(pictures, list):
                for picture in pictures:
                    if isinstance(picture, dict):
                        url = picture.get('Url', '')
                        if url:
                            cursor.execute('''
                                INSERT INTO images (item_id, image_url, image_type, is_main, width, height)
                                VALUES (?, ?, ?, ?, ?, ?)
                            ''', (item_id, url, 'gallery', False, None, None))
                            self.stats['images_added'] += 1
                            
        except Exception as e:
            logging.error(f"Ошибка обновления изображений {item_id}: {e}")
    
    def update_specifications(self, cursor, item_id, item_data):
        """Обновляет характеристики товара"""
        try:
            # Удаляем старые характеристики
            cursor.execute('DELETE FROM specifications WHERE item_id = ?', (item_id,))
            
            # Основные характеристики
            attributes = item_data.get('Attributes', [])
            if isinstance(attributes, list):
                for attr in attributes:
                    if isinstance(attr, dict):
                        name = attr.get('PropertyName', '')
                        value = attr.get('Value', '')
                        if name and value:
                            cursor.execute('''
                                INSERT INTO specifications (item_id, spec_name, spec_value, spec_type, is_required)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (item_id, name, str(value), 'attribute', False))
                            self.stats['specs_added'] += 1
            
            # Физические параметры
            physical = item_data.get('PhysicalParameters', {})
            if isinstance(physical, dict):
                for key, value in physical.items():
                    if value:
                        cursor.execute('''
                            INSERT INTO specifications (item_id, spec_name, spec_value, spec_type, is_required)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (item_id, f'Physical_{key}', str(value), 'physical', False))
                        self.stats['specs_added'] += 1
            
            # Информация о весе
            weight_info = item_data.get('ActualWeightInfo', {})
            if isinstance(weight_info, dict):
                for key, value in weight_info.items():
                    if value:
                        cursor.execute('''
                            INSERT INTO specifications (item_id, spec_name, spec_value, spec_type, is_required)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (item_id, f'Weight_{key}', str(value), 'weight', False))
                        self.stats['specs_added'] += 1
            
            # Дополнительные характеристики
            additional_specs = [
                ('BrandName', item_data.get('BrandName', '')),
                ('VendorName', item_data.get('VendorName', '')),
                ('CategoryId', item_data.get('CategoryId', '')),
                ('StuffStatus', item_data.get('StuffStatus', '')),
                ('MasterQuantity', item_data.get('MasterQuantity', ''))
            ]
            
            for name, value in additional_specs:
                if value and str(value).strip():
                    cursor.execute('''
                        INSERT INTO specifications (item_id, spec_name, spec_value, spec_type, is_required)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (item_id, name, str(value), 'additional', False))
                    self.stats['specs_added'] += 1
                    
        except Exception as e:
            logging.error(f"Ошибка обновления характеристик {item_id}: {e}")
    
    def print_statistics(self):
        """Выводит статистику объединения"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ОБЪЕДИНЕНИЯ РАБОЧИХ CHUNKS")
        print("="*60)
        print(f"📁 Обработано chunks: {self.stats['total_chunks']}")
        print(f"📦 Обработано товаров: {self.stats['total_products']}")
        print(f"➕ Добавлено товаров: {self.stats['products_added']}")
        print(f"🔄 Обновлено товаров: {self.stats['products_updated']}")
        print(f"🖼️ Добавлено изображений: {self.stats['images_added']}")
        print(f"📋 Добавлено характеристик: {self.stats['specs_added']}")
        print(f"❌ Ошибок: {self.stats['errors']}")
        
        # Проверяем финальное состояние БД
        self.check_final_database_state()
    
    def check_final_database_state(self):
        """Проверяет финальное состояние БД"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM products')
            total_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM images')
            total_images = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM specifications')
            total_specs = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM products p 
                WHERE NOT EXISTS (SELECT 1 FROM images i WHERE i.item_id = p.item_id)
            ''')
            products_without_images = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM products p 
                WHERE NOT EXISTS (SELECT 1 FROM specifications s WHERE s.item_id = p.item_id)
            ''')
            products_without_specs = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n📊 ФИНАЛЬНОЕ СОСТОЯНИЕ БД:")
            print(f"   Всего товаров: {total_products:,}")
            print(f"   Всего изображений: {total_images:,}")
            print(f"   Всего характеристик: {total_specs:,}")
            print(f"   Товаров без изображений: {products_without_images:,}")
            print(f"   Товаров без характеристик: {products_without_specs:,}")
            print(f"   Процент покрытия изображениями: {(total_products - products_without_images)/total_products*100:.1f}%")
            print(f"   Процент покрытия характеристиками: {(total_products - products_without_specs)/total_products*100:.1f}%")
            
        except Exception as e:
            logging.error(f"Ошибка проверки БД: {e}")

def main():
    """Основная функция"""
    merger = WorkingChunksMerger()
    
    if merger.merge_working_chunks():
        print("\n✅ ОБЪЕДИНЕНИЕ РАБОЧИХ CHUNKS УСПЕШНО ЗАВЕРШЕНО!")
    else:
        print("\n❌ ОБЪЕДИНЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")

if __name__ == "__main__":
    main()

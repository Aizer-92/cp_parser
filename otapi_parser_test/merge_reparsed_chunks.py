#!/usr/bin/env python3
"""
Скрипт для объединения перепарсенных chunks в БД
Использует логику из fast_parser.py для корректного извлечения данных
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ReparsedChunksMerger:
    """Объединяет перепарсенные chunks в существующую БД"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.chunk_dir = self.results_dir / "chunks"
        self.db_path = self.results_dir / "all_chunks_database.db"
        
        # Статистика
        self.stats = {
            'total_chunks': 0,
            'total_products': 0,
            'updated_products': 0,
            'images_added': 0,
            'specs_added': 0,
            'errors': 0
        }
    
    def merge_reparsed_chunks(self):
        """Объединяет перепарсенные chunks в БД"""
        try:
            print("🔧 ОБЪЕДИНЕНИЕ ПЕРЕПАРСЕННЫХ CHUNKS В БД")
            print("=" * 60)
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем список новых chunks (последние по времени)
            chunk_files = list(self.chunk_dir.glob("fast_chunk_*.json"))
            chunk_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Берем последние 6 файлов (новые)
            new_chunks = chunk_files[-6:]
            
            print(f"📁 НОВЫЕ CHUNKS ДЛЯ ОБЪЕДИНЕНИЯ:")
            for chunk_file in new_chunks:
                print(f"   {chunk_file.name}")
            
            # Обрабатываем каждый новый chunk
            for chunk_file in new_chunks:
                self.process_chunk(cursor, chunk_file)
            
            # Сохраняем изменения
            conn.commit()
            conn.close()
            
            # Выводим статистику
            self.print_statistics()
            
            return True
            
        except Exception as e:
            logging.error(f"Ошибка объединения: {e}")
            return False
    
    def process_chunk(self, cursor, chunk_file):
        """Обрабатывает один chunk файл"""
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
                    self.process_product(cursor, product)
                except Exception as e:
                    logging.error(f"Ошибка обработки товара: {e}")
                    self.stats['errors'] += 1
                    
        except Exception as e:
            logging.error(f"Ошибка чтения {chunk_file.name}: {e}")
    
    def process_product(self, cursor, product):
        """Обрабатывает один товар из chunk"""
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
                self.update_existing_product(cursor, item_id, product)
                self.stats['updated_products'] += 1
            else:
                # Товара нет - добавляем новый
                self.add_new_product(cursor, item_id, product)
                
        except Exception as e:
            logging.error(f"Ошибка обработки товара {item_id}: {e}")
    
    def update_existing_product(self, cursor, item_id, product):
        """Обновляет существующий товар в БД"""
        try:
            # Получаем данные из product (как в fast_parser.py)
            title = product.get('title', '')
            price = product.get('price', '')
            vendor = product.get('vendor', '')
            brand = product.get('brand', '')
            description = product.get('description', '')
            
            # Извлекаем данные из raw_data.Item
            raw_data = product.get('raw_data', {})
            item_data = raw_data.get('Item', {})
            
            # Извлекаем изображения и характеристики из item_data
            specifications = []
            images = []
            
            if isinstance(item_data, dict):
                # Изображения
                main_image = item_data.get('MainPictureUrl', '')
                if main_image:
                    images.append({'url': main_image, 'is_main': True})
                
                pictures = item_data.get('Pictures', [])
                if isinstance(pictures, list):
                    for picture in pictures:
                        if isinstance(picture, dict):
                            url = picture.get('Url', '')
                            if url:
                                images.append({'url': url, 'is_main': False})
                
                # Характеристики
                attributes = item_data.get('Attributes', [])
                if isinstance(attributes, list):
                    for attr in attributes:
                        if isinstance(attr, dict):
                            name = attr.get('PropertyName', '') or attr.get('name', '')
                            value = attr.get('Value', '') or attr.get('value', '')
                            if name and value:
                                specifications.append({'name': name, 'value': value})
                
                # Дополнительные характеристики
                additional_specs = [
                    ('BrandName', item_data.get('BrandName', '')),
                    ('VendorName', item_data.get('VendorName', '')),
                    ('CategoryName', item_data.get('CategoryName', '')),
                    ('Material', item_data.get('Material', '')),
                    ('Color', item_data.get('Color', '')),
                    ('Size', item_data.get('Size', '')),
                    ('Model', item_data.get('Model', '')),
                    ('Style', item_data.get('Style', ''))
                ]
                
                for name, value in additional_specs:
                    if value and str(value).strip():
                        specifications.append({'name': name, 'value': str(value)})
            
            # Обновляем основную информацию
            cursor.execute('''
                UPDATE products 
                SET title = ?, price = ?, vendor = ?, brand = ?, 
                    description = ?, parsed_at = datetime('now')
                WHERE item_id = ?
            ''', (
                title, price, vendor, brand, description, item_id
            ))
            
            # Обновляем изображения
            if images:
                # Удаляем старые изображения
                cursor.execute('DELETE FROM images WHERE item_id = ?', (item_id,))
                
                # Добавляем новые изображения
                if isinstance(images, list):
                    for img in images:
                        if isinstance(img, dict):
                            img_url = img.get('url', '')
                            is_main = img.get('is_main', False)
                            if img_url:
                                cursor.execute('''
                                    INSERT INTO images (item_id, image_url, image_type, is_main, width, height)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                ''', (item_id, img_url, 'gallery', is_main, None, None))
                                self.stats['images_added'] += 1
            
            # Обновляем характеристики
            if specifications:
                # Удаляем старые характеристики
                cursor.execute('DELETE FROM specifications WHERE item_id = ?', (item_id,))
                
                # Добавляем новые характеристики
                if isinstance(specifications, list):
                    for spec in specifications:
                        if isinstance(spec, dict):
                            name = spec.get('name', '')
                            value = spec.get('value', '')
                            if name and value:
                                cursor.execute('''
                                    INSERT INTO specifications (item_id, spec_name, spec_value, spec_type, is_required)
                                    VALUES (?, ?, ?, ?, ?)
                                ''', (item_id, name, str(value), 'attribute', False))
                                self.stats['specs_added'] += 1
                                
        except Exception as e:
            logging.error(f"Ошибка обновления товара {item_id}: {e}")
    
    def add_new_product(self, cursor, item_id, product):
        """Добавляет новый товар в БД"""
        try:
            # Получаем данные
            title = product.get('title', '')
            price = product.get('price', '')
            vendor = product.get('vendor', '')
            brand = product.get('brand', '')
            description = product.get('description', '')
            
            # Добавляем товар
            cursor.execute('''
                INSERT INTO products (
                    item_id, title, price, vendor, brand, description,
                    parsed_at, chunk_source, chunk_type
                ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'), 'reparsed', 'fast')
            ''', (
                item_id, title, price, vendor, brand, description
            ))
            
            # Добавляем изображения и характеристики
            self.update_existing_product(cursor, item_id, product)
            
        except Exception as e:
            logging.error(f"Ошибка добавления товара {item_id}: {e}")
    
    def print_statistics(self):
        """Выводит статистику объединения"""
        print("\n" + "="*60)
        print("📊 СТАТИСТИКА ОБЪЕДИНЕНИЯ ПЕРЕПАРСЕННЫХ CHUNKS")
        print("="*60)
        print(f"📁 Обработано chunks: {self.stats['total_chunks']}")
        print(f"📦 Обработано товаров: {self.stats['total_products']}")
        print(f"🔄 Обновлено товаров: {self.stats['updated_products']}")
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
            
            conn.close()
            
            print(f"\n📊 ФИНАЛЬНОЕ СОСТОЯНИЕ БД:")
            print(f"   Всего товаров: {total_products:,}")
            print(f"   Всего изображений: {total_images:,}")
            print(f"   Всего характеристик: {total_specs:,}")
            print(f"   Товаров без изображений: {products_without_images:,}")
            print(f"   Процент покрытия: {(total_products - products_without_images)/total_products*100:.1f}%")
            
        except Exception as e:
            logging.error(f"Ошибка проверки БД: {e}")

def main():
    """Основная функция"""
    merger = ReparsedChunksMerger()
    
    if merger.merge_reparsed_chunks():
        print("\n✅ ОБЪЕДИНЕНИЕ УСПЕШНО ЗАВЕРШЕНО!")
    else:
        print("\n❌ ОБЪЕДИНЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Скрипт для объединения нового OTAPI chunk в БД и проверки качества
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OTAPIChunkMerger:
    """Объединяет OTAPI chunk в БД"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.results_dir = self.data_dir / "results"
        self.chunk_dir = self.results_dir / "chunks"
        self.db_path = self.results_dir / "all_chunks_database.db"
        
        # Статистика
        self.stats = {
            'total_products': 0,
            'products_added': 0,
            'products_updated': 0,
            'images_added': 0,
            'specs_added': 0,
            'errors': 0
        }
    
    def merge_otapi_chunk(self):
        """Объединяет OTAPI chunk в БД"""
        try:
            print("🔧 ОБЪЕДИНЕНИЕ OTAPI CHUNK В БД")
            print("=" * 60)
            
            # Находим OTAPI chunk
            otapi_chunk = self.find_otapi_chunk()
            
            if not otapi_chunk:
                print("❌ Не найден OTAPI chunk!")
                return False
            
            print(f"📁 Найден OTAPI chunk: {otapi_chunk.name}")
            
            # Читаем данные
            with open(otapi_chunk, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                print("❌ Файл не содержит список товаров")
                return False
            
            print(f"📊 Всего товаров в chunk: {len(data)}")
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Обрабатываем каждый товар
            for product in data:
                try:
                    self.process_otapi_product(cursor, product)
                except Exception as e:
                    logging.error(f"Ошибка обработки товара: {e}")
                    self.stats['errors'] += 1
            
            # Сохраняем изменения
            conn.commit()
            conn.close()
            
            # Выводим статистику
            self.print_statistics()
            
            # Проверяем качество после объединения
            self.check_quality_after_merge()
            
            return True
            
        except Exception as e:
            logging.error(f"Ошибка объединения: {e}")
            return False
    
    def find_otapi_chunk(self):
        """Находит OTAPI chunk"""
        chunk_files = list(self.chunk_dir.glob("otapi_chunk_*.json"))
        if chunk_files:
            # Берем самый новый
            chunk_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return chunk_files[0]
        return None
    
    def process_otapi_product(self, cursor, product):
        """Обрабатывает один товар из OTAPI chunk"""
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
                self.update_otapi_product(cursor, item_id, product)
                self.stats['products_updated'] += 1
            else:
                # Товара нет - добавляем новый
                self.add_otapi_product(cursor, item_id, product)
                self.stats['products_added'] += 1
                
        except Exception as e:
            logging.error(f"Ошибка обработки товара {item_id}: {e}")
    
    def update_otapi_product(self, cursor, item_id, product):
        """Обновляет существующий товар данными из OTAPI chunk"""
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
    
    def add_otapi_product(self, cursor, item_id, product):
        """Добавляет новый товар из OTAPI chunk"""
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
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), 'otapi', 'api')
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
        print("📊 СТАТИСТИКА ОБЪЕДИНЕНИЯ OTAPI CHUNK")
        print("=" * 60)
        print(f"📦 Обработано товаров: {self.stats['total_products']}")
        print(f"➕ Добавлено товаров: {self.stats['products_added']}")
        print(f"🔄 Обновлено товаров: {self.stats['products_updated']}")
        print(f"🖼️ Добавлено изображений: {self.stats['images_added']}")
        print(f"📋 Добавлено характеристик: {self.stats['specs_added']}")
        print(f"❌ Ошибок: {self.stats['errors']}")
    
    def check_quality_after_merge(self):
        """Проверяет качество данных после объединения"""
        print(f"\n🔍 ПРОВЕРКА КАЧЕСТВА ПОСЛЕ ОБЪЕДИНЕНИЯ")
        print("-" * 40)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Общая статистика БД
            cursor.execute('SELECT COUNT(*) FROM products')
            total_products = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM images')
            total_images = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM specifications')
            total_specs = cursor.fetchone()[0]
            
            # Товары без изображений
            cursor.execute('''
                SELECT COUNT(*) FROM products p 
                WHERE NOT EXISTS (SELECT 1 FROM images i WHERE i.item_id = p.item_id)
            ''')
            products_without_images = cursor.fetchone()[0]
            
            # Товары без характеристик
            cursor.execute('''
                SELECT COUNT(*) FROM products p 
                WHERE NOT EXISTS (SELECT 1 FROM specifications s WHERE s.item_id = p.item_id)
            ''')
            products_without_specs = cursor.fetchone()[0]
            
            # Товары без описаний
            cursor.execute('''
                SELECT COUNT(*) FROM products 
                WHERE description IS NULL OR description = '' OR description = 'Описание товара'
            ''')
            products_without_descriptions = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"📊 ФИНАЛЬНОЕ СОСТОЯНИЕ БД:")
            print(f"   Всего товаров: {total_products:,}")
            print(f"   Всего изображений: {total_images:,}")
            print(f"   Всего характеристик: {total_specs:,}")
            print(f"   Товаров без изображений: {products_without_images:,}")
            print(f"   Товаров без характеристик: {products_without_specs:,}")
            print(f"   Товаров без описаний: {products_without_descriptions:,}")
            
            if total_products > 0:
                print(f"\n📈 ПРОЦЕНТЫ ПОКРЫТИЯ:")
                print(f"   Изображениями: {(total_products - products_without_images)/total_products*100:.1f}%")
                print(f"   Характеристиками: {(total_products - products_without_specs)/total_products*100:.1f}%")
                print(f"   Описаниями: {(total_products - products_without_descriptions)/total_products*100:.1f}%")
            
            # Анализ улучшений
            print(f"\n🎯 АНАЛИЗ УЛУЧШЕНИЙ:")
            if products_without_images > 0:
                print(f"   ⚠️  Осталось {products_without_images} товаров без изображений")
            else:
                print(f"   ✅ Все товары имеют изображения!")
            
            if products_without_specs > 0:
                print(f"   ⚠️  Осталось {products_without_specs} товаров без характеристик")
            else:
                print(f"   ✅ Все товары имеют характеристики!")
            
            if products_without_descriptions > 0:
                print(f"   ⚠️  Осталось {products_without_descriptions} товаров без описаний")
            else:
                print(f"   ✅ Все товары имеют описания!")
                
        except Exception as e:
            logging.error(f"Ошибка проверки качества: {e}")

def main():
    """Основная функция"""
    merger = OTAPIChunkMerger()
    
    if merger.merge_otapi_chunk():
        print("\n✅ ОБЪЕДИНЕНИЕ OTAPI CHUNK УСПЕШНО ЗАВЕРШЕНО!")
    else:
        print("\n❌ ОБЪЕДИНЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")

if __name__ == "__main__":
    main()

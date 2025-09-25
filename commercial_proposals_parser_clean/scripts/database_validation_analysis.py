#!/usr/bin/env python3
"""
Анализ валидности данных в БД без изменения исходных данных
Создает отчет для дальнейшего анализа и разметки
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, ProductImage, PriceOffer
import pandas as pd
from pathlib import Path
import re
from collections import defaultdict
import json

class DatabaseValidator:
    """Валидатор данных БД для анализа"""
    
    def __init__(self):
        self.session = DatabaseManager.get_session()
        self.validation_results = {
            'products': [],
            'images': [],
            'prices': [],
            'summary': {}
        }
    
    def analyze_products(self):
        """Анализирует товары на валидность"""
        print("🔍 АНАЛИЗ ТОВАРОВ")
        print("=" * 50)
        
        products = self.session.query(Product).all()
        
        categories = {
            'valid': [],
            'suspicious_name': [],
            'no_characteristics': [],
            'huge_row_range': [],
            'no_images': [],
            'no_prices': [],
            'phantom': []
        }
        
        for product in products:
            product_data = {
                'id': product.id,
                'name': product.name,
                'sheet_id': product.sheet_id,
                'start_row': product.start_row,
                'end_row': product.end_row,
                'row_range': product.end_row - product.start_row + 1,
                'has_characteristics': bool(product.characteristics and product.characteristics.strip()),
                'characteristics_length': len(product.characteristics or ''),
                'issues': []
            }
            
            # Проверка названия
            if not product.name or len(product.name.strip()) < 2:
                categories['suspicious_name'].append(product_data)
                product_data['issues'].append('empty_or_short_name')
            elif self._is_service_name(product.name):
                categories['suspicious_name'].append(product_data)
                product_data['issues'].append('service_name')
            
            # Проверка характеристик
            if not product_data['has_characteristics']:
                categories['no_characteristics'].append(product_data)
                product_data['issues'].append('no_characteristics')
            
            # Проверка диапазона строк
            if product_data['row_range'] > 50:
                categories['huge_row_range'].append(product_data)
                product_data['issues'].append('huge_row_range')
            
            # Проверка изображений
            images_count = self.session.query(ProductImage).filter(ProductImage.product_id == product.id).count()
            product_data['images_count'] = images_count
            if images_count == 0:
                categories['no_images'].append(product_data)
                product_data['issues'].append('no_images')
            
            # Проверка цен
            prices_count = self.session.query(PriceOffer).filter(PriceOffer.product_id == product.id).count()
            product_data['prices_count'] = prices_count
            if prices_count == 0:
                categories['no_prices'].append(product_data)
                product_data['issues'].append('no_prices')
            
            # Фантомные товары (огромный диапазон строк)
            if product_data['row_range'] > 100:
                categories['phantom'].append(product_data)
                product_data['issues'].append('phantom_product')
            
            # Валидные товары
            if not product_data['issues']:
                categories['valid'].append(product_data)
            
            self.validation_results['products'].append(product_data)
        
        # Выводим статистику
        print(f"📊 Всего товаров: {len(products)}")
        print(f"✅ Валидных: {len(categories['valid'])}")
        print(f"⚠️  Подозрительные названия: {len(categories['suspicious_name'])}")
        print(f"📝 Без характеристик: {len(categories['no_characteristics'])}")
        print(f"📏 Огромный диапазон строк: {len(categories['huge_row_range'])}")
        print(f"🖼️  Без изображений: {len(categories['no_images'])}")
        print(f"💰 Без цен: {len(categories['no_prices'])}")
        print(f"👻 Фантомные товары: {len(categories['phantom'])}")
        
        # Показываем примеры проблемных товаров
        if categories['phantom']:
            print(f"\\n👻 ФАНТОМНЫЕ ТОВАРЫ (топ-5):")
            for product_data in sorted(categories['phantom'], key=lambda x: x['row_range'], reverse=True)[:5]:
                print(f"  ID {product_data['id']}: {product_data['name']} ({product_data['row_range']} строк)")
        
        if categories['suspicious_name']:
            print(f"\\n⚠️  ПОДОЗРИТЕЛЬНЫЕ НАЗВАНИЯ (топ-5):")
            for product_data in categories['suspicious_name'][:5]:
                print(f"  ID {product_data['id']}: '{product_data['name']}'")
        
        return categories
    
    def analyze_images(self):
        """Анализирует изображения"""
        print(f"\\n🖼️  АНАЛИЗ ИЗОБРАЖЕНИЙ")
        print("=" * 50)
        
        images = self.session.query(ProductImage).all()
        
        categories = {
            'valid': [],
            'missing_files': [],
            'wrong_type': [],
            'orphaned': []
        }
        
        storage_path = Path('storage/images')
        
        for image in images:
            image_data = {
                'id': image.id,
                'product_id': image.product_id,
                'local_path': image.local_path,
                'row': image.row,
                'column': image.column,
                'image_type': image.image_type,
                'issues': []
            }
            
            # Проверка существования файла
            if image.local_path:
                file_path = Path(image.local_path)
                if not file_path.exists():
                    categories['missing_files'].append(image_data)
                    image_data['issues'].append('file_not_found')
            
            # Проверка типа изображения
            if image.image_type not in ['main', 'additional']:
                categories['wrong_type'].append(image_data)
                image_data['issues'].append('wrong_type')
            
            # Проверка связи с товаром
            product = self.session.query(Product).filter(Product.id == image.product_id).first()
            if not product:
                categories['orphaned'].append(image_data)
                image_data['issues'].append('orphaned')
            
            if not image_data['issues']:
                categories['valid'].append(image_data)
            
            self.validation_results['images'].append(image_data)
        
        print(f"📊 Всего изображений: {len(images)}")
        print(f"✅ Валидных: {len(categories['valid'])}")
        print(f"📁 Отсутствующие файлы: {len(categories['missing_files'])}")
        print(f"🏷️  Неправильный тип: {len(categories['wrong_type'])}")
        print(f"🔗 Потерянные связи: {len(categories['orphaned'])}")
        
        return categories
    
    def analyze_prices(self):
        """Анализирует цены"""
        print(f"\\n💰 АНАЛИЗ ЦЕН")
        print("=" * 50)
        
        prices = self.session.query(PriceOffer).all()
        
        categories = {
            'valid': [],
            'suspicious_quantity': [],
            'suspicious_price': [],
            'missing_route': [],
            'orphaned': []
        }
        
        for price in prices:
            price_data = {
                'id': price.id,
                'product_id': price.product_id,
                'quantity': price.quantity,
                'price_usd': price.price_usd,
                'route_name': price.route_name,
                'delivery_time': price.delivery_time,
                'issues': []
            }
            
            # Проверка тиража
            if price.quantity is None or price.quantity < 1:
                categories['suspicious_quantity'].append(price_data)
                price_data['issues'].append('invalid_quantity')
            elif price.quantity > 100000:
                categories['suspicious_quantity'].append(price_data)
                price_data['issues'].append('huge_quantity')
            elif price.quantity < 10:
                categories['suspicious_quantity'].append(price_data)
                price_data['issues'].append('small_quantity')
            
            # Проверка цены
            if price.price_usd is None or price.price_usd <= 0:
                categories['suspicious_price'].append(price_data)
                price_data['issues'].append('invalid_price')
            elif price.price_usd > 1000:
                categories['suspicious_price'].append(price_data)
                price_data['issues'].append('huge_price')
            elif price.price_usd < 0.01:
                categories['suspicious_price'].append(price_data)
                price_data['issues'].append('tiny_price')
            
            # Проверка маршрута
            if not price.route_name or price.route_name.strip() == '':
                categories['missing_route'].append(price_data)
                price_data['issues'].append('missing_route')
            
            # Проверка связи с товаром
            product = self.session.query(Product).filter(Product.id == price.product_id).first()
            if not product:
                categories['orphaned'].append(price_data)
                price_data['issues'].append('orphaned')
            
            if not price_data['issues']:
                categories['valid'].append(price_data)
            
            self.validation_results['prices'].append(price_data)
        
        print(f"📊 Всего цен: {len(prices)}")
        print(f"✅ Валидных: {len(categories['valid'])}")
        print(f"📦 Подозрительные тиражи: {len(categories['suspicious_quantity'])}")
        print(f"💵 Подозрительные цены: {len(categories['suspicious_price'])}")
        print(f"🚚 Без маршрута: {len(categories['missing_route'])}")
        print(f"🔗 Потерянные связи: {len(categories['orphaned'])}")
        
        # Показываем примеры
        if categories['suspicious_quantity']:
            print(f"\\n📦 ПОДОЗРИТЕЛЬНЫЕ ТИРАЖИ (топ-5):")
            for price_data in sorted(categories['suspicious_quantity'], key=lambda x: x['quantity'] or 0, reverse=True)[:5]:
                product = self.session.query(Product).filter(Product.id == price_data['product_id']).first()
                product_name = product.name if product else 'Неизвестно'
                print(f"  ID {price_data['product_id']} ({product_name}): тираж {price_data['quantity']}")
        
        if categories['suspicious_price']:
            print(f"\\n💵 ПОДОЗРИТЕЛЬНЫЕ ЦЕНЫ (топ-5):")
            for price_data in sorted(categories['suspicious_price'], key=lambda x: x['price_usd'] or 0, reverse=True)[:5]:
                product = self.session.query(Product).filter(Product.id == price_data['product_id']).first()
                product_name = product.name if product else 'Неизвестно'
                print(f"  ID {price_data['product_id']} ({product_name}): ${price_data['price_usd']}")
        
        return categories
    
    def analyze_sheets_coverage(self):
        """Анализирует покрытие таблиц"""
        print(f"\\n📊 АНАЛИЗ ПОКРЫТИЯ ТАБЛИЦ")
        print("=" * 50)
        
        sheets = self.session.query(SheetMetadata).all()
        
        for sheet in sheets:
            products_count = self.session.query(Product).filter(Product.sheet_id == sheet.id).count()
            images_count = self.session.query(ProductImage).filter(ProductImage.sheet_id == sheet.id).count()
            
            print(f"📋 {sheet.sheet_title} (ID {sheet.id}):")
            print(f"   📦 Товаров: {products_count}")
            print(f"   🖼️  Изображений: {images_count}")
            print(f"   📁 Статус: {sheet.status}")
    
    def _is_service_name(self, name: str) -> bool:
        """Проверяет, является ли название служебной информацией"""
        name_lower = name.lower().strip()
        
        service_patterns = [
            r'менеджер|email|телефон|примечание|фабрика',
            r'цена указана|срок тиража|производство|доставка',
            r'^наименование$',
            r'copy of|цена|доставка|образец',
            r'^материал|^размер|^цвет|^упаковка'
        ]
        
        for pattern in service_patterns:
            if re.search(pattern, name_lower):
                return True
        
        return False
    
    def create_validation_report(self):
        """Создает отчет валидации"""
        print(f"\\n📝 СОЗДАНИЕ ОТЧЕТА ВАЛИДАЦИИ")
        print("=" * 50)
        
        # Сохраняем детальный JSON отчет
        report_path = Path('validation_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Детальный отчет сохранен: {report_path}")
        
        # Создаем CSV для анализа проблемных товаров
        if self.validation_results['products']:
            df_products = pd.DataFrame(self.validation_results['products'])
            df_products.to_csv('problematic_products.csv', index=False, encoding='utf-8')
            print(f"✅ CSV с проблемными товарами: problematic_products.csv")
        
        # Создаем сводку
        summary = {
            'total_products': len(self.validation_results['products']),
            'total_images': len(self.validation_results['images']),
            'total_prices': len(self.validation_results['prices']),
            'products_with_issues': len([p for p in self.validation_results['products'] if p['issues']]),
            'images_with_issues': len([i for i in self.validation_results['images'] if i['issues']]),
            'prices_with_issues': len([p for p in self.validation_results['prices'] if p['issues']])
        }
        
        self.validation_results['summary'] = summary
        
        print(f"\\n📊 СВОДКА:")
        print(f"  Товаров с проблемами: {summary['products_with_issues']}/{summary['total_products']}")
        print(f"  Изображений с проблемами: {summary['images_with_issues']}/{summary['total_images']}")
        print(f"  Цен с проблемами: {summary['prices_with_issues']}/{summary['total_prices']}")
        
        return summary
    
    def close(self):
        """Закрывает сессию"""
        self.session.close()

def main():
    print("🔍 АНАЛИЗ ВАЛИДНОСТИ ДАННЫХ В БД")
    print("=" * 60)
    print("Примечание: Данные НЕ изменяются, только анализируются")
    print("=" * 60)
    
    validator = DatabaseValidator()
    
    try:
        # Анализируем товары
        products_analysis = validator.analyze_products()
        
        # Анализируем изображения
        images_analysis = validator.analyze_images()
        
        # Анализируем цены
        prices_analysis = validator.analyze_prices()
        
        # Анализируем покрытие таблиц
        validator.analyze_sheets_coverage()
        
        # Создаем отчет
        summary = validator.create_validation_report()
        
        print("\\n" + "=" * 60)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print("Все данные сохранены для дальнейшего анализа")
        
    finally:
        validator.close()

if __name__ == "__main__":
    main()

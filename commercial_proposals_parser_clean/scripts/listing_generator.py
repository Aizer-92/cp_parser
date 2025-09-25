"""
Генератор листингов из парсенных данных
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, Product, ProductImage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ListingGenerator:
    """Генератор листингов"""
    
    def __init__(self):
        self.db_manager = DatabaseManager
        self.storage_dir = Path("storage")
        self.listings_dir = self.storage_dir / "listings"
        self.listings_dir.mkdir(exist_ok=True)
    
    def generate_listings(self) -> Dict:
        """Генерация листингов"""
        try:
            logger.info("=== ГЕНЕРАЦИЯ ЛИСТИНГОВ ===")
            
            session = self.db_manager.get_session()
            
            try:
                # Получаем все листы
                sheets = session.query(SheetMetadata).all()
                logger.info(f"Найдено {len(sheets)} листов для генерации листингов")
                
                results = {
                    'listings_generated': 0,
                    'total_products': 0,
                    'total_images': 0,
                    'errors': []
                }
                
                for sheet in sheets:
                    try:
                        # Генерируем листинг для листа
                        listing_data = self._generate_sheet_listing(sheet, session)
                        
                        # Сохраняем листинг
                        listing_file = self.listings_dir / f"{sheet.sheet_title}_listing.json"
                        with open(listing_file, 'w', encoding='utf-8') as f:
                            json.dump(listing_data, f, ensure_ascii=False, indent=2, default=str)
                        
                        results['listings_generated'] += 1
                        results['total_products'] += listing_data.get('total_products', 0)
                        results['total_images'] += listing_data.get('total_images', 0)
                        
                        logger.info(f"✅ Создан листинг: {listing_file.name}")
                        
                    except Exception as e:
                        error_msg = f"Ошибка генерации листинга для {sheet.sheet_title}: {e}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                
                return results
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Ошибка генерации листингов: {e}")
            return {'error': str(e)}
    
    def _generate_sheet_listing(self, sheet: SheetMetadata, session) -> Dict:
        """Генерация листинга для листа"""
        # Получаем изображения для листа
        images = session.query(ProductImage).all()
        
        # Группируем изображения по товарам
        products_data = []
        for i, image in enumerate(images):
            # Парсим JSON позицию
            position_data = image.position if isinstance(image.position, dict) else {}
            
            product_data = {
                'id': i + 1,
                'name': f"Товар {i + 1}",
                'description': f"Описание товара {i + 1}",
                'price_rub': 1000 + i * 100,  # Примерная цена
                'images': [{
                    'path': image.local_path,
                    'position': position_data.get('cell', 'N/A'),
                    'row': position_data.get('row', 'N/A'),
                    'col': position_data.get('col', 'N/A'),
                    'worksheet': position_data.get('worksheet', 'N/A'),
                    'found': position_data.get('found', False),
                    'type': image.image_type,
                    'size': image.file_size
                }]
            }
            products_data.append(product_data)
        
        listing_data = {
            'sheet_info': {
                'title': sheet.sheet_title,
                'project_name': sheet.project_name or 'Не указано',
                'executor': sheet.executor or 'Не указано',
                'total_products': len(products_data),
                'total_images': len(images),
                'created_at': datetime.now().isoformat()
            },
            'products': products_data
        }
        
        return listing_data

def main():
    """Основная функция"""
    generator = ListingGenerator()
    results = generator.generate_listings()
    
    if 'error' in results:
        logger.error(f"Критическая ошибка: {results['error']}")
    else:
        logger.info("Генерация листингов завершена успешно!")

if __name__ == "__main__":
    main()

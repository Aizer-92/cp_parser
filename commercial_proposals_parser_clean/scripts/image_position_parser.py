"""
Парсер позиций изображений в Excel файлах
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from config import STORAGE_DIR
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata, ProductImage

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImagePositionParser:
    """Парсер позиций изображений в Excel файлах"""
    
    def __init__(self):
        self.db_manager = DatabaseManager
        self.storage_dir = STORAGE_DIR
        self.excel_files_dir = self.storage_dir / "excel_files"
        self.images_dir = self.storage_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        
    def parse_images_with_positions(self) -> Dict:
        """Парсинг изображений с позициями"""
        try:
            logger.info("=== ПАРСИНГ ИЗОБРАЖЕНИЙ С ПОЗИЦИЯМИ ===")
            
            # Получаем Excel файлы
            excel_files = list(self.excel_files_dir.glob("*.xlsx"))
            logger.info(f"Найдено {len(excel_files)} Excel файлов")
            
            results = {
                'files_processed': 0,
                'images_extracted': 0,
                'images_saved_to_db': 0,
                'errors': []
            }
            
            for excel_file in excel_files:
                try:
                    logger.info(f"Обработка файла: {excel_file.name}")
                    
                    # Извлекаем изображения с позициями
                    images = self._extract_images_from_excel(excel_file)
                    results['images_extracted'] += len(images)
                    results['files_processed'] += 1
                    
                    # Сохраняем в базу данных
                    saved_count = self._save_images_to_db(images, excel_file)
                    results['images_saved_to_db'] += saved_count
                    
                    logger.info(f"✅ Обработано {len(images)} изображений из {excel_file.name}")
                    
                except Exception as e:
                    error_msg = f"Ошибка обработки {excel_file.name}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Парсинг завершен: {results['images_extracted']} изображений")
            return results
            
        except Exception as e:
            logger.error(f"Ошибка парсинга изображений: {e}")
            return {'error': str(e)}
    
    def _extract_images_from_excel(self, excel_file: Path) -> List[Dict]:
        """Извлечение изображений из Excel файла"""
        images = []
        
        try:
            with zipfile.ZipFile(excel_file, 'r') as zip_file:
                # Получаем медиа файлы
                media_files = [f for f in zip_file.namelist() if f.startswith('xl/media/')]
                
                if not media_files:
                    return images
                
                # Получаем позиции из drawings
                positions = self._get_positions_from_drawings(zip_file)
                
                # Обрабатываем каждое изображение
                for i, media_file in enumerate(media_files):
                    position = positions[i] if i < len(positions) else positions[0] if positions else self._get_default_position()
                    
                    image_info = self._process_image(excel_file, media_file, zip_file, position, i)
                    if image_info:
                        images.append(image_info)
        
        except Exception as e:
            logger.error(f"Ошибка извлечения изображений из {excel_file.name}: {e}")
        
        return images
    
    def _get_positions_from_drawings(self, zip_file: zipfile.ZipFile) -> List[Dict]:
        """Получение позиций из drawings"""
        positions = []
        
        try:
            drawing_files = [f for f in zip_file.namelist() if f.startswith('xl/drawings/') and f.endswith('.xml')]
            
            for drawing_file in drawing_files:
                try:
                    drawing_xml = zip_file.read(drawing_file)
                    root = ET.fromstring(drawing_xml)
                    
                    anchors = root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}oneCellAnchor')
                    anchors.extend(root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}twoCellAnchor'))
                    
                    for anchor in anchors:
                        position = self._extract_position_from_anchor(anchor)
                        if position:
                            positions.append(position)
                
                except Exception as e:
                    logger.warning(f"Ошибка анализа drawing файла {drawing_file}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Ошибка получения позиций из drawings: {e}")
        
        return positions
    
    def _extract_position_from_anchor(self, anchor: ET.Element) -> Dict:
        """Извлечение позиции из якоря"""
        try:
            from_elem = anchor.find('.//{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}from')
            if from_elem is not None:
                row_elem = from_elem.find('.//{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}row')
                col_elem = from_elem.find('.//{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}col')
                
                if row_elem is not None and col_elem is not None:
                    row = int(row_elem.text)
                    col = int(col_elem.text)
                    return {
                        'row': row,
                        'col': col,
                        'cell': self._convert_to_cell_notation(row, col),
                        'found': True,
                        'worksheet': 'sheet1'
                    }
        except Exception as e:
            logger.warning(f"Ошибка извлечения позиции: {e}")
        
        return {}
    
    def _get_default_position(self) -> Dict:
        """Позиция по умолчанию"""
        return {
            'row': 0,
            'col': 0,
            'cell': 'A1',
            'found': False,
            'worksheet': 'unknown'
        }
    
    def _process_image(self, excel_file: Path, media_file: str, zip_file: zipfile.ZipFile, position: Dict, index: int) -> Dict:
        """Обработка изображения"""
        try:
            file_info = zip_file.getinfo(media_file)
            file_extension = Path(media_file).suffix.lower()
            image_type = self._get_image_type(file_extension)
            
            original_name = Path(media_file).name
            unique_name = f"{excel_file.stem}_{original_name}"
            
            image_data = zip_file.read(media_file)
            image_path = self.images_dir / unique_name
            
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            return {
                'original_path': media_file,
                'saved_path': str(image_path),
                'name': unique_name,
                'type': image_type,
                'size': file_info.file_size,
                'position': position,
                'index': index,
                'excel_file': excel_file.name,
                'created_at': datetime.now(timezone.utc)
            }
        
        except Exception as e:
            logger.warning(f"Ошибка обработки изображения {media_file}: {e}")
            return None
    
    def _get_image_type(self, file_extension: str) -> str:
        """Определение типа изображения"""
        image_types = {
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.tiff': 'tiff',
            '.webp': 'webp'
        }
        return image_types.get(file_extension, 'unknown')
    
    def _convert_to_cell_notation(self, row: int, col: int) -> str:
        """Конвертация координат в формат A1"""
        try:
            col_letter = self._col_index_to_letter(col)
            return f"{col_letter}{row + 1}"
        except Exception:
            return f"R{row}C{col}"
    
    def _col_index_to_letter(self, col_index: int) -> str:
        """Конвертация индекса колонки в букву"""
        result = ""
        while col_index >= 0:
            result = chr(65 + (col_index % 26)) + result
            col_index = col_index // 26 - 1
        return result
    
    def _save_images_to_db(self, images: List[Dict], excel_file: Path) -> int:
        """Сохранение изображений в базу данных"""
        try:
            session = self.db_manager.get_session()
            saved_count = 0
            
            try:
                # Находим или создаем лист
                sheet = session.query(SheetMetadata).filter(
                    SheetMetadata.sheet_title == excel_file.stem
                ).first()
                
                if not sheet:
                    sheet = SheetMetadata(
                        sheet_url=f"https://docs.google.com/spreadsheets/d/{excel_file.stem}",
                        sheet_title=excel_file.stem,
                        sheet_id=excel_file.stem,
                        status='processed',
                        local_file_path=str(excel_file)
                    )
                    session.add(sheet)
                    session.flush()
                
                # Сохраняем изображения
                for image_info in images:
                    product_image = ProductImage(
                        product_id=1,  # Временно
                        sheet_id=sheet.id,  # ID таблицы!
                        local_path=image_info['saved_path'],
                        image_type='main',
                        file_size=image_info['size'],
                        format=image_info['type'],
                        is_downloaded=True,
                        position=image_info['position']  # Сохраняем позицию!
                    )
                    session.add(product_image)
                    saved_count += 1
                
                session.commit()
                
            except Exception as e:
                session.rollback()
                logger.error(f"Ошибка сохранения в базу данных: {e}")
                raise
            finally:
                session.close()
            
            return saved_count
            
        except Exception as e:
            logger.error(f"Ошибка сохранения изображений: {e}")
            return 0

def main():
    """Основная функция"""
    parser = ImagePositionParser()
    results = parser.parse_images_with_positions()
    
    if 'error' in results:
        logger.error(f"Критическая ошибка: {results['error']}")
    else:
        logger.info("Парсинг изображений завершен успешно!")

if __name__ == "__main__":
    main()

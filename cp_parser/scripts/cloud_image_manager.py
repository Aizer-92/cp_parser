#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Менеджер облачных изображений для парсера коммерческих предложений
Проверяет, какие изображения уже загружены в облако, чтобы не загружать их повторно
"""

import json
import os
from pathlib import Path
from typing import Set, Dict, Optional
import logging

class CloudImageManager:
    """Менеджер для работы с облачными изображениями"""
    
    def __init__(self, report_file: str = 'uploaded_images_index.json'):
        """
        Инициализация менеджера
        
        Args:
            report_file: Путь к файлу индекса загруженных изображений
        """
        self.report_file = Path(report_file)
        self.uploaded_filenames: Set[str] = set()
        self.uploaded_images_data: Dict[str, Dict] = {}
        self.load_uploaded_images()
    
    def load_uploaded_images(self) -> None:
        """Загружает список уже загруженных изображений"""
        try:
            if self.report_file.exists():
                with open(self.report_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                
                self.uploaded_filenames = set(index_data.get('filenames', []))
                logging.info(f"Загружен индекс: {len(self.uploaded_filenames)} изображений")
            else:
                logging.warning(f"Файл индекса не найден: {self.report_file}")
                self.uploaded_filenames = set()
                
        except Exception as e:
            logging.error(f"Ошибка загрузки индекса изображений: {e}")
            self.uploaded_filenames = set()
    
    def is_image_uploaded(self, filename: str) -> bool:
        """
        Проверяет, загружено ли изображение в облако
        
        Args:
            filename: Имя файла изображения
            
        Returns:
            True если изображение уже загружено, False иначе
        """
        return filename in self.uploaded_filenames
    
    def get_cloud_url(self, filename: str) -> Optional[str]:
        """
        Получает URL изображения в облачном хранилище
        
        Args:
            filename: Имя файла изображения
            
        Returns:
            URL изображения в облаке или None если не загружено
        """
        if self.is_image_uploaded(filename):
            return f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
        return None
    
    def add_uploaded_image(self, filename: str, size_bytes: int = 0) -> None:
        """
        Добавляет изображение в список загруженных (для обновления индекса)
        
        Args:
            filename: Имя файла изображения
            size_bytes: Размер файла в байтах
        """
        self.uploaded_filenames.add(filename)
        logging.info(f"Добавлено в индекс: {filename}")
    
    def get_upload_stats(self) -> Dict[str, int]:
        """
        Получает статистику загруженных изображений
        
        Returns:
            Словарь со статистикой
        """
        return {
            'total_uploaded': len(self.uploaded_filenames),
            'index_file_exists': self.report_file.exists()
        }
    
    def should_upload_image(self, filename: str) -> bool:
        """
        Определяет, нужно ли загружать изображение
        
        Args:
            filename: Имя файла изображения
            
        Returns:
            True если нужно загружать, False если уже загружено
        """
        return not self.is_image_uploaded(filename)
    
    def get_missing_images(self, image_filenames: list) -> list:
        """
        Получает список изображений, которые нужно загрузить
        
        Args:
            image_filenames: Список имен файлов изображений
            
        Returns:
            Список изображений, которые не загружены в облако
        """
        return [filename for filename in image_filenames 
                if self.should_upload_image(filename)]
    
    def get_uploaded_images(self, image_filenames: list) -> list:
        """
        Получает список изображений, которые уже загружены
        
        Args:
            image_filenames: Список имен файлов изображений
            
        Returns:
            Список изображений, которые уже загружены в облако
        """
        return [filename for filename in image_filenames 
                if self.is_image_uploaded(filename)]

def create_image_manager() -> CloudImageManager:
    """
    Создает экземпляр менеджера облачных изображений
    
    Returns:
        CloudImageManager: Экземпляр менеджера
    """
    return CloudImageManager()

# Пример использования
if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Создаем менеджер
    manager = create_image_manager()
    
    # Получаем статистику
    stats = manager.get_upload_stats()
    print(f"📊 Статистика: {stats}")
    
    # Тестируем проверку изображений
    test_filenames = [
        "1D9Wk9TV-nc-Cq7Eic83-6MQ4G13xy4MUCLhdOCVKzAw_A4_6c.png",
        "test_new_image.jpg",
        "another_test.png"
    ]
    
    print("\n🧪 Тестирование:")
    for filename in test_filenames:
        is_uploaded = manager.is_image_uploaded(filename)
        cloud_url = manager.get_cloud_url(filename)
        should_upload = manager.should_upload_image(filename)
        
        print(f"📁 {filename}")
        print(f"   Загружено: {'✅' if is_uploaded else '❌'}")
        print(f"   URL: {cloud_url or 'Нет'}")
        print(f"   Нужно загружать: {'Да' if should_upload else 'Нет'}")
        print()
    
    # Тестируем фильтрацию
    missing = manager.get_missing_images(test_filenames)
    uploaded = manager.get_uploaded_images(test_filenames)
    
    print(f"📋 Нужно загрузить: {len(missing)} изображений")
    print(f"📋 Уже загружено: {len(uploaded)} изображений")

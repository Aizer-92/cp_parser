#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример интеграции CloudImageManager с парсером коммерческих предложений
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent))

from cloud_image_manager import CloudImageManager
import logging

def example_parsing_with_cloud_check():
    """Пример парсинга с проверкой облачных изображений"""
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    print("🔧 Пример интеграции CloudImageManager с парсером")
    print("=" * 60)
    
    # Создаем менеджер облачных изображений
    manager = CloudImageManager()
    
    # Получаем статистику
    stats = manager.get_upload_stats()
    print(f"📊 Загружено изображений: {stats['total_uploaded']:,}")
    print()
    
    # Симулируем парсинг нового коммерческого предложения
    print("📋 Симулируем парсинг нового КП...")
    
    # Список изображений из нового КП (пример)
    new_images = [
        "1D9Wk9TV-nc-Cq7Eic83-6MQ4G13xy4MUCLhdOCVKzAw_A4_6c.png",  # Уже загружено
        "new_product_image_1.jpg",  # Новое изображение
        "new_product_image_2.png",  # Новое изображение
        "1OjUpP-7qUtMbJlYo7ADDPkSIENKOPB3GvfWLxf4615E_A4_97.png",  # Уже загружено
    ]
    
    print(f"📁 Найдено {len(new_images)} изображений в новом КП")
    print()
    
    # Разделяем изображения на загруженные и новые
    uploaded_images = manager.get_uploaded_images(new_images)
    missing_images = manager.get_missing_images(new_images)
    
    print("📊 АНАЛИЗ ИЗОБРАЖЕНИЙ:")
    print("=" * 60)
    print(f"✅ Уже загружено: {len(uploaded_images)} изображений")
    print(f"🆕 Нужно загрузить: {len(missing_images)} изображений")
    print()
    
    # Обрабатываем уже загруженные изображения
    if uploaded_images:
        print("✅ ОБРАБОТКА ЗАГРУЖЕННЫХ ИЗОБРАЖЕНИЙ:")
        for filename in uploaded_images:
            cloud_url = manager.get_cloud_url(filename)
            print(f"   📁 {filename}")
            print(f"      🌐 URL: {cloud_url}")
            print(f"      💾 Пропускаем загрузку")
        print()
    
    # Обрабатываем новые изображения
    if missing_images:
        print("🆕 ОБРАБОТКА НОВЫХ ИЗОБРАЖЕНИЙ:")
        for filename in missing_images:
            print(f"   📁 {filename}")
            print(f"      ⬆️  Загружаем в облако...")
            
            # Здесь был бы код загрузки изображения
            # upload_image_to_cloud(filename)
            
            # После загрузки добавляем в индекс
            manager.add_uploaded_image(filename)
            print(f"      ✅ Загружено и добавлено в индекс")
        print()
    
    # Итоговая статистика
    print("📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 60)
    print(f"📁 Всего изображений в КП: {len(new_images)}")
    print(f"✅ Уже было в облаке: {len(uploaded_images)}")
    print(f"🆕 Загружено новых: {len(missing_images)}")
    print(f"💰 Экономия времени: {len(uploaded_images)} загрузок")
    print(f"🚀 Ускорение парсинга: {len(uploaded_images)/len(new_images)*100:.1f}%")

def example_batch_processing():
    """Пример пакетной обработки с проверкой облачных изображений"""
    
    print("\n" + "=" * 60)
    print("📦 ПРИМЕР ПАКЕТНОЙ ОБРАБОТКИ")
    print("=" * 60)
    
    manager = CloudImageManager()
    
    # Симулируем пакетную обработку нескольких КП
    batch_images = [
        # КП 1
        ["image1.jpg", "image2.png", "image3.jpg"],
        # КП 2  
        ["image4.png", "image5.jpg", "image6.png"],
        # КП 3
        ["image7.jpg", "image8.png", "image9.jpg"],
    ]
    
    total_images = sum(len(images) for images in batch_images)
    total_uploaded = 0
    total_new = 0
    
    for i, images in enumerate(batch_images, 1):
        print(f"📋 Обработка КП {i}: {len(images)} изображений")
        
        uploaded = manager.get_uploaded_images(images)
        missing = manager.get_missing_images(images)
        
        total_uploaded += len(uploaded)
        total_new += len(missing)
        
        print(f"   ✅ Уже загружено: {len(uploaded)}")
        print(f"   🆕 Нужно загрузить: {len(missing)}")
        print()
    
    print("📊 ИТОГИ ПАКЕТНОЙ ОБРАБОТКИ:")
    print("=" * 60)
    print(f"📁 Всего изображений: {total_images}")
    print(f"✅ Уже в облаке: {total_uploaded}")
    print(f"🆕 Новых для загрузки: {total_new}")
    print(f"⚡ Экономия: {total_uploaded/total_images*100:.1f}% изображений")

if __name__ == "__main__":
    example_parsing_with_cloud_check()
    example_batch_processing()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Создание JSON отчета о загруженных изображениях в облачное хранилище
"""

import json
import sys
from pathlib import Path
import ftplib
from ftplib import FTP_TLS
from datetime import datetime
import hashlib

# Настройки FTP
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'

# Настройки S3
S3_BASE_URL = 'https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods'
CLOUD_IMAGES_PREFIX = 'images/'

def get_uploaded_images_list():
    """Получает список загруженных изображений через FTP"""
    print("📋 Получаю список загруженных изображений...")
    
    uploaded_images = {}
    
    try:
        # Создаем FTPS соединение
        ftp = FTP_TLS()
        ftp.connect(FTP_HOST, 21, timeout=30)
        ftp.login(FTP_USERNAME, FTP_PASSWORD)
        ftp.prot_p()
        
        print("✅ FTP соединение установлено!")
        
        # Переходим в папку images
        ftp.cwd(FTP_REMOTE_DIR)
        print(f"✅ Перешел в папку: {FTP_REMOTE_DIR}")
        
        # Получаем список файлов
        files = []
        ftp.retrlines('LIST', files.append)
        
        print(f"📊 Найдено {len(files)} файлов")
        
        # Обрабатываем каждый файл
        for i, file_info in enumerate(files, 1):
            if i % 1000 == 0:
                print(f"   Обработано: {i}/{len(files)} файлов")
            
            # Парсим информацию о файле
            parts = file_info.split()
            if len(parts) >= 9:
                # Формат: -rw-r--r-- 1 ftp ftp size date time name
                size = int(parts[4])
                date = parts[5]
                time = parts[6]
                filename = ' '.join(parts[8:])  # Имя файла может содержать пробелы
                
                # Пропускаем служебные файлы
                if filename.startswith('.'):
                    continue
                
                # Создаем URL изображения
                cloud_url = f"{S3_BASE_URL}/{CLOUD_IMAGES_PREFIX}{filename}"
                
                # Добавляем в словарь
                uploaded_images[filename] = {
                    'filename': filename,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'upload_date': f"{date} {time}",
                    'cloud_url': cloud_url,
                    'relative_path': filename,  # Относительный путь в папке images
                    'uploaded': True
                }
        
        # Закрываем соединение
        ftp.quit()
        print("✅ Список получен!")
        
        return uploaded_images
        
    except Exception as e:
        print(f"❌ Ошибка получения списка: {e}")
        return {}

def create_upload_report():
    """Создает JSON отчет о загруженных изображениях"""
    print("📝 Создаю JSON отчет о загруженных изображениях...")
    print("=" * 60)
    
    # Получаем список загруженных изображений
    uploaded_images = get_uploaded_images_list()
    
    if not uploaded_images:
        print("❌ Не удалось получить список изображений")
        return
    
    # Создаем отчет
    report = {
        'metadata': {
            'created_at': datetime.now().isoformat(),
            'total_images': len(uploaded_images),
            'cloud_storage': {
                'provider': 'Beget S3',
                'bucket': '73d16f7545b3-promogoods',
                'base_url': S3_BASE_URL,
                'images_prefix': CLOUD_IMAGES_PREFIX
            },
            'ftp_server': {
                'host': FTP_HOST,
                'directory': FTP_REMOTE_DIR
            }
        },
        'images': uploaded_images
    }
    
    # Вычисляем статистику
    total_size_bytes = sum(img['size_bytes'] for img in uploaded_images.values())
    total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
    total_size_gb = round(total_size_mb / 1024, 2)
    
    report['metadata']['total_size_bytes'] = total_size_bytes
    report['metadata']['total_size_mb'] = total_size_mb
    report['metadata']['total_size_gb'] = total_size_gb
    
    # Сохраняем отчет
    report_file = Path('uploaded_images_report.json')
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Отчет сохранен: {report_file}")
        print()
        print("📊 СТАТИСТИКА ЗАГРУЖЕННЫХ ИЗОБРАЖЕНИЙ:")
        print("=" * 60)
        print(f"📁 Всего изображений: {len(uploaded_images):,}")
        print(f"💾 Общий размер: {total_size_mb:,} MB ({total_size_gb:.2f} GB)")
        print(f"📅 Дата создания отчета: {report['metadata']['created_at']}")
        print(f"🌐 Базовый URL: {S3_BASE_URL}/{CLOUD_IMAGES_PREFIX}")
        print()
        
        # Создаем индекс для быстрого поиска
        index_file = Path('uploaded_images_index.json')
        index = {
            'filenames': list(uploaded_images.keys()),
            'created_at': report['metadata']['created_at'],
            'total_count': len(uploaded_images)
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Индекс создан: {index_file}")
        print()
        print("📝 ИСПОЛЬЗОВАНИЕ:")
        print("=" * 60)
        print("1. При парсинге новых КП проверяйте файл uploaded_images_index.json")
        print("2. Если изображение уже загружено, пропускайте его загрузку")
        print("3. Полный отчет в uploaded_images_report.json содержит все детали")
        print()
        print("🔧 ИНТЕГРАЦИЯ В ПАРСЕР:")
        print("=" * 60)
        print("```python")
        print("import json")
        print("")
        print("# Загружаем индекс загруженных изображений")
        print("with open('uploaded_images_index.json', 'r') as f:")
        print("    uploaded_index = json.load(f)")
        print("uploaded_filenames = set(uploaded_index['filenames'])")
        print("")
        print("# При парсинге проверяем:")
        print("if image_filename not in uploaded_filenames:")
        print("    # Загружаем изображение")
        print("    upload_image_to_cloud(image_filename)")
        print("else:")
        print("    # Пропускаем загрузку")
        print("    print(f'Изображение {image_filename} уже загружено')")
        print("```")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения отчета: {e}")

def test_report():
    """Тестирует созданный отчет"""
    print("🧪 Тестирую созданный отчет...")
    
    try:
        # Загружаем отчет
        with open('uploaded_images_report.json', 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        print(f"✅ Отчет загружен: {report['metadata']['total_images']} изображений")
        
        # Загружаем индекс
        with open('uploaded_images_index.json', 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        print(f"✅ Индекс загружен: {index['total_count']} файлов")
        
        # Проверяем соответствие
        if len(report['images']) == index['total_count']:
            print("✅ Количество файлов совпадает!")
        else:
            print("❌ Несоответствие количества файлов!")
        
        # Тестируем поиск
        test_filename = list(report['images'].keys())[0]
        if test_filename in index['filenames']:
            print(f"✅ Поиск работает: {test_filename}")
        else:
            print(f"❌ Поиск не работает: {test_filename}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    print("📊 Создатель отчета о загруженных изображениях")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        test_report()
    else:
        create_upload_report()

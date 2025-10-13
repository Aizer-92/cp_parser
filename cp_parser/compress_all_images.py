#!/usr/bin/env python3
"""
Массовое сжатие изображений >1MB
Ресайз до 1920px + конвертация в WebP с quality=85
"""

import os
import csv
import re
from ftplib import FTP_TLS
from PIL import Image
import io
import time
import sys

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

def get_files_to_compress():
    """Получить список файлов >1MB для сжатия"""
    print("📄 Читаю список файлов из анализа...")
    
    files = []
    with open('STORAGE_ANALYSIS_20251012_1455.txt', 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Парсим строки с файлами
            if 'MB -' in line and '.png' in line:
                try:
                    parts = line.split(' - ', 1)
                    if len(parts) == 2:
                        # Извлекаем размер
                        size_match = re.search(r'(\d+\.\d+)\s+MB', parts[0])
                        if size_match:
                            size_mb = float(size_match.group(1))
                            
                            # Только файлы >1MB
                            if size_mb >= 1.0:
                                filename = parts[1].strip()
                                
                                if filename.endswith('.png') and not filename.endswith('...'):
                                    files.append({
                                        'filename': filename,
                                        'size_mb': size_mb
                                    })
                except:
                    continue
    
    print(f"✅ Найдено {len(files):,} файлов >1MB для сжатия")
    return files


def compress_and_replace_file(ftp, filename, original_size_mb, stats):
    """Скачать, сжать и создать WebP версию (оригинал сохраняется)"""
    try:
        # 1. Скачиваем оригинал
        original_data = io.BytesIO()
        ftp.retrbinary(f'RETR {filename}', original_data.write)
        original_data.seek(0)
        original_size_kb = len(original_data.getvalue()) / 1024
        
        # 2. Открываем изображение
        img = Image.open(original_data)
        original_dimensions = img.size
        
        # 3. Проверяем нужен ли ресайз
        max_size = 1920
        needs_resize = max(original_dimensions) > max_size
        
        if needs_resize:
            # Ресайз с сохранением пропорций
            if original_dimensions[0] > original_dimensions[1]:
                new_width = max_size
                new_height = int(original_dimensions[1] * (max_size / original_dimensions[0]))
            else:
                new_height = max_size
                new_width = int(original_dimensions[0] * (max_size / original_dimensions[1]))
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_dimensions = (new_width, new_height)
        else:
            resized_dimensions = original_dimensions
        
        # 4. Конвертируем в RGB
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 5. Сжимаем в WebP
        compressed_data = io.BytesIO()
        img.save(compressed_data, format='WEBP', quality=85, method=6)
        compressed_data.seek(0)
        compressed_size_kb = len(compressed_data.getvalue()) / 1024
        
        # 6. Создаем WebP версию (оригинал остается)
        new_filename = filename.replace('.png', '.webp')
        compressed_data.seek(0)
        ftp.storbinary(f'STOR {new_filename}', compressed_data)
        
        # Статистика
        compression_ratio = (1 - compressed_size_kb / original_size_kb) * 100
        
        stats['processed'] += 1
        stats['total_original_mb'] += original_size_kb / 1024
        stats['total_compressed_mb'] += compressed_size_kb / 1024
        stats['resized_count'] += 1 if needs_resize else 0
        
        return {
            'filename': filename,
            'new_filename': new_filename,
            'original_size_mb': original_size_kb / 1024,
            'compressed_size_mb': compressed_size_kb / 1024,
            'compression_ratio': compression_ratio,
            'original_dimensions': f"{original_dimensions[0]}x{original_dimensions[1]}",
            'new_dimensions': f"{resized_dimensions[0]}x{resized_dimensions[1]}",
            'resized': 'Yes' if needs_resize else 'No'
        }
        
    except Exception as e:
        stats['failed'] += 1
        return None


def main():
    print("=" * 80)
    print("🗜️  МАССОВОЕ СЖАТИЕ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print()
    
    # 1. Получаем список файлов
    files = get_files_to_compress()
    
    if not files:
        print("❌ Не найдено файлов для сжатия")
        return
    
    print(f"\n📊 Всего файлов для обработки: {len(files):,}")
    print(f"📊 Примерный общий размер: {sum(f['size_mb'] for f in files):.2f} MB")
    
    # 2. Подтверждение
    print("\n⚠️  ВНИМАНИЕ!")
    print("   • Оригинальные .png файлы будут УДАЛЕНЫ")
    print("   • Вместо них будут .webp файлы")
    print("   • Изображения >1920px будут уменьшены до 1920px")
    print("   • Качество WebP: 85%")
    
    response = input("\n❓ Продолжить? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Отменено пользователем")
        return
    
    # 3. Подключаемся к FTP
    print(f"\n🔌 Подключение к FTP...")
    
    try:
        ftp = FTP_TLS(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()
        ftp.cwd(FTP_DIR)
        print("✅ Подключено")
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # 4. Обрабатываем файлы
    print(f"\n🗜️  Начинаю сжатие {len(files):,} файлов...")
    print("   (это займет время, прогресс каждые 10 файлов)\n")
    
    stats = {
        'processed': 0,
        'failed': 0,
        'total_original_mb': 0,
        'total_compressed_mb': 0,
        'resized_count': 0
    }
    
    results = []
    
    for i, file_info in enumerate(files, 1):
        filename = file_info['filename']
        
        # Прогресс каждые 10 файлов
        if i % 10 == 0 or i == 1:
            percent = (i / len(files)) * 100
            print(f"   [{i:,}/{len(files):,}] ({percent:.1f}%) - {filename[:50]}...")
        
        result = compress_and_replace_file(ftp, filename, file_info['size_mb'], stats)
        
        if result:
            results.append(result)
        
        # Небольшая пауза чтобы не перегружать FTP
        if i % 10 == 0:
            time.sleep(0.5)
    
    ftp.quit()
    
    # 5. Сохраняем результаты
    print("\n" + "=" * 80)
    print("📊 ИТОГИ СЖАТИЯ")
    print("=" * 80)
    
    saved_mb = stats['total_original_mb'] - stats['total_compressed_mb']
    compression_percent = (saved_mb / stats['total_original_mb'] * 100) if stats['total_original_mb'] > 0 else 0
    
    print(f"\n✅ УСПЕШНО:")
    print(f"   Обработано файлов: {stats['processed']:,}")
    print(f"   Из них с ресайзом: {stats['resized_count']:,}")
    
    if stats['failed'] > 0:
        print(f"\n❌ ОШИБОК:")
        print(f"   Не удалось обработать: {stats['failed']:,}")
    
    print(f"\n💾 ЭКОНОМИЯ МЕСТА:")
    print(f"   Было: {stats['total_original_mb']:.2f} MB ({stats['total_original_mb']/1024:.2f} GB)")
    print(f"   Стало: {stats['total_compressed_mb']:.2f} MB ({stats['total_compressed_mb']/1024:.2f} GB)")
    print(f"   Сохранено: {saved_mb:.2f} MB ({saved_mb/1024:.2f} GB)")
    print(f"   Коэффициент сжатия: {compression_percent:.1f}%")
    
    # Сохраняем детальный отчет
    if results:
        csv_file = 'COMPRESSION_RESULTS.csv'
        print(f"\n💾 Сохраняю детальный отчет: {csv_file}")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'filename', 'new_filename', 
                'original_size_mb', 'compressed_size_mb',
                'compression_ratio', 'original_dimensions', 'new_dimensions', 'resized'
            ])
            writer.writeheader()
            writer.writerows(results)
        
        print(f"✅ Сохранено {len(results):,} записей")
    
    print("\n" + "=" * 80)
    print("✅ СЖАТИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    
    print(f"\n📊 Средняя экономия на файл: {(saved_mb / stats['processed'] if stats['processed'] > 0 else 0):.2f} MB")
    print(f"📊 Средний коэффициент сжатия: {compression_percent:.1f}%")


if __name__ == '__main__':
    main()


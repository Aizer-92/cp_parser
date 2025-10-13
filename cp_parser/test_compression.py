#!/usr/bin/env python3
"""
Тестовое сжатие 20 самых больших изображений
"""

import os
import csv
import re
from ftplib import FTP_TLS
from PIL import Image
import io
import time

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

def get_top_20_largest_files():
    """Получить 20 самых больших файлов из анализа"""
    print("📄 Читаю список файлов...")
    
    files = []
    with open('STORAGE_ANALYSIS_20251012_1455.txt', 'r', encoding='utf-8') as f:
        count = 0
        for line in f:
            line = line.strip()
            
            # Парсим строки с файлами (формат: "    1.   10.97 MB - filename.png")
            if 'MB -' in line and '.png' in line:
                try:
                    # Разбиваем по " - "
                    parts = line.split(' - ', 1)
                    if len(parts) == 2:
                        # Извлекаем размер
                        size_part = parts[0].strip()
                        # Ищем размер в MB
                        size_match = re.search(r'(\d+\.\d+)\s+MB', size_part)
                        if size_match:
                            size_mb = float(size_match.group(1))
                            filename = parts[1].strip()
                            
                            # Убираем обрезанные имена и не-png файлы
                            if filename.endswith('.png') and not filename.endswith('...'):
                                files.append({
                                    'filename': filename,
                                    'size_mb': size_mb
                                })
                                count += 1
                                
                                # Останавливаемся после 20 файлов
                                if count >= 20:
                                    break
                except:
                    continue
    
    print(f"✅ Найдено {len(files)} файлов для тестирования")
    return files


def download_and_compress_file(ftp, filename, original_size_mb):
    """Скачать, сжать и загрузить обратно файл"""
    print(f"\n📥 Обрабатываю: {filename[:60]}...")
    print(f"   Оригинал: {original_size_mb:.2f} MB")
    
    try:
        # 1. Скачиваем оригинал
        original_data = io.BytesIO()
        ftp.retrbinary(f'RETR {filename}', original_data.write)
        original_data.seek(0)
        original_size_kb = len(original_data.getvalue()) / 1024
        
        # 2. Открываем изображение
        img = Image.open(original_data)
        original_format = img.format
        original_dimensions = img.size
        
        print(f"   Формат: {original_format}, Размер: {original_dimensions[0]}x{original_dimensions[1]}")
        
        # 3. Ресайз до 1920px по большей стороне
        max_size = 1920
        if max(original_dimensions) > max_size:
            # Вычисляем новые размеры с сохранением пропорций
            if original_dimensions[0] > original_dimensions[1]:
                # Ширина больше
                new_width = max_size
                new_height = int(original_dimensions[1] * (max_size / original_dimensions[0]))
            else:
                # Высота больше
                new_height = max_size
                new_width = int(original_dimensions[0] * (max_size / original_dimensions[1]))
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_dimensions = (new_width, new_height)
            print(f"   Ресайз: {original_dimensions[0]}x{original_dimensions[1]} → {new_width}x{new_height}")
        else:
            resized_dimensions = original_dimensions
        
        # 4. Конвертируем в RGB если необходимо
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
        
        # 5. Создаем имя для сжатого файла
        compressed_filename = filename.replace('.png', '_compressed.webp')
        
        # 6. Загружаем сжатый файл на FTP
        compressed_data.seek(0)
        ftp.storbinary(f'STOR {compressed_filename}', compressed_data)
        
        # Результат
        compression_ratio = (1 - compressed_size_kb / original_size_kb) * 100
        
        print(f"   ✅ Сжато: {compressed_size_kb:.2f} KB")
        print(f"   💾 Экономия: {compression_ratio:.1f}%")
        
        return {
            'filename': filename,
            'compressed_filename': compressed_filename,
            'original_size_kb': original_size_kb,
            'compressed_size_kb': compressed_size_kb,
            'compression_ratio': compression_ratio,
            'original_dimensions': f"{original_dimensions[0]}x{original_dimensions[1]}",
            'resized_dimensions': f"{resized_dimensions[0]}x{resized_dimensions[1]}",
            'original_url': f"https://ftp.ru1.storage.beget.cloud{FTP_DIR}/{filename}",
            'compressed_url': f"https://ftp.ru1.storage.beget.cloud{FTP_DIR}/{compressed_filename}"
        }
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return None


def main():
    print("=" * 80)
    print("🧪 ТЕСТОВОЕ СЖАТИЕ 20 САМЫХ БОЛЬШИХ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print()
    
    # 1. Получаем список файлов
    files = get_top_20_largest_files()
    
    if not files:
        print("❌ Не найдено файлов для сжатия")
        return
    
    # 2. Подключаемся к FTP
    print(f"\n🔌 Подключение к FTP...")
    print(f"   Host: {FTP_HOST}")
    print(f"   Path: {FTP_DIR}")
    
    ftp = FTP_TLS(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()
    ftp.cwd(FTP_DIR)
    
    print("✅ Подключено")
    
    # 3. Обрабатываем файлы
    results = []
    
    for i, file_info in enumerate(files, 1):
        print(f"\n{'=' * 80}")
        print(f"📊 Файл {i}/{len(files)}")
        
        result = download_and_compress_file(
            ftp, 
            file_info['filename'], 
            file_info['size_mb']
        )
        
        if result:
            results.append(result)
        
        # Небольшая пауза
        time.sleep(0.5)
    
    ftp.quit()
    
    # 4. Сохраняем результаты
    print("\n" + "=" * 80)
    print("📊 ИТОГИ ТЕСТОВОГО СЖАТИЯ")
    print("=" * 80)
    
    if not results:
        print("\n❌ Не удалось сжать ни одного файла")
        return
    
    # Сохраняем в CSV
    csv_file = 'TEST_COMPRESSION_RESULTS.csv'
    print(f"\n💾 Сохраняю результаты в {csv_file}...")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'filename', 'compressed_filename', 
            'original_size_kb', 'compressed_size_kb', 
            'compression_ratio', 'original_dimensions', 'resized_dimensions',
            'original_url', 'compressed_url'
        ])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"✅ Сохранено {len(results)} результатов")
    
    # Статистика
    total_original = sum(r['original_size_kb'] for r in results) / 1024
    total_compressed = sum(r['compressed_size_kb'] for r in results) / 1024
    total_saved = total_original - total_compressed
    avg_compression = sum(r['compression_ratio'] for r in results) / len(results)
    
    print(f"\n📊 СТАТИСТИКА:")
    print(f"   Обработано файлов: {len(results)}")
    print(f"   Оригинальный размер: {total_original:.2f} MB")
    print(f"   Сжатый размер: {total_compressed:.2f} MB")
    print(f"   Экономия: {total_saved:.2f} MB ({avg_compression:.1f}%)")
    
    # Ссылки для проверки
    print("\n" + "=" * 80)
    print("🔗 ССЫЛКИ ДЛЯ ПРОВЕРКИ")
    print("=" * 80)
    
    print("\n📋 Сравнение оригинал vs сжатый:\n")
    
    for i, result in enumerate(results[:5], 1):  # Показываем первые 5
        print(f"{i}. {result['filename'][:60]}")
        print(f"   Оригинал:  {result['original_url']}")
        print(f"   Сжатый:    {result['compressed_url']}")
        print(f"   Размеры:   {result['original_dimensions']} → {result['resized_dimensions']}")
        print(f"   Экономия:  {result['compression_ratio']:.1f}%")
        print()
    
    if len(results) > 5:
        print(f"... и еще {len(results) - 5} файлов (см. {csv_file})")
    
    print("\n" + "=" * 80)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 80)
    print(f"\n💡 Проверь качество сжатых изображений по ссылкам выше")
    print(f"📄 Полный список: {csv_file}")


if __name__ == '__main__':
    main()


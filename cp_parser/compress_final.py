#!/usr/bin/env python3
"""
ФИНАЛЬНОЕ СЖАТИЕ - использует готовый список FTP файлов
"""

from ftplib import FTP_TLS
from PIL import Image
import io
import re
import json
import os
import pandas as pd

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

BATCH_SIZE = 50
PROGRESS_FILE = 'compression_progress.json'

print("=" * 80)
print("🗜️  ФИНАЛЬНОЕ СЖАТИЕ ИЗОБРАЖЕНИЙ")
print("=" * 80)

# Читаем список существующих файлов из CSV (быстро!)
print("\n📄 Читаю список существующих файлов из FTP_FILES_ANALYSIS.csv...")
df = pd.read_csv('FTP_FILES_ANALYSIS.csv')
# Извлекаем только имена файлов из URLs
ftp_filenames = set()
for url in df['image_url']:
    filename = url.split('/')[-1]
    ftp_filenames.add(filename)
print(f"✅ Файлов на FTP: {len(ftp_filenames):,}")

# Читаем список файлов >1MB из анализа
print("\n📄 Читаю список файлов >1MB из анализа...")
all_files = []
with open('STORAGE_ANALYSIS_20251012_1455.txt', 'r', encoding='utf-8') as f:
    for line in f:
        match = re.search(r'(\d+\.\d+)\s+MB\s+-\s+(.+\.png)', line)
        if match:
            size_mb = float(match.group(1))
            filename = match.group(2).strip()
            if size_mb >= 1.0:
                all_files.append({
                    'filename': filename,
                    'size_mb': size_mb
                })

print(f"✅ Файлов >1MB в анализе: {len(all_files):,}")

# Фильтруем только существующие
existing_files = [f for f in all_files if f['filename'] in ftp_filenames]
print(f"✅ Существует на FTP: {len(existing_files):,}")

# Загружаем прогресс если есть
processed_files = set()
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r') as f:
        data = json.load(f)
        processed_files = set(data.get('processed', []))
    print(f"📊 Уже обработано: {len(processed_files):,}")

# Фильтруем необработанные
remaining_files = [f for f in existing_files if f['filename'] not in processed_files]
print(f"📊 Осталось обработать: {len(remaining_files):,}")
total_size = sum(f['size_mb'] for f in remaining_files)
print(f"📊 Общий размер: {total_size:.2f} MB ({total_size/1024:.2f} GB)")

if len(remaining_files) == 0:
    print("\n✅ ВСЕ ФАЙЛЫ УЖЕ ОБРАБОТАНЫ!")
    exit(0)

# Подключаемся к FTP с retry
print("\n🔌 Подключение к FTP...")
import time
for attempt in range(5):
    try:
        ftp = FTP_TLS(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()
        ftp.cwd(FTP_DIR)
        print("✅ Подключено")
        break
    except Exception as e:
        print(f"⚠️  Попытка {attempt+1}/5 не удалась: {str(e)[:50]}")
        if attempt < 4:
            time.sleep(5)
        else:
            raise

# Обрабатываем батчами
print(f"\n🗜️  Обрабатываю батчами по {BATCH_SIZE} файлов...")
print("   (прогресс после каждого файла)\n")

total_success = 0
total_errors = 0
total_original = 0
total_compressed = 0
resized_count = 0

batch_num = 1
for i in range(0, len(remaining_files), BATCH_SIZE):
    batch = remaining_files[i:i+BATCH_SIZE]
    print(f"\n{'='*80}")
    print(f"📦 БАТЧ #{batch_num} ({i+1}-{min(i+BATCH_SIZE, len(remaining_files))} из {len(remaining_files):,})")
    print(f"{'='*80}\n")
    
    for j, file_info in enumerate(batch, 1):
        filename = file_info['filename']
        current_num = i + j
        
        try:
            # Скачиваем PNG
            bio = io.BytesIO()
            ftp.retrbinary(f'RETR {filename}', bio.write)
            bio.seek(0)
            
            if len(bio.getvalue()) == 0:
                raise Exception("Файл пустой или не скачался")
            
            # Открываем изображение
            img = Image.open(bio)
            original_size = len(bio.getvalue())
            total_original += original_size
            
            # Ресайз если нужно
            width, height = img.size
            was_resized = False
            if max(width, height) > 1920:
                if width > height:
                    img = img.resize((1920, int(height * (1920 / width))), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((int(width * (1920 / height)), 1920), Image.Resampling.LANCZOS)
                was_resized = True
                resized_count += 1
            
            # Конвертируем в WebP
            webp_bio = io.BytesIO()
            img.save(webp_bio, 'WEBP', quality=85)
            compressed_size = len(webp_bio.getvalue())
            total_compressed += compressed_size
            
            # Загружаем WebP
            webp_filename = filename.replace('.png', '.webp')
            webp_bio.seek(0)
            ftp.storbinary(f'STOR {webp_filename}', webp_bio)
            
            total_success += 1
            processed_files.add(filename)
            
            savings = (1 - compressed_size/original_size)*100 if original_size > 0 else 0
            resize_mark = "📐" if was_resized else ""
            print(f"   [{current_num}/{len(remaining_files)}] ✅ {resize_mark} {filename[:40]}... ({savings:.0f}% ↓)")
        
        except Exception as e:
            total_errors += 1
            processed_files.add(filename)
            print(f"   [{current_num}/{len(remaining_files)}] ❌ {filename[:40]}... - {str(e)[:50]}")
    
    # Сохраняем прогресс после каждого батча
    with open(PROGRESS_FILE, 'w') as f:
        json.dump({
            'processed': list(processed_files),
            'total_success': total_success,
            'total_errors': total_errors,
            'total_original_mb': total_original / (1024*1024),
            'total_compressed_mb': total_compressed / (1024*1024),
            'resized_count': resized_count
        }, f)
    
    batch_progress = (current_num / len(remaining_files)) * 100
    print(f"\n💾 Прогресс: {total_success} успешно, {total_errors} ошибок ({batch_progress:.1f}% завершено)")
    batch_num += 1

ftp.quit()

# Финальный отчет
savings_mb = (total_original - total_compressed) / (1024*1024)
savings_gb = savings_mb / 1024
compression_ratio = (1 - total_compressed/total_original)*100 if total_original > 0 else 0

print("\n" + "="*80)
print("📊 ИТОГОВЫЙ ОТЧЕТ")
print("="*80)
print(f"\n✅ Успешно обработано: {total_success:,}")
print(f"   Из них с ресайзом: {resized_count:,}")
print(f"❌ Ошибок: {total_errors:,}")
print(f"\n💾 Экономия:")
print(f"   Было: {total_original/(1024*1024):.2f} MB ({total_original/(1024*1024*1024):.2f} GB)")
print(f"   Стало: {total_compressed/(1024*1024):.2f} MB ({total_compressed/(1024*1024*1024):.2f} GB)")
print(f"   Сохранено: {savings_mb:.2f} MB ({savings_gb:.2f} GB)")
print(f"   Коэффициент сжатия: {compression_ratio:.1f}%")
if total_success > 0:
    print(f"\n📊 Средняя экономия на файл: {savings_mb/total_success:.2f} MB")
print("="*80)


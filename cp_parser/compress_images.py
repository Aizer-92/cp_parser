#!/usr/bin/env python3
"""
Сжатие больших изображений на S3 (>1MB)
Создаёт WebP версии с максимальным разрешением 1920px
"""
import sys
import os
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
import boto3
from botocore.client import Config

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# S3 credentials (Beget Cloud Storage)
S3_ENDPOINT = "https://s3.ru1.storage.beget.cloud"
S3_ACCESS_KEY = "LH3T0JG5BYBX8HMPNC2B"
S3_SECRET_KEY = "XTuAtdL78ZlvB4ydG1WKCzGPBRXlLvfqSEBXYj8J"
S3_BUCKET = "73d16f7545b3-promogoods"
S3_REGION = "ru-1"

# Настройки сжатия
MAX_DIMENSION = 1920  # макс размер по большей стороне
WEBP_QUALITY = 85     # качество WebP (0-100)
MIN_SIZE_MB = 1.0     # сжимать только файлы > 1 MB

def init_s3():
    """Инициализация S3 клиента"""
    return boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=S3_REGION,
        config=Config(signature_version='s3v4')
    )

def download_image(url):
    """Скачивание изображения по URL"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))

def compress_image(img):
    """
    Сжатие изображения:
    1. Изменение размера до MAX_DIMENSION по большей стороне
    2. Конвертация в WebP с качеством WEBP_QUALITY
    """
    # Изменяем размер если больше MAX_DIMENSION
    width, height = img.size
    max_side = max(width, height)
    
    if max_side > MAX_DIMENSION:
        scale = MAX_DIMENSION / max_side
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f"      Изменён размер: {width}x{height} → {new_width}x{new_height}")
    
    # Конвертируем в RGB если есть альфа-канал
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Сохраняем в WebP
    output = BytesIO()
    img.save(output, format='WebP', quality=WEBP_QUALITY, method=6)
    output.seek(0)
    
    return output

def upload_to_s3(s3_client, file_data, s3_key):
    """Загрузка файла на S3"""
    s3_client.upload_fileobj(
        file_data,
        S3_BUCKET,
        s3_key,
        ExtraArgs={'ContentType': 'image/webp'}
    )

def process_images(limit=20, test_mode=True):
    """
    Обработка изображений
    
    Args:
        limit: количество изображений для обработки
        test_mode: если True, не обновляет БД и не удаляет оригиналы
    """
    print(f"\n{'='*80}")
    print(f"🖼️  СЖАТИЕ БОЛЬШИХ ИЗОБРАЖЕНИЙ")
    print(f"{'='*80}")
    print(f"Режим: {'ТЕСТ' if test_mode else 'ПРОДАКШН'}")
    print(f"Лимит: {limit} изображений")
    print(f"Мин. размер: {MIN_SIZE_MB} MB")
    print(f"Макс. разрешение: {MAX_DIMENSION}px")
    print(f"Качество WebP: {WEBP_QUALITY}")
    print(f"{'='*80}\n")
    
    db = PostgreSQLManager()
    s3 = init_s3()
    
    with db.get_session() as session:
        # Получаем изображения для обработки
        images = session.execute(
            text("""
                SELECT 
                    pi.id,
                    pi.image_url,
                    pi.image_filename,
                    pi.product_id
                FROM product_images pi
                WHERE pi.image_url IS NOT NULL
                ORDER BY RANDOM()
                LIMIT :limit
            """),
            {'limit': limit * 2}  # берём с запасом, т.к. будем фильтровать по размеру
        ).fetchall()
        
        print(f"📥 Получено {len(images)} кандидатов для обработки\n")
        
        processed = 0
        skipped = 0
        errors = 0
        total_saved_mb = 0
        
        for img_id, url, filename, product_id in images:
            if processed >= limit:
                break
                
            try:
                # Проверяем размер файла
                head_response = requests.head(url, timeout=5)
                if head_response.status_code != 200:
                    print(f"❌ #{img_id}: Файл недоступен")
                    errors += 1
                    continue
                
                original_size = int(head_response.headers.get('Content-Length', 0))
                original_size_mb = original_size / 1024 / 1024
                
                # Пропускаем маленькие файлы
                if original_size_mb < MIN_SIZE_MB:
                    skipped += 1
                    continue
                
                print(f"🔄 [{processed + 1}/{limit}] {filename}")
                print(f"   Оригинал: {original_size_mb:.2f} MB")
                
                # Скачиваем и сжимаем
                img = download_image(url)
                print(f"   Размер: {img.size[0]}x{img.size[1]}")
                
                compressed = compress_image(img)
                compressed_size = len(compressed.getvalue())
                compressed_size_mb = compressed_size / 1024 / 1024
                
                # Новое имя файла (.webp)
                new_filename = filename.rsplit('.', 1)[0] + '.webp'
                s3_key = f"images/{new_filename}"
                
                print(f"   Сжато: {compressed_size_mb:.2f} MB ({compressed_size_mb / original_size_mb * 100:.1f}%)")
                print(f"   Экономия: {original_size_mb - compressed_size_mb:.2f} MB")
                
                # Загружаем на S3
                if not test_mode:
                    upload_to_s3(s3, compressed, s3_key)
                    new_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{s3_key}"
                    
                    # Обновляем БД
                    session.execute(
                        text("""
                            UPDATE product_images
                            SET 
                                image_filename = :new_filename,
                                image_url = :new_url
                            WHERE id = :img_id
                        """),
                        {
                            'new_filename': new_filename,
                            'new_url': new_url,
                            'img_id': img_id
                        }
                    )
                    session.commit()
                    print(f"   ✅ Загружено на S3 и обновлено в БД")
                else:
                    print(f"   ℹ️  ТЕСТ: Загрузка и обновление пропущены")
                
                total_saved_mb += (original_size_mb - compressed_size_mb)
                processed += 1
                print()
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}\n")
                errors += 1
                continue
        
        print(f"\n{'='*80}")
        print(f"✅ Обработано: {processed}")
        print(f"⏭️  Пропущено (маленькие): {skipped}")
        print(f"❌ Ошибок: {errors}")
        print(f"💾 Общая экономия: {total_saved_mb:.2f} MB")
        print(f"{'='*80}\n")

if __name__ == '__main__':
    # Тестовый запуск на 20 файлах
    process_images(limit=20, test_mode=True)


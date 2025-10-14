#!/usr/bin/env python3
"""
Сжатие больших изображений на S3 - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""
import sys
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
import boto3
from botocore.client import Config
from datetime import datetime

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# S3 credentials
S3_ENDPOINT = "https://s3.ru1.storage.beget.cloud"
S3_ACCESS_KEY = "RECD00AQJIM4300MLJ0W"
S3_SECRET_KEY = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
S3_BUCKET = "73d16f7545b3-promogoods"
S3_REGION = "ru1"

# Настройки
MAX_DIMENSION = 1920
WEBP_QUALITY = 85
MIN_SIZE_MB = 1.0

print(f"\n{'='*80}")
print(f"🖼️  СЖАТИЕ БОЛЬШИХ ИЗОБРАЖЕНИЙ")
print(f"{'='*80}")
print(f"Мин. размер: {MIN_SIZE_MB} MB | Макс. разрешение: {MAX_DIMENSION}px | Качество: {WEBP_QUALITY}")
print(f"{'='*80}\n")

def compress_image(img):
    """Сжатие изображения в WebP с изменением размера"""
    original_size = img.size
    width, height = img.size
    max_side = max(width, height)
    
    resized = False
    if max_side > MAX_DIMENSION:
        scale = MAX_DIMENSION / max_side
        new_width = int(width * scale)
        new_height = int(height * scale)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized = True
    
    # Конвертируем в RGB если есть альфа-канал
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    # Сохраняем в WebP и получаем bytes
    output = BytesIO()
    img.save(output, format='WebP', quality=WEBP_QUALITY, method=6)
    webp_bytes = output.getvalue()  # ВАЖНО: получаем bytes ОДИН РАЗ
    
    return webp_bytes, original_size, img.size, resized

# Инициализация
db = PostgreSQLManager()
s3 = boto3.client(
    's3',
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT,
    config=boto3.session.Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'}
    )
)

start_time = datetime.now()
processed = 0
skipped = 0
errors = 0
total_saved_mb = 0

print(f"🚀 Начинаем обработку...\n")

with db.get_session() as session:
    offset = 0
    chunk_size = 100
    
    while True:
        images = session.execute(
            text("""
                SELECT id, image_url, image_filename
                FROM product_images
                WHERE image_url IS NOT NULL
                AND image_filename NOT LIKE '%.webp'
                ORDER BY id
                LIMIT :chunk OFFSET :offset
            """),
            {'chunk': chunk_size, 'offset': offset}
        ).fetchall()
        
        if not images:
            break
        
        for img_id, url, filename in images:
            try:
                # Проверка размера
                head = requests.head(url, timeout=5)
                if head.status_code != 200:
                    errors += 1
                    continue
                
                size_mb = int(head.headers.get('Content-Length', 0)) / 1024 / 1024
                if size_mb < MIN_SIZE_MB:
                    skipped += 1
                    continue
                
                # Скачиваем и сжимаем
                response = requests.get(url, timeout=30)
                img = Image.open(BytesIO(response.content))
                webp_bytes, orig_size, new_size, was_resized = compress_image(img)
                
                # Загружаем на S3 используя put_object (более надёжно чем upload_fileobj)
                new_filename = filename.rsplit('.', 1)[0] + '.webp'
                s3_key = f"images/{new_filename}"
                
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=s3_key,
                    Body=webp_bytes,
                    ContentType='image/webp'
                )
                
                new_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{s3_key}"
                
                # Обновляем БД
                session.execute(
                    text("UPDATE product_images SET image_filename = :fn, image_url = :url WHERE id = :id"),
                    {'fn': new_filename, 'url': new_url, 'id': img_id}
                )
                session.commit()
                
                compressed_mb = len(webp_bytes) / 1024 / 1024
                saved_mb = size_mb - compressed_mb
                total_saved_mb += saved_mb
                processed += 1
                
                elapsed = (datetime.now() - start_time).total_seconds()
                speed = processed / elapsed if elapsed > 0 else 0
                
                resize_info = f" {orig_size[0]}x{orig_size[1]}→{new_size[0]}x{new_size[1]}" if was_resized else ""
                print(f"✅ [{processed}] {filename[:45]:<45}{resize_info:<20} | {size_mb:.2f}→{compressed_mb:.2f}MB | Σ={total_saved_mb:.1f}MB | {speed:.1f}/s")
                
            except Exception as e:
                errors += 1
                error_msg = str(e)[:80]
                print(f"❌ [{errors}] {filename[:45]}: {error_msg}")
                continue
        
        offset += chunk_size
        
        if offset % 1000 == 0:
            print(f"\n📊 Проверено {offset:,} | Обработано: {processed} | Пропущено: {skipped} | Ошибок: {errors}\n")

print(f"\n{'='*80}")
print(f"✅ ЗАВЕРШЕНО")
print(f"   Обработано: {processed:,}")
print(f"   Пропущено: {skipped:,}")
print(f"   Ошибок: {errors:,}")
print(f"   Экономия: {total_saved_mb:.2f} MB ({total_saved_mb/1024:.2f} GB)")
total_time = (datetime.now() - start_time).total_seconds()
print(f"   Время: {int(total_time//60)}м {int(total_time%60)}с")
print(f"{'='*80}\n")


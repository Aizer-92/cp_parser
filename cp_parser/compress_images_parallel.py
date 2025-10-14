#!/usr/bin/env python3
"""
Сжатие больших изображений на S3 - МНОГОПОТОЧНАЯ ВЕРСИЯ
"""
import sys
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
import boto3
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
NUM_WORKERS = 8  # Количество параллельных потоков

# Глобальные счётчики (потокобезопасные)
lock = threading.Lock()
stats = {
    'processed': 0,
    'skipped': 0,
    'errors': 0,
    'total_saved_mb': 0.0
}

print(f"\n{'='*80}")
print(f"🖼️  МНОГОПОТОЧНОЕ СЖАТИЕ ИЗОБРАЖЕНИЙ")
print(f"{'='*80}")
print(f"Потоков: {NUM_WORKERS} | Мин. размер: {MIN_SIZE_MB} MB | Качество: {WEBP_QUALITY}")
print(f"{'='*80}\n")

def create_s3_client():
    """Создание S3 клиента (для каждого потока свой)"""
    return boto3.client(
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

def compress_image(img):
    """Сжатие изображения в WebP"""
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
    
    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    
    output = BytesIO()
    img.save(output, format='WebP', quality=WEBP_QUALITY, method=6)
    webp_bytes = output.getvalue()
    
    return webp_bytes, original_size, img.size, resized

def process_single_image(img_data):
    """Обработка одного изображения (выполняется в отдельном потоке)"""
    img_id, url, filename = img_data
    
    try:
        # Свой S3 клиент для каждого потока
        s3 = create_s3_client()
        
        # Проверка размера
        head = requests.head(url, timeout=5)
        if head.status_code != 200:
            return {'status': 'error', 'filename': filename, 'error': 'File not accessible'}
        
        size_mb = int(head.headers.get('Content-Length', 0)) / 1024 / 1024
        if size_mb < MIN_SIZE_MB:
            return {'status': 'skipped', 'filename': filename}
        
        # Скачиваем и сжимаем
        response = requests.get(url, timeout=30)
        img = Image.open(BytesIO(response.content))
        webp_bytes, orig_size, new_size, was_resized = compress_image(img)
        
        # Загружаем на S3
        new_filename = filename.rsplit('.', 1)[0] + '.webp'
        s3_key = f"images/{new_filename}"
        
        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=webp_bytes,
            ContentType='image/webp'
        )
        
        new_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{s3_key}"
        
        # Обновляем БД (с отдельным подключением)
        db = PostgreSQLManager()
        with db.get_session() as session:
            session.execute(
                text("UPDATE product_images SET image_filename = :fn, image_url = :url WHERE id = :id"),
                {'fn': new_filename, 'url': new_url, 'id': img_id}
            )
            session.commit()
        
        compressed_mb = len(webp_bytes) / 1024 / 1024
        saved_mb = size_mb - compressed_mb
        
        return {
            'status': 'success',
            'filename': filename,
            'orig_size': orig_size,
            'new_size': new_size,
            'resized': was_resized,
            'size_mb': size_mb,
            'compressed_mb': compressed_mb,
            'saved_mb': saved_mb
        }
        
    except Exception as e:
        return {'status': 'error', 'filename': filename, 'error': str(e)[:80]}

# Основной процесс
start_time = datetime.now()
db = PostgreSQLManager()

print(f"🚀 Начинаем параллельную обработку...\n")

with db.get_session() as session:
    offset = 0
    chunk_size = 500  # Больший размер батча для параллельной обработки
    
    while True:
        # Получаем батч изображений
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
        
        # Обрабатываем батч параллельно
        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(process_single_image, img): img for img in images}
            
            for future in as_completed(futures):
                result = future.result()
                
                with lock:
                    if result['status'] == 'success':
                        stats['processed'] += 1
                        stats['total_saved_mb'] += result['saved_mb']
                        
                        elapsed = (datetime.now() - start_time).total_seconds()
                        speed = stats['processed'] / elapsed if elapsed > 0 else 0
                        
                        resize_info = ""
                        if result['resized']:
                            resize_info = f" {result['orig_size'][0]}x{result['orig_size'][1]}→{result['new_size'][0]}x{result['new_size'][1]}"
                        
                        print(f"✅ [{stats['processed']}] {result['filename'][:45]:<45}{resize_info:<20} | {result['size_mb']:.2f}→{result['compressed_mb']:.2f}MB | Σ={stats['total_saved_mb']:.1f}MB | {speed:.1f}/s")
                        
                    elif result['status'] == 'skipped':
                        stats['skipped'] += 1
                        
                    elif result['status'] == 'error':
                        stats['errors'] += 1
                        print(f"❌ [{stats['errors']}] {result['filename'][:45]}: {result.get('error', 'Unknown')}")
        
        offset += chunk_size
        
        if offset % 2000 == 0:
            print(f"\n📊 Проверено {offset:,} | Обработано: {stats['processed']} | Пропущено: {stats['skipped']} | Ошибок: {stats['errors']}\n")

# Финальная статистика
print(f"\n{'='*80}")
print(f"✅ ЗАВЕРШЕНО")
print(f"   Обработано: {stats['processed']:,}")
print(f"   Пропущено: {stats['skipped']:,}")
print(f"   Ошибок: {stats['errors']:,}")
print(f"   Экономия: {stats['total_saved_mb']:.2f} MB ({stats['total_saved_mb']/1024:.2f} GB)")
total_time = (datetime.now() - start_time).total_seconds()
print(f"   Время: {int(total_time//60)}м {int(total_time%60)}с")
print(f"   Скорость: {stats['processed']/total_time:.2f} изображений/сек")
print(f"{'='*80}\n")


#!/usr/bin/env python3
"""
Массовое сжатие всех больших изображений (>1MB) на S3
Создаёт WebP версии, обновляет БД, оставляет оригиналы как backup
"""
import sys
import os
from pathlib import Path
import requests
from io import BytesIO
from PIL import Image
import boto3
from botocore.client import Config
from datetime import datetime
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

# S3 credentials (Beget Cloud Storage)
S3_ENDPOINT = "https://s3.ru1.storage.beget.cloud"
S3_ACCESS_KEY = "RECD00AQJIM4300MLJ0W"
S3_SECRET_KEY = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
S3_BUCKET = "73d16f7545b3-promogoods"
S3_REGION = "ru1"

# Настройки сжатия
MAX_DIMENSION = 1920  # макс размер по большей стороне
WEBP_QUALITY = 85     # качество WebP (0-100)
MIN_SIZE_MB = 1.0     # сжимать только файлы > 1 MB
BATCH_SIZE = 50       # размер батча перед коммитом

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
    original_size = img.size
    
    # Изменяем размер если больше MAX_DIMENSION
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
    
    # Сохраняем в WebP
    output = BytesIO()
    img.save(output, format='WebP', quality=WEBP_QUALITY, method=6)
    output.seek(0)
    
    return output, original_size, img.size, resized

def upload_to_s3(s3_client, file_data, s3_key):
    """Загрузка файла на S3"""
    file_data.seek(0)  # Важно: сброс позиции перед загрузкой
    s3_client.upload_fileobj(
        file_data,
        S3_BUCKET,
        s3_key,
        ExtraArgs={'ContentType': 'image/webp'}
    )

def process_all_images():
    """
    Массовая обработка всех больших изображений
    """
    log_file = Path("compression_log.txt")
    
    print(f"\n{'='*80}")
    print(f"🖼️  МАССОВОЕ СЖАТИЕ БОЛЬШИХ ИЗОБРАЖЕНИЙ")
    print(f"{'='*80}")
    print(f"Режим: ПРОДАКШН")
    print(f"Мин. размер: {MIN_SIZE_MB} MB")
    print(f"Макс. разрешение: {MAX_DIMENSION}px")
    print(f"Качество WebP: {WEBP_QUALITY}")
    print(f"Размер батча: {BATCH_SIZE}")
    print(f"Лог: {log_file}")
    print(f"{'='*80}\n")
    
    db = PostgreSQLManager()
    s3 = init_s3()
    
    start_time = datetime.now()
    
    with db.get_session() as session:
        # Получаем ВСЕ изображения (будем фильтровать по размеру на лету)
        total_images = session.execute(
            text("""
                SELECT COUNT(*)
                FROM product_images
                WHERE image_url IS NOT NULL
                AND image_filename NOT LIKE '%.webp'
            """)
        ).scalar()
        
        print(f"📊 Всего изображений в БД (не WebP): {total_images:,}\n")
        print(f"🔍 Начинаем проверку размеров и сжатие...\n")
        
        processed = 0
        skipped_small = 0
        skipped_webp = 0
        errors = 0
        total_saved_mb = 0
        batch_updates = []
        
        # Обрабатываем порциями
        offset = 0
        chunk_size = 100
        
        with open(log_file, 'w', encoding='utf-8') as log:
            log.write(f"Compression Log - {datetime.now()}\n")
            log.write(f"{'='*80}\n\n")
            
            while True:
                # Получаем очередную порцию
                images = session.execute(
                    text("""
                        SELECT 
                            pi.id,
                            pi.image_url,
                            pi.image_filename,
                            pi.product_id
                        FROM product_images pi
                        WHERE pi.image_url IS NOT NULL
                        AND pi.image_filename NOT LIKE '%.webp'
                        ORDER BY pi.id
                        LIMIT :chunk_size OFFSET :offset
                    """),
                    {'chunk_size': chunk_size, 'offset': offset}
                ).fetchall()
                
                if not images:
                    break
                
                for img_id, url, filename, product_id in images:
                    try:
                        # Проверяем размер файла
                        head_response = requests.head(url, timeout=5)
                        if head_response.status_code != 200:
                            errors += 1
                            log.write(f"ERROR: {filename} - File not accessible\n")
                            continue
                        
                        original_size = int(head_response.headers.get('Content-Length', 0))
                        original_size_mb = original_size / 1024 / 1024
                        
                        # Пропускаем маленькие файлы
                        if original_size_mb < MIN_SIZE_MB:
                            skipped_small += 1
                            continue
                        
                        # Скачиваем и сжимаем
                        img = download_image(url)
                        compressed, orig_size, new_size, was_resized = compress_image(img)
                        compressed_size = len(compressed.getvalue())
                        compressed_size_mb = compressed_size / 1024 / 1024
                        
                        # Новое имя файла (.webp)
                        new_filename = filename.rsplit('.', 1)[0] + '.webp'
                        s3_key = f"images/{new_filename}"
                        
                        # Загружаем на S3
                        upload_to_s3(s3, compressed, s3_key)
                        new_url = f"{S3_ENDPOINT}/{S3_BUCKET}/{s3_key}"
                        
                        # Добавляем в батч для обновления
                        batch_updates.append({
                            'img_id': img_id,
                            'new_filename': new_filename,
                            'new_url': new_url
                        })
                        
                        # Коммитим батч если достигли размера
                        if len(batch_updates) >= BATCH_SIZE:
                            for upd in batch_updates:
                                session.execute(
                                    text("""
                                        UPDATE product_images
                                        SET 
                                            image_filename = :new_filename,
                                            image_url = :new_url
                                        WHERE id = :img_id
                                    """),
                                    upd
                                )
                            session.commit()
                            batch_updates = []
                        
                        saved_mb = original_size_mb - compressed_size_mb
                        total_saved_mb += saved_mb
                        processed += 1
                        
                        # Прогресс
                        elapsed = (datetime.now() - start_time).total_seconds()
                        speed = processed / elapsed if elapsed > 0 else 0
                        
                        status = f"✅ [{processed}] {filename}"
                        if was_resized:
                            status += f" {orig_size[0]}x{orig_size[1]}→{new_size[0]}x{new_size[1]}"
                        status += f" | {original_size_mb:.2f}MB → {compressed_size_mb:.2f}MB ({compressed_size_mb/original_size_mb*100:.1f}%) | Σ={total_saved_mb:.1f}MB | {speed:.1f}img/s"
                        
                        print(status)
                        log.write(status + '\n')
                        
                        # Пауза чтобы не перегрузить S3
                        if processed % 10 == 0:
                            time.sleep(0.5)
                        
                    except Exception as e:
                        errors += 1
                        error_msg = f"❌ ERROR: {filename} - {str(e)}"
                        print(error_msg)
                        log.write(error_msg + '\n')
                        continue
                
                offset += chunk_size
                
                # Периодически показываем статус
                if offset % 1000 == 0:
                    print(f"\n📊 Прогресс: проверено {offset}/{total_images:,} ({offset/total_images*100:.1f}%)")
                    print(f"   Обработано: {processed} | Пропущено: {skipped_small} | Ошибок: {errors}\n")
            
            # Коммитим остаток батча
            if batch_updates:
                for upd in batch_updates:
                    session.execute(
                        text("""
                            UPDATE product_images
                            SET 
                                image_filename = :new_filename,
                                image_url = :new_url
                            WHERE id = :img_id
                        """),
                        upd
                    )
                session.commit()
            
            # Финальная статистика
            total_time = (datetime.now() - start_time).total_seconds()
            
            summary = f"""
{'='*80}
✅ ЗАВЕРШЕНО
{'='*80}
Всего обработано: {processed:,}
Пропущено (маленькие): {skipped_small:,}
Ошибок: {errors:,}
Общая экономия: {total_saved_mb:.2f} MB ({total_saved_mb/1024:.2f} GB)
Время работы: {int(total_time//60)}м {int(total_time%60)}с
Скорость: {processed/total_time:.2f} изображений/сек
{'='*80}
"""
            print(summary)
            log.write(summary)

if __name__ == '__main__':
    try:
        process_all_images()
    except KeyboardInterrupt:
        print("\n\n⚠️  Остановлено пользователем\n")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}\n")
        import traceback
        traceback.print_exc()


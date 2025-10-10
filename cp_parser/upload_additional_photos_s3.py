#!/usr/bin/env python3
"""
Загрузка ТОЛЬКО дополнительных фото (с суффиксами _1_, _2_, _3_, _4_) на S3
Основные фото (без суффиксов) уже загружены ранее
Использует boto3 вместо FTP для стабильности
"""

import sys
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from sqlalchemy import text
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

class AdditionalPhotosS3Uploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.storage_dir = Path('storage/images')
        
        # S3 настройки (Beget)
        self.s3_client = boto3.client(
            's3',
            endpoint_url='https://s3.ru1.storage.beget.cloud',
            aws_access_key_id='RECD00AQJIM4300MLJ0W',
            aws_secret_access_key='FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
        )
        
        self.bucket_name = '73d16f7545b3-promogoods'
        self.s3_prefix = 'images/'
        
        self.stats_lock = Lock()
        self.uploaded = 0
        self.skipped = 0
        self.errors = 0
    
    def get_additional_images(self):
        """Получить список дополнительных изображений (с суффиксами)"""
        with open('template_4_perfect_ids.txt', 'r') as f:
            project_ids = [int(line.strip()) for line in f if line.strip()]
        
        with self.db.get_session() as session:
            # Получаем ВСЕ изображения из Шаблона 4
            result = session.execute(text("""
                SELECT 
                    pi.id,
                    pi.image_filename,
                    p.project_id
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id = ANY(:ids)
                AND (pi.image_url IS NULL OR pi.image_url = '')
                ORDER BY pi.id
            """), {'ids': project_ids}).fetchall()
            
            # Фильтруем: только с суффиксами _1_, _2_, _3_ и т.д.
            filtered = []
            for row in result:
                img_id, filename = row[0], row[1]
                parts = filename.replace('.png', '').split('_')
                
                # Проверяем: есть ли цифра перед хешем
                if len(parts) >= 4:
                    try:
                        int(parts[-2])  # Если это число - значит суффикс есть
                        filtered.append((img_id, filename))
                    except ValueError:
                        pass  # Нет суффикса - пропускаем
            
            return filtered
    
    def upload_file(self, img_id, filename):
        """Загружает один файл на S3"""
        try:
            filepath = self.storage_dir / filename
            
            if not filepath.exists():
                with self.stats_lock:
                    self.skipped += 1
                return False, f"Файл не найден: {filename}"
            
            # Загружаем на S3
            s3_key = f"{self.s3_prefix}{filename}"
            
            self.s3_client.upload_file(
                str(filepath),
                self.bucket_name,
                s3_key,
                ExtraArgs={'ACL': 'public-read'}
            )
            
            # URL файла
            url = f"https://s3.ru1.storage.beget.cloud/{self.bucket_name}/{s3_key}"
            
            # Обновляем БД
            with self.db.get_session() as session:
                session.execute(text("""
                    UPDATE product_images 
                    SET image_url = :url 
                    WHERE id = :img_id
                """), {'url': url, 'img_id': img_id})
                session.commit()
            
            with self.stats_lock:
                self.uploaded += 1
            
            return True, url
            
        except ClientError as e:
            with self.stats_lock:
                self.errors += 1
            return False, f"S3 error: {str(e)}"
        except Exception as e:
            with self.stats_lock:
                self.errors += 1
            return False, str(e)
    
    def run(self, max_workers=10):
        """Запускает многопоточную загрузку"""
        images = self.get_additional_images()
        total = len(images)
        
        print("=" * 80)
        print("📤 ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ ФОТО НА S3")
        print("=" * 80)
        print(f"\n📊 Найдено дополнительных фото: {total:,}")
        print(f"🔧 Потоков: {max_workers}")
        print(f"📁 S3: {self.bucket_name}/{self.s3_prefix}")
        print(f"\n{'='*80}\n")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.upload_file, img_id, filename): (img_id, filename)
                for img_id, filename in images
            }
            
            for idx, future in enumerate(as_completed(futures), 1):
                img_id, filename = futures[future]
                success, result = future.result()
                
                if idx % 10 == 0 or idx == total:
                    elapsed = time.time() - start_time
                    speed = idx / elapsed if elapsed > 0 else 0
                    remaining = (total - idx) / speed if speed > 0 else 0
                    
                    print(f"\r⏳ {idx}/{total} ({idx/total*100:.1f}%) | "
                          f"✅ {self.uploaded} | ⚠️ {self.skipped} | ❌ {self.errors} | "
                          f"⚡ {speed:.1f} файл/сек | ⏱️ ~{remaining/60:.1f} мин",
                          end='', flush=True)
        
        print(f"\n\n{'='*80}")
        print(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
        print(f"   Загружено:  {self.uploaded:,}")
        print(f"   Пропущено:  {self.skipped:,}")
        print(f"   Ошибки:     {self.errors:,}")
        print(f"   Время:      {(time.time() - start_time)/60:.1f} мин")
        print("=" * 80)


if __name__ == '__main__':
    uploader = AdditionalPhotosS3Uploader()
    uploader.run(max_workers=10)


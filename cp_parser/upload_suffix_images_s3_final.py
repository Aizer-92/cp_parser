"""
Загрузка дополнительных изображений с суффиксами (_1_, _2_, _3_) на S3 Beget
"""
import sys
from pathlib import Path
from sqlalchemy import text
import boto3
from botocore.exceptions import ClientError
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

class S3SuffixImageUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.images_dir = Path('storage/images')
        
        # S3 Beget настройки
        self.s3_client = boto3.client(
            's3',
            endpoint_url='https://s3.ru1.storage.beget.cloud',
            aws_access_key_id='TBE6JWQV7YZUVDE45OE1',
            aws_secret_access_key='QbqHyOCEo1xCHhGmgZiIZZNSxiufcRc6pYx0Qhmc',
            region_name='ru-1'
        )
        self.bucket_name = '73d16f7545b3-promogoods'
        self.s3_prefix = 'images/'
        
    def get_suffix_images(self):
        """Получить список изображений с суффиксами"""
        with open('template_4_perfect_ids.txt', 'r') as f:
            project_ids = [int(line.strip()) for line in f if line.strip()]
        
        with self.db.get_session() as session:
            result = session.execute(text("""
                SELECT DISTINCT pi.image_filename
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id = ANY(:ids)
                  AND (
                    pi.image_filename LIKE '%_1_%' OR
                    pi.image_filename LIKE '%_2_%' OR
                    pi.image_filename LIKE '%_3_%'
                  )
                ORDER BY pi.image_filename
            """), {'ids': project_ids}).fetchall()
            
            return [row[0] for row in result]
    
    def check_file_exists(self, filename):
        """Проверить существует ли файл на S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=self.s3_prefix + filename
            )
            return True
        except ClientError:
            return False
    
    def upload_file(self, filename):
        """Загрузить файл на S3"""
        file_path = self.images_dir / filename
        s3_key = self.s3_prefix + filename
        
        try:
            with open(file_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType='image/png'
                )
            return True
        except Exception as e:
            print(f"      Ошибка: {str(e)[:50]}")
            return False
    
    def upload_to_s3(self):
        """Загрузка на S3"""
        filenames = self.get_suffix_images()
        total = len(filenames)
        
        print("=" * 100)
        print(f"📤 ЗАГРУЗКА {total:,} ДОП ИЗОБРАЖЕНИЙ С СУФФИКСАМИ НА S3 BEGET")
        print("=" * 100)
        
        print(f"\n🔌 S3 Endpoint: https://s3.ru1.storage.beget.cloud")
        print(f"📦 Bucket: {self.bucket_name}")
        print(f"📁 Prefix: {self.s3_prefix}")
        
        # Тестовое подключение
        print(f"\n🧪 Тестирую подключение...")
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Подключение успешно!")
        except Exception as e:
            print(f"❌ Ошибка подключения: {str(e)}")
            return
        
        uploaded = 0
        skipped = 0
        errors = 0
        start_time = time.time()
        
        print(f"\n🚀 НАЧИНАЮ ЗАГРУЗКУ:")
        print("-" * 100)
        
        for i, filename in enumerate(filenames, 1):
            try:
                # Проверяем файл локально
                file_path = self.images_dir / filename
                if not file_path.exists():
                    errors += 1
                    if errors <= 5:  # Показываем первые 5 ошибок
                        print(f"   ❌ Файл не найден: {filename}")
                    continue
                
                # Проверяем на S3
                if self.check_file_exists(filename):
                    skipped += 1
                    if i % 100 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ⏭️  [{i:,}/{total:,}] Пропущено: {skipped:,} | "
                              f"Загружено: {uploaded:,} | Ошибок: {errors} | "
                              f"ETA: {eta/60:.1f}мин")
                    continue
                
                # Загружаем
                if self.upload_file(filename):
                    uploaded += 1
                    
                    # Прогресс каждые 50 файлов
                    if uploaded % 50 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ✅ [{i:,}/{total:,}] Загружено: {uploaded:,} | "
                              f"Пропущено: {skipped:,} | Ошибок: {errors} | "
                              f"Скорость: {speed:.1f} файлов/сек | ETA: {eta/60:.1f}мин")
                else:
                    errors += 1
            
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ❌ Ошибка {filename}: {str(e)[:50]}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 100)
        print(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
        print(f"   Загружено:  {uploaded:,}")
        print(f"   Пропущено:  {skipped:,}")
        print(f"   Ошибок:     {errors}")
        print(f"   Время:      {elapsed/60:.1f} минут")
        if elapsed > 0:
            print(f"   Скорость:   {total/elapsed:.1f} файлов/сек")
        print("=" * 100)

if __name__ == "__main__":
    uploader = S3SuffixImageUploader()
    uploader.upload_to_s3()





Загрузка дополнительных изображений с суффиксами (_1_, _2_, _3_) на S3 Beget
"""
import sys
from pathlib import Path
from sqlalchemy import text
import boto3
from botocore.exceptions import ClientError
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

class S3SuffixImageUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.images_dir = Path('storage/images')
        
        # S3 Beget настройки
        self.s3_client = boto3.client(
            's3',
            endpoint_url='https://s3.ru1.storage.beget.cloud',
            aws_access_key_id='TBE6JWQV7YZUVDE45OE1',
            aws_secret_access_key='QbqHyOCEo1xCHhGmgZiIZZNSxiufcRc6pYx0Qhmc',
            region_name='ru-1'
        )
        self.bucket_name = '73d16f7545b3-promogoods'
        self.s3_prefix = 'images/'
        
    def get_suffix_images(self):
        """Получить список изображений с суффиксами"""
        with open('template_4_perfect_ids.txt', 'r') as f:
            project_ids = [int(line.strip()) for line in f if line.strip()]
        
        with self.db.get_session() as session:
            result = session.execute(text("""
                SELECT DISTINCT pi.image_filename
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id = ANY(:ids)
                  AND (
                    pi.image_filename LIKE '%_1_%' OR
                    pi.image_filename LIKE '%_2_%' OR
                    pi.image_filename LIKE '%_3_%'
                  )
                ORDER BY pi.image_filename
            """), {'ids': project_ids}).fetchall()
            
            return [row[0] for row in result]
    
    def check_file_exists(self, filename):
        """Проверить существует ли файл на S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=self.s3_prefix + filename
            )
            return True
        except ClientError:
            return False
    
    def upload_file(self, filename):
        """Загрузить файл на S3"""
        file_path = self.images_dir / filename
        s3_key = self.s3_prefix + filename
        
        try:
            with open(file_path, 'rb') as f:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType='image/png'
                )
            return True
        except Exception as e:
            print(f"      Ошибка: {str(e)[:50]}")
            return False
    
    def upload_to_s3(self):
        """Загрузка на S3"""
        filenames = self.get_suffix_images()
        total = len(filenames)
        
        print("=" * 100)
        print(f"📤 ЗАГРУЗКА {total:,} ДОП ИЗОБРАЖЕНИЙ С СУФФИКСАМИ НА S3 BEGET")
        print("=" * 100)
        
        print(f"\n🔌 S3 Endpoint: https://s3.ru1.storage.beget.cloud")
        print(f"📦 Bucket: {self.bucket_name}")
        print(f"📁 Prefix: {self.s3_prefix}")
        
        # Тестовое подключение
        print(f"\n🧪 Тестирую подключение...")
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Подключение успешно!")
        except Exception as e:
            print(f"❌ Ошибка подключения: {str(e)}")
            return
        
        uploaded = 0
        skipped = 0
        errors = 0
        start_time = time.time()
        
        print(f"\n🚀 НАЧИНАЮ ЗАГРУЗКУ:")
        print("-" * 100)
        
        for i, filename in enumerate(filenames, 1):
            try:
                # Проверяем файл локально
                file_path = self.images_dir / filename
                if not file_path.exists():
                    errors += 1
                    if errors <= 5:  # Показываем первые 5 ошибок
                        print(f"   ❌ Файл не найден: {filename}")
                    continue
                
                # Проверяем на S3
                if self.check_file_exists(filename):
                    skipped += 1
                    if i % 100 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ⏭️  [{i:,}/{total:,}] Пропущено: {skipped:,} | "
                              f"Загружено: {uploaded:,} | Ошибок: {errors} | "
                              f"ETA: {eta/60:.1f}мин")
                    continue
                
                # Загружаем
                if self.upload_file(filename):
                    uploaded += 1
                    
                    # Прогресс каждые 50 файлов
                    if uploaded % 50 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ✅ [{i:,}/{total:,}] Загружено: {uploaded:,} | "
                              f"Пропущено: {skipped:,} | Ошибок: {errors} | "
                              f"Скорость: {speed:.1f} файлов/сек | ETA: {eta/60:.1f}мин")
                else:
                    errors += 1
            
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ❌ Ошибка {filename}: {str(e)[:50]}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 100)
        print(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
        print(f"   Загружено:  {uploaded:,}")
        print(f"   Пропущено:  {skipped:,}")
        print(f"   Ошибок:     {errors}")
        print(f"   Время:      {elapsed/60:.1f} минут")
        if elapsed > 0:
            print(f"   Скорость:   {total/elapsed:.1f} файлов/сек")
        print("=" * 100)

if __name__ == "__main__":
    uploader = S3SuffixImageUploader()
    uploader.upload_to_s3()













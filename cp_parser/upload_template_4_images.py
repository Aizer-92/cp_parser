#!/usr/bin/env python3
"""
Загрузка изображений Шаблона 4 на FTP
"""
import sys
from pathlib import Path
import ftplib
from concurrent.futures import ThreadPoolExecutor
import time
from sqlalchemy import text

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# FTP настройки
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'
FTP_BASE_URL = 'https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/'
LOCAL_IMAGES_DIR = Path('storage/images')
MAX_WORKERS = 3

class ImageUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.uploaded_count = 0
        self.error_count = 0
        
    def upload_file(self, filename):
        """Загружает один файл на FTP"""
        try:
            local_path = LOCAL_IMAGES_DIR / filename
            
            if not local_path.exists():
                return {'success': False, 'error': 'File not found'}
            
            # Подключение к FTP
            ftp = ftplib.FTP_TLS()
            ftp.connect(FTP_HOST, 21, timeout=30)
            ftp.login(FTP_USERNAME, FTP_PASSWORD)
            ftp.prot_p()
            
            # Переходим в директорию
            ftp.cwd(FTP_REMOTE_DIR)
            
            # Загружаем файл
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            ftp.quit()
            
            # Обновляем URL в БД
            image_url = f"{FTP_BASE_URL}{filename}"
            with self.db.get_session() as session:
                session.execute(text("""
                    UPDATE product_images 
                    SET image_url = :url 
                    WHERE image_filename = :filename
                """), {'url': image_url, 'filename': filename})
                session.commit()
            
            self.uploaded_count += 1
            return {'success': True}
            
        except Exception as e:
            self.error_count += 1
            return {'success': False, 'error': str(e)}
    
    def upload_all(self):
        """Загружает все изображения Шаблона 4"""
        # Читаем список проектов
        with open('template_4_perfect_ids.txt', 'r') as f:
            project_ids = [int(line.strip()) for line in f if line.strip()]
        
        print("=" * 80)
        print("📤 ЗАГРУЗКА ИЗОБРАЖЕНИЙ ШАБЛОНА 4 НА FTP")
        print("=" * 80)
        
        # Получаем список файлов для загрузки
        with self.db.get_session() as session:
            images = session.execute(text("""
                SELECT DISTINCT pi.image_filename
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id = ANY(:ids)
                AND (pi.image_url IS NULL OR pi.image_url = '')
            """), {'ids': project_ids}).fetchall()
        
        filenames = [img[0] for img in images]
        
        print(f"\n📊 К загрузке: {len(filenames):,} изображений")
        print(f"🔧 Потоков: {MAX_WORKERS}")
        print("")
        
        start_time = time.time()
        
        # Загружаем в несколько потоков
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(self.upload_file, filenames))
        
        elapsed = time.time() - start_time
        speed = len(filenames) / elapsed if elapsed > 0 else 0
        
        print("")
        print("=" * 80)
        print("📊 РЕЗУЛЬТАТЫ")
        print("=" * 80)
        print(f"✅ Загружено:  {self.uploaded_count:,}")
        print(f"❌ Ошибки:     {self.error_count:,}")
        print(f"⏱️  Время:      {elapsed:.1f} сек")
        print(f"⚡ Скорость:   {speed:.1f} img/s")
        print("=" * 80)

if __name__ == '__main__':
    uploader = ImageUploader()
    uploader.upload_all()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Многопоточная загрузка изображений из 272 проектов через FTP
"""

import sys
from pathlib import Path
import ftplib
from ftplib import FTP_TLS
import time
from sqlalchemy import text
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import db_manager

# Настройки FTP
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'
BASE_URL = 'https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/'

# Локальные настройки
LOCAL_IMAGES_DIR = Path('storage/images')
MAX_WORKERS = 3  # Количество параллельных потоков
UPLOAD_DELAY = 0.1  # Задержка между загрузками
BATCH_SIZE = 10  # Показывать прогресс каждые N файлов

class MultiThreadFTPUploader:
    def __init__(self):
        self.db = db_manager
        self.uploaded_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def get_images_to_upload(self):
        """Получить список изображений из 272 проектов"""
        import re
        
        valid_list = Path('valid_files_list.txt')
        if not valid_list.exists():
            print("❌ Файл valid_files_list.txt не найден!")
            return []
        
        with open(valid_list, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
        
        project_ids = []
        for filename in files:
            match = re.search(r'project_(\d+)_', filename)
            if match:
                project_ids.append(int(match.group(1)))
        
        print(f"📁 Найдено 272 валидных проектов: {len(project_ids)} IDs")
        
        if not project_ids:
            return []
        
        with self.db.get_session() as session:
            placeholders = ','.join([f':{i}' for i in range(len(project_ids))])
            params = {str(i): pid for i, pid in enumerate(project_ids)}
            
            result = session.execute(text(f"""
                SELECT 
                    pi.id,
                    pi.image_filename
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id IN ({placeholders})
                  AND (pi.image_url IS NULL OR pi.image_url = '')
                  AND pi.image_filename IS NOT NULL
                ORDER BY pi.id
            """), params).fetchall()
            
            return [(row[0], row[1]) for row in result]
    
    def upload_single_image(self, image_id, filename, max_retries=3):
        """Загружает одно изображение через FTP (в отдельном потоке)"""
        local_path = LOCAL_IMAGES_DIR / filename
        
        if not local_path.exists():
            return False, f"Файл не найден"
        
        for attempt in range(max_retries):
            ftp = None
            try:
                # Создаем FTP соединение для этого потока
                ftp = FTP_TLS()
                ftp.connect(FTP_HOST, 21, timeout=30)
                ftp.login(FTP_USERNAME, FTP_PASSWORD)
                ftp.prot_p()
                
                # Переходим в папку
                try:
                    ftp.cwd(FTP_REMOTE_DIR)
                except ftplib.error_perm:
                    ftp.mkd(FTP_REMOTE_DIR)
                    ftp.cwd(FTP_REMOTE_DIR)
                
                # Загружаем файл
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                
                ftp.quit()
                
                # Задержка
                time.sleep(UPLOAD_DELAY)
                
                # Формируем URL
                image_url = f"{BASE_URL}{filename}"
                
                # Обновляем БД
                with self.db.get_session() as session:
                    session.execute(text("""
                        UPDATE product_images
                        SET image_url = :image_url, updated_at = :updated_at
                        WHERE id = :image_id
                    """), {
                        'image_id': image_id,
                        'image_url': image_url,
                        'updated_at': datetime.now().isoformat()
                    })
                    session.commit()
                
                with self.lock:
                    self.uploaded_count += 1
                
                return True, None
                
            except ftplib.error_temp as e:
                if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    time.sleep(wait_time)
                    continue
                else:
                    with self.lock:
                        self.failed_count += 1
                    return False, str(e)[:50]
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    with self.lock:
                        self.failed_count += 1
                    return False, str(e)[:50]
            
            finally:
                if ftp:
                    try:
                        ftp.quit()
                    except:
                        pass
        
        with self.lock:
            self.failed_count += 1
        return False, "Max retries exceeded"
    
    def upload_all_images(self):
        """Загрузить все изображения в несколько потоков"""
        print("\n" + "=" * 80)
        print("🚀 МНОГОПОТОЧНАЯ ЗАГРУЗКА ИЗОБРАЖЕНИЙ")
        print("=" * 80)
        
        # Получаем список изображений
        images = self.get_images_to_upload()
        total = len(images)
        
        if total == 0:
            print("\n✅ Все изображения уже загружены!")
            return
        
        print(f"\n📊 Найдено новых изображений: {total:,}")
        print(f"🔄 Потоков: {MAX_WORKERS}")
        print(f"🌍 Хост: {FTP_HOST}")
        print(f"📁 Папка: {FTP_REMOTE_DIR}")
        print()
        
        # Загружаем в несколько потоков
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.upload_single_image, img_id, filename): (i, img_id, filename)
                for i, (img_id, filename) in enumerate(images, 1)
            }
            
            for future in as_completed(futures):
                i, img_id, filename = futures[future]
                
                try:
                    success, error = future.result()
                    
                    if success:
                        if i % BATCH_SIZE == 0 or i == total:
                            elapsed = time.time() - self.start_time
                            speed = self.uploaded_count / elapsed if elapsed > 0 else 0
                            eta = (total - i) / speed if speed > 0 else 0
                            
                            print(f"[{i:>6}/{total}] ✅ {filename[:50]:<50} | "
                                  f"✓ {self.uploaded_count:>5} ✗ {self.failed_count:>3} | "
                                  f"{speed:>4.1f} img/s | ETA: {eta/60:>4.1f}m")
                    else:
                        if self.failed_count <= 10:  # Показываем только первые 10 ошибок
                            print(f"[{i:>6}/{total}] ❌ {filename[:50]:<50} | {error}")
                
                except Exception as e:
                    with self.lock:
                        self.failed_count += 1
                    if self.failed_count <= 10:
                        print(f"[{i:>6}/{total}] ❌ {filename[:50]:<50} | Exception: {str(e)[:30]}")
        
        # Финальный отчет
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 80)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        print("=" * 80)
        print(f"Успешно: {self.uploaded_count}/{total} ({self.uploaded_count/total*100:.1f}%)")
        print(f"Ошибки: {self.failed_count}")
        print(f"Время: {elapsed/60:.1f} минут")
        print(f"Скорость: {self.uploaded_count/elapsed:.1f} изображений/сек")
        print("=" * 80)

def main():
    uploader = MultiThreadFTPUploader()
    uploader.upload_all_images()

if __name__ == '__main__':
    main()






# -*- coding: utf-8 -*-

"""
Многопоточная загрузка изображений из 272 проектов через FTP
"""

import sys
from pathlib import Path
import ftplib
from ftplib import FTP_TLS
import time
from sqlalchemy import text
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, str(Path(__file__).parent))
from database.postgresql_manager import db_manager

# Настройки FTP
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'
BASE_URL = 'https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/'

# Локальные настройки
LOCAL_IMAGES_DIR = Path('storage/images')
MAX_WORKERS = 3  # Количество параллельных потоков
UPLOAD_DELAY = 0.1  # Задержка между загрузками
BATCH_SIZE = 10  # Показывать прогресс каждые N файлов

class MultiThreadFTPUploader:
    def __init__(self):
        self.db = db_manager
        self.uploaded_count = 0
        self.failed_count = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def get_images_to_upload(self):
        """Получить список изображений из 272 проектов"""
        import re
        
        valid_list = Path('valid_files_list.txt')
        if not valid_list.exists():
            print("❌ Файл valid_files_list.txt не найден!")
            return []
        
        with open(valid_list, 'r') as f:
            files = [line.strip() for line in f if line.strip()]
        
        project_ids = []
        for filename in files:
            match = re.search(r'project_(\d+)_', filename)
            if match:
                project_ids.append(int(match.group(1)))
        
        print(f"📁 Найдено 272 валидных проектов: {len(project_ids)} IDs")
        
        if not project_ids:
            return []
        
        with self.db.get_session() as session:
            placeholders = ','.join([f':{i}' for i in range(len(project_ids))])
            params = {str(i): pid for i, pid in enumerate(project_ids)}
            
            result = session.execute(text(f"""
                SELECT 
                    pi.id,
                    pi.image_filename
                FROM product_images pi
                JOIN products p ON pi.product_id = p.id
                WHERE p.project_id IN ({placeholders})
                  AND (pi.image_url IS NULL OR pi.image_url = '')
                  AND pi.image_filename IS NOT NULL
                ORDER BY pi.id
            """), params).fetchall()
            
            return [(row[0], row[1]) for row in result]
    
    def upload_single_image(self, image_id, filename, max_retries=3):
        """Загружает одно изображение через FTP (в отдельном потоке)"""
        local_path = LOCAL_IMAGES_DIR / filename
        
        if not local_path.exists():
            return False, f"Файл не найден"
        
        for attempt in range(max_retries):
            ftp = None
            try:
                # Создаем FTP соединение для этого потока
                ftp = FTP_TLS()
                ftp.connect(FTP_HOST, 21, timeout=30)
                ftp.login(FTP_USERNAME, FTP_PASSWORD)
                ftp.prot_p()
                
                # Переходим в папку
                try:
                    ftp.cwd(FTP_REMOTE_DIR)
                except ftplib.error_perm:
                    ftp.mkd(FTP_REMOTE_DIR)
                    ftp.cwd(FTP_REMOTE_DIR)
                
                # Загружаем файл
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                
                ftp.quit()
                
                # Задержка
                time.sleep(UPLOAD_DELAY)
                
                # Формируем URL
                image_url = f"{BASE_URL}{filename}"
                
                # Обновляем БД
                with self.db.get_session() as session:
                    session.execute(text("""
                        UPDATE product_images
                        SET image_url = :image_url, updated_at = :updated_at
                        WHERE id = :image_id
                    """), {
                        'image_id': image_id,
                        'image_url': image_url,
                        'updated_at': datetime.now().isoformat()
                    })
                    session.commit()
                
                with self.lock:
                    self.uploaded_count += 1
                
                return True, None
                
            except ftplib.error_temp as e:
                if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 3
                    time.sleep(wait_time)
                    continue
                else:
                    with self.lock:
                        self.failed_count += 1
                    return False, str(e)[:50]
            
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    with self.lock:
                        self.failed_count += 1
                    return False, str(e)[:50]
            
            finally:
                if ftp:
                    try:
                        ftp.quit()
                    except:
                        pass
        
        with self.lock:
            self.failed_count += 1
        return False, "Max retries exceeded"
    
    def upload_all_images(self):
        """Загрузить все изображения в несколько потоков"""
        print("\n" + "=" * 80)
        print("🚀 МНОГОПОТОЧНАЯ ЗАГРУЗКА ИЗОБРАЖЕНИЙ")
        print("=" * 80)
        
        # Получаем список изображений
        images = self.get_images_to_upload()
        total = len(images)
        
        if total == 0:
            print("\n✅ Все изображения уже загружены!")
            return
        
        print(f"\n📊 Найдено новых изображений: {total:,}")
        print(f"🔄 Потоков: {MAX_WORKERS}")
        print(f"🌍 Хост: {FTP_HOST}")
        print(f"📁 Папка: {FTP_REMOTE_DIR}")
        print()
        
        # Загружаем в несколько потоков
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(self.upload_single_image, img_id, filename): (i, img_id, filename)
                for i, (img_id, filename) in enumerate(images, 1)
            }
            
            for future in as_completed(futures):
                i, img_id, filename = futures[future]
                
                try:
                    success, error = future.result()
                    
                    if success:
                        if i % BATCH_SIZE == 0 or i == total:
                            elapsed = time.time() - self.start_time
                            speed = self.uploaded_count / elapsed if elapsed > 0 else 0
                            eta = (total - i) / speed if speed > 0 else 0
                            
                            print(f"[{i:>6}/{total}] ✅ {filename[:50]:<50} | "
                                  f"✓ {self.uploaded_count:>5} ✗ {self.failed_count:>3} | "
                                  f"{speed:>4.1f} img/s | ETA: {eta/60:>4.1f}m")
                    else:
                        if self.failed_count <= 10:  # Показываем только первые 10 ошибок
                            print(f"[{i:>6}/{total}] ❌ {filename[:50]:<50} | {error}")
                
                except Exception as e:
                    with self.lock:
                        self.failed_count += 1
                    if self.failed_count <= 10:
                        print(f"[{i:>6}/{total}] ❌ {filename[:50]:<50} | Exception: {str(e)[:30]}")
        
        # Финальный отчет
        elapsed = time.time() - self.start_time
        print("\n" + "=" * 80)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        print("=" * 80)
        print(f"Успешно: {self.uploaded_count}/{total} ({self.uploaded_count/total*100:.1f}%)")
        print(f"Ошибки: {self.failed_count}")
        print(f"Время: {elapsed/60:.1f} минут")
        print(f"Скорость: {self.uploaded_count/elapsed:.1f} изображений/сек")
        print("=" * 80)

def main():
    uploader = MultiThreadFTPUploader()
    uploader.upload_all_images()

if __name__ == '__main__':
    main()










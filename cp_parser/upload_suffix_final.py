"""
Загрузка дополнительных изображений с суффиксами на FTP Beget S3
"""
import sys
from pathlib import Path
from sqlalchemy import text
from ftplib import FTP_TLS
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# FTP настройки
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'

class SuffixImageUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.images_dir = Path('storage/images')
        
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
    
    def upload_to_ftp(self):
        """Загрузка на FTP"""
        filenames = self.get_suffix_images()
        total = len(filenames)
        
        print("=" * 100)
        print(f"📤 ЗАГРУЗКА {total:,} ДОП ИЗОБРАЖЕНИЙ С СУФФИКСАМИ НА FTP")
        print("=" * 100)
        
        print(f"\n🔌 Подключаюсь к {FTP_HOST}...")
        
        try:
            ftp = FTP_TLS()
            ftp.connect(FTP_HOST, 21, timeout=30)
            ftp.login(FTP_USERNAME, FTP_PASSWORD)
            ftp.prot_p()  # Защищенный режим
            ftp.cwd(FTP_REMOTE_DIR)
            
            print(f"✅ Подключен к {FTP_REMOTE_DIR}")
            
            # Получаем список существующих файлов
            print(f"\n📋 Проверяю существующие файлы на FTP...")
            existing_files = set()
            try:
                existing_files = set(ftp.nlst())
                print(f"✅ Найдено {len(existing_files):,} файлов на FTP")
            except:
                print(f"⚠️  Не удалось получить список файлов, буду загружать все")
            
            uploaded = 0
            skipped = 0
            errors = 0
            start_time = time.time()
            
            print(f"\n🚀 НАЧИНАЮ ЗАГРУЗКУ:")
            print("-" * 100)
            
            for i, filename in enumerate(filenames, 1):
                try:
                    # Пропускаем если уже есть
                    if filename in existing_files:
                        skipped += 1
                        if i % 200 == 0:
                            elapsed = time.time() - start_time
                            speed = i / elapsed if elapsed > 0 else 0
                            eta = (total - i) / speed if speed > 0 else 0
                            print(f"   ⏭️  [{i:,}/{total:,}] Пропущено: {skipped:,} | "
                                  f"Загружено: {uploaded:,} | Ошибок: {errors} | "
                                  f"Скорость: {speed:.1f} ф/с | ETA: {eta/60:.1f}мин")
                        continue
                    
                    # Проверяем файл локально
                    file_path = self.images_dir / filename
                    if not file_path.exists():
                        errors += 1
                        if errors <= 5:
                            print(f"   ❌ Файл не найден: {filename}")
                        continue
                    
                    # Загружаем
                    with open(file_path, 'rb') as f:
                        ftp.storbinary(f'STOR {filename}', f)
                    
                    uploaded += 1
                    
                    # Прогресс каждые 100 файлов
                    if uploaded % 100 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ✅ [{i:,}/{total:,}] Загружено: {uploaded:,} | "
                              f"Пропущено: {skipped:,} | Ошибок: {errors} | "
                              f"Скорость: {speed:.1f} ф/с | ETA: {eta/60:.1f}мин")
                
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"   ❌ Ошибка {filename}: {str(e)[:50]}")
            
            ftp.quit()
            
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
            
        except Exception as e:
            print(f"\n❌ Ошибка подключения: {str(e)}")

if __name__ == "__main__":
    uploader = SuffixImageUploader()
    uploader.upload_to_ftp()





Загрузка дополнительных изображений с суффиксами на FTP Beget S3
"""
import sys
from pathlib import Path
from sqlalchemy import text
from ftplib import FTP_TLS
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# FTP настройки
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USERNAME = 'RECD00AQJIM4300MLJ0W'
FTP_PASSWORD = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'

class SuffixImageUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.images_dir = Path('storage/images')
        
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
    
    def upload_to_ftp(self):
        """Загрузка на FTP"""
        filenames = self.get_suffix_images()
        total = len(filenames)
        
        print("=" * 100)
        print(f"📤 ЗАГРУЗКА {total:,} ДОП ИЗОБРАЖЕНИЙ С СУФФИКСАМИ НА FTP")
        print("=" * 100)
        
        print(f"\n🔌 Подключаюсь к {FTP_HOST}...")
        
        try:
            ftp = FTP_TLS()
            ftp.connect(FTP_HOST, 21, timeout=30)
            ftp.login(FTP_USERNAME, FTP_PASSWORD)
            ftp.prot_p()  # Защищенный режим
            ftp.cwd(FTP_REMOTE_DIR)
            
            print(f"✅ Подключен к {FTP_REMOTE_DIR}")
            
            # Получаем список существующих файлов
            print(f"\n📋 Проверяю существующие файлы на FTP...")
            existing_files = set()
            try:
                existing_files = set(ftp.nlst())
                print(f"✅ Найдено {len(existing_files):,} файлов на FTP")
            except:
                print(f"⚠️  Не удалось получить список файлов, буду загружать все")
            
            uploaded = 0
            skipped = 0
            errors = 0
            start_time = time.time()
            
            print(f"\n🚀 НАЧИНАЮ ЗАГРУЗКУ:")
            print("-" * 100)
            
            for i, filename in enumerate(filenames, 1):
                try:
                    # Пропускаем если уже есть
                    if filename in existing_files:
                        skipped += 1
                        if i % 200 == 0:
                            elapsed = time.time() - start_time
                            speed = i / elapsed if elapsed > 0 else 0
                            eta = (total - i) / speed if speed > 0 else 0
                            print(f"   ⏭️  [{i:,}/{total:,}] Пропущено: {skipped:,} | "
                                  f"Загружено: {uploaded:,} | Ошибок: {errors} | "
                                  f"Скорость: {speed:.1f} ф/с | ETA: {eta/60:.1f}мин")
                        continue
                    
                    # Проверяем файл локально
                    file_path = self.images_dir / filename
                    if not file_path.exists():
                        errors += 1
                        if errors <= 5:
                            print(f"   ❌ Файл не найден: {filename}")
                        continue
                    
                    # Загружаем
                    with open(file_path, 'rb') as f:
                        ftp.storbinary(f'STOR {filename}', f)
                    
                    uploaded += 1
                    
                    # Прогресс каждые 100 файлов
                    if uploaded % 100 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ✅ [{i:,}/{total:,}] Загружено: {uploaded:,} | "
                              f"Пропущено: {skipped:,} | Ошибок: {errors} | "
                              f"Скорость: {speed:.1f} ф/с | ETA: {eta/60:.1f}мин")
                
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"   ❌ Ошибка {filename}: {str(e)[:50]}")
            
            ftp.quit()
            
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
            
        except Exception as e:
            print(f"\n❌ Ошибка подключения: {str(e)}")

if __name__ == "__main__":
    uploader = SuffixImageUploader()
    uploader.upload_to_ftp()













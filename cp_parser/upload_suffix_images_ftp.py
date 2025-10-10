"""
Загрузка дополнительных изображений с суффиксами (_1_, _2_, _3_) на FTP
"""
import sys
from pathlib import Path
from sqlalchemy import text
from ftplib import FTP
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

class SuffixImageUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.images_dir = Path('storage/images')
        
        # FTP настройки (Beget FTP)
        self.ftp_host = 'denbak.beget.tech'
        self.ftp_user = 'denbak_promogo'
        self.ftp_pass = 'C0u5EQi&'
        self.ftp_path = '/public_html/images'
        
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
        
        # Подключаемся к FTP
        print(f"\n🔌 Подключаюсь к {self.ftp_host}...")
        ftp = FTP(self.ftp_host)
        ftp.login(self.ftp_user, self.ftp_pass)
        ftp.cwd(self.ftp_path)
        print(f"✅ Подключен к {self.ftp_path}")
        
        # Получаем список существующих файлов
        print(f"\n📋 Проверяю существующие файлы на FTP...")
        existing_files = set(ftp.nlst())
        print(f"✅ Найдено {len(existing_files):,} файлов на FTP")
        
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
                    if i % 100 == 0:
                        elapsed = time.time() - start_time
                        speed = i / elapsed if elapsed > 0 else 0
                        eta = (total - i) / speed if speed > 0 else 0
                        print(f"   ⏭️  [{i:,}/{total:,}] Пропущено: {skipped:,} | "
                              f"Загружено: {uploaded:,} | Ошибок: {errors} | "
                              f"ETA: {eta/60:.1f}мин")
                    continue
                
                # Проверяем наличие файла
                file_path = self.images_dir / filename
                if not file_path.exists():
                    errors += 1
                    print(f"   ❌ Файл не найден: {filename}")
                    continue
                
                # Загружаем
                with open(file_path, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                
                uploaded += 1
                
                # Прогресс каждые 50 файлов
                if uploaded % 50 == 0:
                    elapsed = time.time() - start_time
                    speed = i / elapsed if elapsed > 0 else 0
                    eta = (total - i) / speed if speed > 0 else 0
                    print(f"   ✅ [{i:,}/{total:,}] Загружено: {uploaded:,} | "
                          f"Пропущено: {skipped:,} | Ошибок: {errors} | "
                          f"Скорость: {speed:.1f} файлов/сек | ETA: {eta/60:.1f}мин")
            
            except Exception as e:
                errors += 1
                print(f"   ❌ Ошибка загрузки {filename}: {str(e)[:50]}")
        
        ftp.quit()
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 100)
        print(f"✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
        print(f"   Загружено:  {uploaded:,}")
        print(f"   Пропущено:  {skipped:,}")
        print(f"   Ошибок:     {errors}")
        print(f"   Время:      {elapsed/60:.1f} минут")
        print(f"   Скорость:   {total/elapsed:.1f} файлов/сек")
        print("=" * 100)

if __name__ == "__main__":
    uploader = SuffixImageUploader()
    uploader.upload_to_ftp()


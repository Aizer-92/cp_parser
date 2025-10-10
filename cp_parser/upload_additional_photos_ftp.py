#!/usr/bin/env python3
"""
Загрузка ТОЛЬКО дополнительных фото (с суффиксами _1_, _2_, _3_, _4_) на FTP
Основные фото (без суффиксов) уже загружены ранее
"""

import sys
from pathlib import Path
from ftplib import FTP
from sqlalchemy import text
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

class AdditionalPhotosFTPUploader:
    def __init__(self):
        self.db = PostgreSQLManager()
        self.storage_dir = Path('storage/images')
        
        # FTP настройки (S3-совместимый)
        self.ftp_host = 's3.timeweb.cloud'
        self.ftp_user = 'A79TJRUXGGM2V65LQ6RG'
        self.ftp_pass = 'Q6LBVoVafX39zHKhwGpn0GCbT9MnjZz0cGTgZHl1'
        self.ftp_dir = '/7aace6d0-e0a3d7f2-8b12-447f-bf68-66fcb7a94b79/images'
        
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
            
            # Фильтруем Python-ом: только с суффиксами _1_, _2_, _3_ и т.д.
            # Формат: table_id_Q4_1_hash.png (с суффиксом)
            # Формат: table_id_Q4_hash.png (без суффикса - ПРОПУСКАЕМ)
            
            filtered = []
            for row in result:
                img_id, filename = row[0], row[1]
                parts = filename.replace('.png', '').split('_')
                
                # Проверяем: есть ли цифра перед хешем (предпоследний элемент)
                if len(parts) >= 4:
                    try:
                        int(parts[-2])  # Если это число - значит суффикс есть
                        filtered.append((img_id, filename))
                    except ValueError:
                        pass  # Нет суффикса - пропускаем
            
            return filtered
    
    def upload_file(self, img_id, filename):
        """Загружает один файл на FTP"""
        try:
            filepath = self.storage_dir / filename
            
            if not filepath.exists():
                with self.stats_lock:
                    self.skipped += 1
                return False, f"Файл не найден: {filename}"
            
            # Подключаемся к FTP
            ftp = FTP(self.ftp_host, timeout=30)
            ftp.login(self.ftp_user, self.ftp_pass)
            ftp.cwd(self.ftp_dir)
            
            # Загружаем файл
            with open(filepath, 'rb') as f:
                ftp.storbinary(f'STOR {filename}', f)
            
            ftp.quit()
            
            # URL файла
            url = f"https://s3.timeweb.cloud/7aace6d0-e0a3d7f2-8b12-447f-bf68-66fcb7a94b79/images/{filename}"
            
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
            
        except Exception as e:
            with self.stats_lock:
                self.errors += 1
            return False, str(e)
    
    def run(self, max_workers=10):
        """Запускает многопоточную загрузку"""
        images = self.get_additional_images()
        total = len(images)
        
        print("=" * 80)
        print("📤 ЗАГРУЗКА ДОПОЛНИТЕЛЬНЫХ ФОТО НА FTP")
        print("=" * 80)
        print(f"\n📊 Найдено дополнительных фото: {total:,}")
        print(f"🔧 Потоков: {max_workers}")
        print(f"📁 FTP: {self.ftp_host}{self.ftp_dir}")
        print(f"\n{'='*80}")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.upload_file, img_id, filename): (img_id, filename)
                for img_id, filename in images
            }
            
            for idx, future in enumerate(as_completed(futures), 1):
                img_id, filename = futures[future]
                success, result = future.result()
                
                if idx % 50 == 0 or idx == total:
                    elapsed = time.time() - start_time
                    speed = idx / elapsed if elapsed > 0 else 0
                    remaining = (total - idx) / speed if speed > 0 else 0
                    
                    print(f"\r⏳ {idx}/{total} ({idx/total*100:.1f}%) | "
                          f"✅ {self.uploaded} | ⚠️ {self.skipped} | ❌ {self.errors} | "
                          f"⚡ {speed:.1f} файл/сек | ⏱️ осталось {remaining/60:.1f} мин",
                          end='', flush=True)
        
        print(f"\n{'='*80}")
        print(f"\n✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
        print(f"   Загружено:  {self.uploaded:,}")
        print(f"   Пропущено:  {self.skipped:,}")
        print(f"   Ошибки:     {self.errors:,}")
        print(f"   Время:      {(time.time() - start_time)/60:.1f} мин")
        print("=" * 80)


if __name__ == '__main__':
    uploader = AdditionalPhotosFTPUploader()
    uploader.run(max_workers=15)


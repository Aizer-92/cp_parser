#!/usr/bin/env python3
"""
Загрузка допарсенных изображений (94 шт.) на Beget FTP
"""

import sys
from pathlib import Path
from ftplib import FTP_TLS
from sqlalchemy import text
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# FTP настройки Beget
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_USER = 'RECD00AQJIM4300MLJ0W'
FTP_PASS = 'FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf'
FTP_PATH = '/73d16f7545b3-promogoods/images/'

def main():
    db = PostgreSQLManager()
    
    print("=" * 80)
    print("🚀 ЗАГРУЗКА ДОПАРСЕННЫХ ИЗОБРАЖЕНИЙ НА FTP")
    print("=" * 80)
    
    # Получаем список проектов которые допарсили
    template4_missing = []
    with open('missing_images_template4.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 1:
                template4_missing.append(int(parts[0]))
    
    template5_missing = []
    with open('missing_images_template5.txt', 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 1:
                template5_missing.append(int(parts[0]))
    
    all_missing = template4_missing + template5_missing
    
    print(f"\n📋 Проектов для обработки: {len(all_missing)}")
    
    # Получаем изображения БЕЗ URL (только что допарсенные)
    with db.get_session() as session:
        images = session.execute(text("""
            SELECT pi.id, pi.image_filename, pi.local_path
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND (pi.image_url IS NULL OR pi.image_url = '')
            AND pi.local_path IS NOT NULL
            ORDER BY pi.id
        """), {'ids': all_missing}).fetchall()
        
        print(f"🖼️  Изображений для загрузки: {len(images)}")
        
        if len(images) == 0:
            print("\n✅ Нечего загружать!")
            return
        
        # Подключаемся к FTP
        print(f"\n🔌 Подключение к FTP: {FTP_HOST}")
        ftp = FTP_TLS(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()  # Защищенный канал данных
        
        # Переходим в нужную директорию
        try:
            ftp.cwd(FTP_PATH)
        except:
            print(f"📁 Создаю директорию: {FTP_PATH}")
            ftp.mkd(FTP_PATH)
            ftp.cwd(FTP_PATH)
        
        print(f"✅ Подключено к FTP\n")
        
        # Загружаем изображения
        uploaded = 0
        errors = 0
        
        for idx, (image_id, filename, local_path) in enumerate(images, 1):
            try:
                # Проверяем файл
                local_file = Path(local_path)
                if not local_file.exists():
                    print(f"[{idx}/{len(images)}] ❌ {filename}: файл не найден")
                    errors += 1
                    continue
                
                # Загружаем на FTP
                with open(local_file, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                
                # Обновляем URL в БД (ПРАВИЛЬНЫЙ формат с s3. префиксом!)
                new_url = f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
                
                session.execute(text("""
                    UPDATE product_images
                    SET image_url = :url
                    WHERE id = :image_id
                """), {'url': new_url, 'image_id': image_id})
                session.commit()
                
                uploaded += 1
                
                if uploaded % 10 == 0:
                    print(f"[{idx}/{len(images)}] ✅ Загружено: {uploaded}")
                
                # Небольшая задержка
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[{idx}/{len(images)}] ❌ {filename}: {e}")
                errors += 1
                continue
        
        ftp.quit()
        
        print("\n" + "=" * 80)
        print("✅ ЗАГРУЗКА ЗАВЕРШЕНА")
        print("=" * 80)
        print(f"\n📊 Статистика:")
        print(f"  • Загружено: {uploaded}")
        print(f"  • Ошибок: {errors}")
        print(f"  • Всего: {len(images)}")
        print("\n" + "=" * 80)

if __name__ == '__main__':
    main()


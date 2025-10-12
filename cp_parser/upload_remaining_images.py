#!/usr/bin/env python3
"""
Загрузка ТОЛЬКО недостающих изображений на FTP
"""

from pathlib import Path
from ftplib import FTP_TLS
import time

print("=" * 80)
print("🚀 ЗАГРУЗКА НЕДОСТАЮЩИХ ИЗОБРАЖЕНИЙ НА FTP")
print("=" * 80)

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

# Локальные файлы
images_dir = Path("storage/images")
local_files = {f.name: f for f in images_dir.glob("*") if f.is_file()}
print(f"\n📁 Локальных файлов: {len(local_files):,}")

# Подключаемся к FTP
print(f"\n🔌 Подключение к FTP...")
ftp = FTP_TLS(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd(FTP_DIR)
print("  ✅ Подключено")

# Список на FTP
print(f"\n📋 Проверяю файлы на FTP...")
ftp_files = set()
ftp.retrlines('NLST', ftp_files.add)
print(f"  ✅ На FTP: {len(ftp_files):,} файлов")

# Определяем что нужно загрузить
to_upload = set(local_files.keys()) - ftp_files
print(f"\n📤 К загрузке: {len(to_upload):,} файлов")

if not to_upload:
    print("\n🎉 ВСЕ ФАЙЛЫ УЖЕ НА FTP!")
    ftp.quit()
    exit(0)

# Загружаем
uploaded = 0
errors = 0
start_time = time.time()

print(f"\n🔄 Начинаю загрузку...")

for i, filename in enumerate(sorted(to_upload), 1):
    try:
        file_path = local_files[filename]
        with open(file_path, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        uploaded += 1
        
        # Прогресс каждые 50 файлов
        if uploaded % 50 == 0 or uploaded == len(to_upload):
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            remaining = len(to_upload) - uploaded
            eta_seconds = int(remaining / speed) if speed > 0 else 0
            
            print(f"  📤 {uploaded}/{len(to_upload)} | {speed:.1f} файлов/сек | ETA: {eta_seconds}с | {filename[:50]}")
    
    except Exception as e:
        errors += 1
        print(f"  ❌ Ошибка ({filename}): {e}")

ftp.quit()

elapsed = time.time() - start_time

print("\n" + "=" * 80)
print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
print("=" * 80)
print(f"\n📊 Результаты:")
print(f"  ✅ Загружено: {uploaded:,}")
print(f"  ❌ Ошибок: {errors:,}")
print(f"  ⏱️  Время: {int(elapsed//60)} мин {int(elapsed%60)} сек")
if uploaded > 0:
    print(f"  🚀 Средняя скорость: {uploaded/elapsed:.1f} файлов/сек")

print("\n" + "=" * 80)





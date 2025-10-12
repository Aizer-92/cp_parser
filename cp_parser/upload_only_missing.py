#!/usr/bin/env python3
"""
Загрузка ТОЛЬКО 847 недостающих файлов
Сначала сохраняем список, потом загружаем только их
"""

from pathlib import Path
from ftplib import FTP_TLS
import time
import json

print("=" * 80)
print("🚀 ЗАГРУЗКА ТОЛЬКО НЕДОСТАЮЩИХ 847 ФАЙЛОВ")
print("=" * 80)

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

missing_list_file = Path("missing_files.json")

# Если есть сохраненный список - загружаем из него
if missing_list_file.exists():
    print(f"\n📄 Найден сохраненный список недостающих файлов")
    with open(missing_list_file, 'r') as f:
        to_upload = json.load(f)
    print(f"  ✅ К загрузке: {len(to_upload)} файлов")
else:
    # Создаем список недостающих файлов
    print(f"\n🔍 Определяю недостающие файлы...")
    
    images_dir = Path("storage/images")
    local_files = {f.name: str(f) for f in images_dir.glob("*") if f.is_file()}
    print(f"  📁 Локальных файлов: {len(local_files):,}")
    
    # Подключаемся к FTP и получаем список
    print(f"\n🔌 Подключение к FTP (это займет ~1-2 минуты)...")
    ftp = FTP_TLS(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()
    ftp.cwd(FTP_DIR)
    
    print(f"  📋 Получаю список файлов на FTP...")
    ftp_files = set()
    ftp.retrlines('NLST', ftp_files.add)
    print(f"  ✅ На FTP: {len(ftp_files):,} файлов")
    
    ftp.quit()
    
    # Определяем недостающие
    missing_names = set(local_files.keys()) - ftp_files
    to_upload = [local_files[name] for name in missing_names]
    
    print(f"\n💾 Сохраняю список в {missing_list_file}")
    with open(missing_list_file, 'w') as f:
        json.dump(to_upload, f, indent=2)
    
    print(f"  ✅ К загрузке: {len(to_upload)} файлов")

if not to_upload:
    print("\n🎉 Нет файлов для загрузки!")
    exit(0)

# Теперь загружаем ТОЛЬКО эти файлы
print(f"\n🔌 Подключение к FTP для загрузки...")
ftp = FTP_TLS(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd(FTP_DIR)
print("  ✅ Подключено")

uploaded = 0
errors = 0
start_time = time.time()

print(f"\n🔄 Загружаю {len(to_upload)} файлов...\n")

for i, file_path_str in enumerate(to_upload, 1):
    file_path = Path(file_path_str)
    filename = file_path.name
    
    try:
        with open(file_path, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        uploaded += 1
        
        # Прогресс каждые 50 файлов
        if uploaded % 50 == 0 or uploaded == len(to_upload):
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            remaining = len(to_upload) - uploaded
            eta_seconds = int(remaining / speed) if speed > 0 else 0
            
            print(f"  ✅ {uploaded}/{len(to_upload)} | {speed:.1f} ф/сек | ETA: {eta_seconds}с")
    
    except Exception as e:
        errors += 1
        if errors <= 10:
            print(f"  ❌ Ошибка ({filename}): {e}")

ftp.quit()

elapsed = time.time() - start_time

print("\n" + "=" * 80)
print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
print("=" * 80)
print(f"\n📊 Результаты:")
print(f"  ✅ Загружено: {uploaded:,} из {len(to_upload):,}")
print(f"  ❌ Ошибок: {errors:,}")
print(f"  ⏱️  Время: {int(elapsed//60)} мин {int(elapsed%60)} сек")
if uploaded > 0:
    print(f"  🚀 Средняя скорость: {uploaded/elapsed:.1f} файлов/сек")

# Удаляем список после успешной загрузки
if errors == 0 and uploaded == len(to_upload):
    missing_list_file.unlink()
    print(f"\n🗑️  Список недостающих файлов удален")

print("\n" + "=" * 80)





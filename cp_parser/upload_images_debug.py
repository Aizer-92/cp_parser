#!/usr/bin/env python3
"""
Отладочная версия загрузки изображений на FTP
С детальным логированием
"""

import sys
from pathlib import Path
from ftplib import FTP_TLS
import time

print("=" * 80)
print("🚀 ЗАГРУЗКА ИЗОБРАЖЕНИЙ НА FTP (DEBUG VERSION)")
print("=" * 80)

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

print(f"\n🔧 FTP CONFIG:")
print(f"  Host: {FTP_HOST}")
print(f"  User: {FTP_USER}")
print(f"  Dir: {FTP_DIR}")

# Проверяем папку с изображениями
images_dir = Path("storage/images")
print(f"\n📁 Проверяю папку: {images_dir}")

if not images_dir.exists():
    print(f"❌ Папка не существует!")
    sys.exit(1)

all_images = [f for f in images_dir.glob("*") if f.is_file()]
print(f"✅ Найдено файлов: {len(all_images):,}")

if len(all_images) == 0:
    print("❌ Нет файлов для загрузки!")
    sys.exit(1)

# Подключаемся к FTP
print(f"\n🔌 Подключение к FTP...")
try:
    ftp = FTP_TLS(FTP_HOST)
    print("  ✅ Создан объект FTP_TLS")
    
    print(f"  🔑 Логин...")
    ftp.login(FTP_USER, FTP_PASS)
    print("  ✅ Логин успешен")
    
    print(f"  🔒 Защищенное соединение...")
    ftp.prot_p()
    print("  ✅ Защищенное соединение установлено")
    
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    sys.exit(1)

# Переходим в директорию
print(f"\n📁 Переход в директорию: {FTP_DIR}")
try:
    ftp.cwd(FTP_DIR)
    print("  ✅ Директория найдена")
except Exception as e:
    print(f"  ⚠️  Директория не существует, создаю...")
    try:
        ftp.mkd(FTP_DIR)
        ftp.cwd(FTP_DIR)
        print("  ✅ Директория создана")
    except Exception as e2:
        print(f"  ❌ Не могу создать директорию: {e2}")
        sys.exit(1)

# Получаем список файлов на FTP
print(f"\n📋 Получаю список файлов на FTP...")
existing_files = set()
try:
    ftp.retrlines('NLST', existing_files.add)
    print(f"  ✅ Файлов на FTP: {len(existing_files):,}")
except Exception as e:
    print(f"  ⚠️  Не могу получить список: {e}")
    print(f"  ℹ️  Считаю что FTP пустой")

# Загружаем файлы
uploaded = 0
skipped = 0
errors = 0

print(f"\n🔄 Начинаю загрузку...")
print(f"  К загрузке: {len(all_images) - len(existing_files):,} файлов")
start_time = time.time()

for i, img_file in enumerate(all_images, 1):
    filename = img_file.name
    
    # Пропускаем если уже есть
    if filename in existing_files:
        skipped += 1
        continue
    
    try:
        # Загружаем
        with open(img_file, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        uploaded += 1
        
        # Прогресс каждые 10 файлов
        if uploaded % 10 == 0:
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            remaining = len(all_images) - skipped - uploaded
            eta_minutes = int(remaining / speed / 60) if speed > 0 else 0
            
            print(f"  📤 {uploaded:,}/{len(all_images):,} | {speed:.1f} файлов/сек | ETA: ~{eta_minutes} мин")
    
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
print(f"  ✅ Загружено: {uploaded:,}")
print(f"  ⏭️  Пропущено (уже есть): {skipped:,}")
print(f"  ❌ Ошибок: {errors:,}")
print(f"  ⏱️  Время: {int(elapsed/60)} мин {int(elapsed%60)} сек")
if uploaded > 0:
    print(f"  🚀 Средняя скорость: {uploaded/elapsed:.1f} файлов/сек")

print("\n" + "=" * 80)





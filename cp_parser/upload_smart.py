#!/usr/bin/env python3
"""
Умная загрузка: пробуем загрузить, если ошибка "exists" - пропускаем
Без получения полного списка FTP (экономия времени)
"""

from pathlib import Path
from ftplib import FTP_TLS, error_perm
import time

print("=" * 80)
print("🚀 УМНАЯ ЗАГРУЗКА ИЗОБРАЖЕНИЙ НА FTP")
print("=" * 80)

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

# Локальные файлы
images_dir = Path("storage/images")
all_files = sorted([f for f in images_dir.glob("*") if f.is_file()])
print(f"\n📁 Локальных файлов: {len(all_files):,}")

# Подключаемся к FTP
print(f"\n🔌 Подключение к FTP...")
ftp = FTP_TLS(FTP_HOST)
ftp.login(FTP_USER, FTP_PASS)
ftp.prot_p()
ftp.cwd(FTP_DIR)
print("  ✅ Подключено")

# Загружаем БЕЗ предварительной проверки
# Просто пытаемся загрузить, если файл есть - получим ошибку
uploaded = 0
skipped = 0
errors = 0
start_time = time.time()

print(f"\n🔄 Начинаю загрузку (без проверки списка FTP)...")
print(f"  💡 Стратегия: пытаемся загрузить каждый файл")
print(f"  💡 Если файл существует - пропускаем\n")

for i, file_path in enumerate(all_files, 1):
    filename = file_path.name
    
    try:
        # Пытаемся загрузить
        with open(file_path, 'rb') as f:
            ftp.storbinary(f'STOR {filename}', f)
        
        uploaded += 1
        
        # Прогресс каждые 10 файлов
        if uploaded % 10 == 0:
            elapsed = time.time() - start_time
            speed = uploaded / elapsed if elapsed > 0 else 0
            print(f"  ✅ {uploaded} загружено | {skipped} пропущено | {speed:.1f} файлов/сек | {filename[:50]}")
    
    except error_perm as e:
        # Файл уже существует (553 error) - пропускаем
        if '553' in str(e) or 'exists' in str(e).lower() or 'already' in str(e).lower():
            skipped += 1
        else:
            errors += 1
            print(f"  ❌ Ошибка ({filename}): {e}")
    
    except Exception as e:
        errors += 1
        if errors <= 20:
            print(f"  ❌ Ошибка ({filename}): {e}")
    
    # Прогресс каждые 1000 файлов
    if i % 1000 == 0:
        elapsed = time.time() - start_time
        progress = i / len(all_files) * 100
        print(f"\n  📊 Прогресс: {i}/{len(all_files)} ({progress:.1f}%) | {int(elapsed//60)}:{int(elapsed%60):02d}\n")

ftp.quit()

elapsed = time.time() - start_time

print("\n" + "=" * 80)
print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
print("=" * 80)
print(f"\n📊 Результаты:")
print(f"  ✅ Загружено: {uploaded:,}")
print(f"  ⏭️  Пропущено (уже есть): {skipped:,}")
print(f"  ❌ Ошибок: {errors:,}")
print(f"  📁 Всего обработано: {len(all_files):,}")
print(f"  ⏱️  Время: {int(elapsed//60)} мин {int(elapsed%60)} сек")
if uploaded > 0:
    print(f"  🚀 Средняя скорость: {uploaded/elapsed:.1f} файлов/сек")

print("\n" + "=" * 80)





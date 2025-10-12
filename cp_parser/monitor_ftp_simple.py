#!/usr/bin/env python3
"""Простой мониторинг загрузки - считает файлы на FTP"""

from ftplib import FTP_TLS
from pathlib import Path
import time

FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

# Считаем локальные файлы
local_count = len(list(Path("storage/images").glob("*")))

print("=" * 80)
print("📊 МОНИТОРИНГ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
print("=" * 80)
print(f"\n📁 Локальных файлов: {local_count:,}")

last_count = 0
iteration = 0

while True:
    iteration += 1
    
    try:
        # Подключаемся и считаем файлы на FTP
        ftp = FTP_TLS(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()
        ftp.cwd(FTP_DIR)
        
        files = []
        ftp.retrlines('NLST', files.append)
        ftp_count = len(files)
        ftp.quit()
        
        # Прогресс
        progress = (ftp_count * 100 // local_count) if local_count > 0 else 0
        remaining = local_count - ftp_count
        speed = ftp_count - last_count if iteration > 1 else 0
        
        print(f"\n[Итерация #{iteration}]")
        print(f"  📤 На FTP: {ftp_count:,}/{local_count:,} ({progress}%)")
        print(f"  ⏳ Осталось: {remaining:,}")
        
        if speed > 0:
            eta_minutes = int(remaining / speed / 6)  # 6 итераций в минуту
            print(f"  🚀 Скорость: ~{speed * 6} файлов/мин")
            print(f"  ⏱️  ETA: ~{eta_minutes} минут")
        
        if ftp_count >= local_count:
            print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
            break
        
        last_count = ftp_count
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    time.sleep(10)

print("=" * 80)



"""Простой мониторинг загрузки - считает файлы на FTP"""

from ftplib import FTP_TLS
from pathlib import Path
import time

FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

# Считаем локальные файлы
local_count = len(list(Path("storage/images").glob("*")))

print("=" * 80)
print("📊 МОНИТОРИНГ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
print("=" * 80)
print(f"\n📁 Локальных файлов: {local_count:,}")

last_count = 0
iteration = 0

while True:
    iteration += 1
    
    try:
        # Подключаемся и считаем файлы на FTP
        ftp = FTP_TLS(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()
        ftp.cwd(FTP_DIR)
        
        files = []
        ftp.retrlines('NLST', files.append)
        ftp_count = len(files)
        ftp.quit()
        
        # Прогресс
        progress = (ftp_count * 100 // local_count) if local_count > 0 else 0
        remaining = local_count - ftp_count
        speed = ftp_count - last_count if iteration > 1 else 0
        
        print(f"\n[Итерация #{iteration}]")
        print(f"  📤 На FTP: {ftp_count:,}/{local_count:,} ({progress}%)")
        print(f"  ⏳ Осталось: {remaining:,}")
        
        if speed > 0:
            eta_minutes = int(remaining / speed / 6)  # 6 итераций в минуту
            print(f"  🚀 Скорость: ~{speed * 6} файлов/мин")
            print(f"  ⏱️  ETA: ~{eta_minutes} минут")
        
        if ftp_count >= local_count:
            print("\n✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
            break
        
        last_count = ftp_count
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    time.sleep(10)

print("=" * 80)











#!/usr/bin/env python3
"""Мониторинг прогресса загрузки"""

from ftplib import FTP_TLS
from pathlib import Path
import time
from datetime import datetime

FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

# Локальные файлы
local_files = set([f.name for f in Path("storage/images").glob("*") if f.is_file()])
total = len(local_files)

print("=" * 80)
print("📊 МОНИТОРИНГ ЗАГРУЗКИ НА FTP")
print("=" * 80)
print(f"\n📁 Всего файлов для загрузки: {total:,}")

last_uploaded = 0
iteration = 0

while True:
    iteration += 1
    
    try:
        # Подключаемся к FTP
        ftp = FTP_TLS(FTP_HOST, timeout=30)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()
        ftp.cwd(FTP_DIR)
        
        # Получаем список файлов
        ftp_files = set()
        ftp.retrlines('NLST', ftp_files.add)
        ftp.quit()
        
        # Считаем пересечение
        uploaded = len(local_files & ftp_files)
        remaining = total - uploaded
        progress = (uploaded * 100 // total) if total > 0 else 0
        
        # Скорость
        speed = uploaded - last_uploaded if iteration > 1 else 0
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Итерация #{iteration}")
        print(f"  📤 Загружено: {uploaded:,}/{total:,} ({progress}%)")
        print(f"  ⏳ Осталось: {remaining:,}")
        
        if speed > 0:
            speed_per_min = speed * 2  # т.к. проверяем каждые 30 сек
            eta_minutes = int(remaining / speed_per_min) if speed_per_min > 0 else 0
            print(f"  🚀 Скорость: ~{speed_per_min} файлов/мин")
            print(f"  ⏱️  ETA: ~{eta_minutes} минут")
        elif iteration > 1:
            print(f"  ⚠️  Нет изменений (процесс может быть остановлен)")
        
        if uploaded >= total:
            print("\n" + "=" * 80)
            print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
            print("=" * 80)
            break
        
        last_uploaded = uploaded
        
    except Exception as e:
        print(f"  ❌ Ошибка: {e}")
    
    time.sleep(30)  # Проверяем каждые 30 секунд



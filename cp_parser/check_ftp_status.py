#!/usr/bin/env python3
"""
Проверка: сколько изображений уже на FTP
"""

from pathlib import Path
from ftplib import FTP_TLS

print("=" * 80)
print("🔍 ПРОВЕРКА СТАТУСА FTP")
print("=" * 80)

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

# Проверяем локальные файлы
images_dir = Path("storage/images")
if images_dir.exists():
    local_files = set(f.name for f in images_dir.glob("*") if f.is_file())
    print(f"\n📁 ЛОКАЛЬНЫЕ ФАЙЛЫ:")
    print(f"  Всего в папке storage/images: {len(local_files):,}")
else:
    print(f"\n❌ Папка storage/images не найдена!")
    local_files = set()

# Подключаемся к FTP
print(f"\n🔌 Подключение к FTP: {FTP_HOST}")
try:
    ftp = FTP_TLS(FTP_HOST)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.prot_p()
    ftp.cwd(FTP_DIR)
    print("  ✅ Подключение успешно")
    
    # Получаем список файлов на FTP
    print(f"\n📋 Получаю список файлов на FTP...")
    ftp_files = set()
    ftp.retrlines('NLST', ftp_files.add)
    
    print(f"\n☁️  ФАЙЛЫ НА FTP:")
    print(f"  Всего на FTP: {len(ftp_files):,}")
    
    ftp.quit()
    
    # Анализ
    print(f"\n📊 АНАЛИЗ:")
    
    if local_files:
        already_uploaded = local_files & ftp_files
        need_upload = local_files - ftp_files
        only_on_ftp = ftp_files - local_files
        
        print(f"  ✅ Уже загружено (есть локально и на FTP): {len(already_uploaded):,}")
        print(f"  📤 Нужно загрузить (есть локально, нет на FTP): {len(need_upload):,}")
        print(f"  ☁️  Только на FTP (нет локально): {len(only_on_ftp):,}")
        
        if need_upload:
            print(f"\n📝 ПРИМЕРЫ ФАЙЛОВ К ЗАГРУЗКЕ (первые 10):")
            for i, filename in enumerate(sorted(need_upload)[:10], 1):
                print(f"  {i}. {filename}")
        else:
            print(f"\n🎉 ВСЕ ЛОКАЛЬНЫЕ ФАЙЛЫ УЖЕ НА FTP!")
    else:
        print(f"  ⚠️  Нет локальных файлов для сравнения")
        print(f"  ☁️  На FTP: {len(ftp_files):,} файлов")

except Exception as e:
    print(f"❌ Ошибка: {e}")

print("=" * 80)





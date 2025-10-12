#!/usr/bin/env python3
"""
Проверка реального состояния хранилища S3/FTP на Beget
Анализ: количество, размер, формат файлов
"""

from ftplib import FTP_TLS
import time
from datetime import datetime
from collections import defaultdict

# FTP настройки
FTP_HOST = "ftp.ru1.storage.beget.cloud"
FTP_USER = "RECD00AQJIM4300MLJ0W"
FTP_PASS = "FIucJ3i9iIWZ5ieJvabvI0OxEn2Yv4gG5XRUeSNf"
FTP_DIR = "/73d16f7545b3-promogoods/images"

def get_size_readable(bytes_size):
    """Конвертирует байты в читаемый формат"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def analyze_storage():
    """Анализирует хранилище на FTP"""
    print("="*80)
    print("📊 АНАЛИЗ РЕАЛЬНОГО ХРАНИЛИЩА НА BEGET S3/FTP")
    print("="*80)
    
    print(f"\n🔌 Подключение к FTP...")
    print(f"   Host: {FTP_HOST}")
    print(f"   Path: {FTP_DIR}")
    
    try:
        ftp = FTP_TLS(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.prot_p()
        ftp.cwd(FTP_DIR)
        print("   ✅ Подключено успешно\n")
        
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return
    
    print("📥 Получаю список файлов (это может занять 1-2 минуты)...")
    start_time = time.time()
    
    # Получаем детальный список файлов
    files_data = []
    try:
        # LIST возвращает строки формата:
        # -rw-r--r--   1 user group    1234567 Oct 12 14:23 filename.png
        lines = []
        ftp.retrlines('LIST', lines.append)
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 9:
                # Размер файла - это обычно 5-й элемент
                try:
                    size = int(parts[4])
                    filename = ' '.join(parts[8:])  # имя файла может содержать пробелы
                    files_data.append({
                        'name': filename,
                        'size': size
                    })
                except (ValueError, IndexError):
                    continue
        
    except Exception as e:
        print(f"❌ Ошибка при получении списка: {e}")
        ftp.quit()
        return
    
    elapsed = time.time() - start_time
    print(f"✅ Список получен за {elapsed:.1f} сек\n")
    
    # Закрываем соединение
    ftp.quit()
    
    # АНАЛИЗ ДАННЫХ
    print("="*80)
    print("📊 СТАТИСТИКА")
    print("="*80)
    
    total_files = len(files_data)
    total_size = sum(f['size'] for f in files_data)
    
    print(f"\n📁 ОБЩАЯ ИНФОРМАЦИЯ:")
    print(f"   Всего файлов: {total_files:,}")
    print(f"   Общий размер: {get_size_readable(total_size)}")
    print(f"   Средний размер: {get_size_readable(total_size / total_files if total_files > 0 else 0)}")
    
    # Анализ по форматам
    print(f"\n📷 ФОРМАТЫ ФАЙЛОВ:")
    formats = defaultdict(lambda: {'count': 0, 'size': 0})
    
    for f in files_data:
        ext = f['name'].split('.')[-1].lower() if '.' in f['name'] else 'no_ext'
        formats[ext]['count'] += 1
        formats[ext]['size'] += f['size']
    
    for ext in sorted(formats.keys(), key=lambda x: formats[x]['size'], reverse=True):
        count = formats[ext]['count']
        size = formats[ext]['size']
        percent = (size / total_size * 100) if total_size > 0 else 0
        avg = size / count if count > 0 else 0
        print(f"   .{ext:6s}: {count:6,} файлов | {get_size_readable(size):>10} ({percent:5.1f}%) | avg: {get_size_readable(avg)}")
    
    # ТОП самых больших файлов
    print(f"\n🔝 ТОП-20 САМЫХ БОЛЬШИХ ФАЙЛОВ:")
    sorted_files = sorted(files_data, key=lambda x: x['size'], reverse=True)
    
    for i, f in enumerate(sorted_files[:20], 1):
        size_mb = f['size'] / (1024 * 1024)
        name = f['name'][:60] + '...' if len(f['name']) > 60 else f['name']
        print(f"   {i:2d}. {get_size_readable(f['size']):>10} - {name}")
    
    # Анализ по размерам
    print(f"\n📊 РАСПРЕДЕЛЕНИЕ ПО РАЗМЕРАМ:")
    size_ranges = {
        'Очень маленькие (<100 KB)': (0, 100 * 1024),
        'Маленькие (100 KB - 500 KB)': (100 * 1024, 500 * 1024),
        'Средние (500 KB - 1 MB)': (500 * 1024, 1 * 1024 * 1024),
        'Большие (1 MB - 5 MB)': (1 * 1024 * 1024, 5 * 1024 * 1024),
        'Очень большие (5 MB - 10 MB)': (5 * 1024 * 1024, 10 * 1024 * 1024),
        'Огромные (>10 MB)': (10 * 1024 * 1024, float('inf'))
    }
    
    for label, (min_size, max_size) in size_ranges.items():
        files_in_range = [f for f in files_data if min_size <= f['size'] < max_size]
        count = len(files_in_range)
        size = sum(f['size'] for f in files_in_range)
        percent = (count / total_files * 100) if total_files > 0 else 0
        size_percent = (size / total_size * 100) if total_size > 0 else 0
        print(f"   {label:30s}: {count:6,} ({percent:5.1f}%) | {get_size_readable(size):>10} ({size_percent:5.1f}%)")
    
    # ПОТЕНЦИАЛ СЖАТИЯ
    print(f"\n💡 ПОТЕНЦИАЛ СЖАТИЯ:")
    
    # Файлы >1 MB можно хорошо сжать
    large_files = [f for f in files_data if f['size'] > 1 * 1024 * 1024]
    large_size = sum(f['size'] for f in large_files)
    
    # Оценка: WebP дает ~90% сжатия для PNG
    estimated_after = large_size * 0.1  # 10% от оригинала
    estimated_savings = large_size - estimated_after
    
    print(f"   Файлов >1 MB: {len(large_files):,}")
    print(f"   Их размер: {get_size_readable(large_size)}")
    print(f"   После сжатия (WebP): {get_size_readable(estimated_after)}")
    print(f"   💰 Экономия: {get_size_readable(estimated_savings)} ({(estimated_savings/large_size*100):.1f}%)")
    
    # Сохраняем детальный отчет
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    report_file = f"STORAGE_ANALYSIS_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"Анализ хранилища Beget S3/FTP\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"="*80 + "\n\n")
        
        f.write(f"Всего файлов: {total_files:,}\n")
        f.write(f"Общий размер: {get_size_readable(total_size)}\n\n")
        
        f.write("ВСЕ ФАЙЛЫ (от больших к меньшим):\n")
        f.write("-"*80 + "\n")
        for i, file in enumerate(sorted_files, 1):
            f.write(f"{i:5d}. {get_size_readable(file['size']):>10} - {file['name']}\n")
    
    print(f"\n✅ Детальный отчет сохранен: {report_file}")
    print("="*80)

if __name__ == '__main__':
    analyze_storage()




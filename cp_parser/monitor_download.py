#!/usr/bin/env python3
"""
Мониторинг скачивания Excel файлов
"""

from pathlib import Path
import time

def monitor():
    """Показывает прогресс скачивания"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        total = len([line for line in f if line.strip().isdigit()])
    
    excel_dir = Path('excel_files')
    
    while True:
        # Считаем скачанные файлы
        downloaded = []
        for excel_path in excel_dir.glob('project_*.xlsx'):
            if excel_path.stat().st_size > 0:
                downloaded.append(excel_path)
        
        downloaded_count = len(downloaded)
        total_size = sum(f.stat().st_size for f in downloaded)
        
        print("\n" + "=" * 80)
        print(f"📥 ПРОГРЕСС СКАЧИВАНИЯ")
        print("=" * 80)
        print(f"Скачано файлов:  {downloaded_count}/{total} ({downloaded_count*100//total}%)")
        print(f"Общий размер:    {total_size:,} байт ({total_size/1024/1024:.1f} МБ)")
        print(f"Осталось:        {total - downloaded_count}")
        print("=" * 80)
        
        if downloaded_count >= total:
            print("\n✅ ВСЕ ФАЙЛЫ СКАЧАНЫ!")
            print("Следующий шаг: python3 reparse_images_from_excel.py")
            break
        
        # Показываем последние 5 файлов
        recent = sorted(downloaded, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        if recent:
            print("\n📁 Последние файлы:")
            for f in recent:
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"  • {f.name} ({size_mb:.1f} МБ)")
        
        print("\n⏳ Обновление через 10 секунд... (Ctrl+C для выхода)")
        time.sleep(10)

if __name__ == '__main__':
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Мониторинг остановлен")



"""
Мониторинг скачивания Excel файлов
"""

from pathlib import Path
import time

def monitor():
    """Показывает прогресс скачивания"""
    
    # Читаем список проектов
    with open('projects_need_images.txt', 'r') as f:
        total = len([line for line in f if line.strip().isdigit()])
    
    excel_dir = Path('excel_files')
    
    while True:
        # Считаем скачанные файлы
        downloaded = []
        for excel_path in excel_dir.glob('project_*.xlsx'):
            if excel_path.stat().st_size > 0:
                downloaded.append(excel_path)
        
        downloaded_count = len(downloaded)
        total_size = sum(f.stat().st_size for f in downloaded)
        
        print("\n" + "=" * 80)
        print(f"📥 ПРОГРЕСС СКАЧИВАНИЯ")
        print("=" * 80)
        print(f"Скачано файлов:  {downloaded_count}/{total} ({downloaded_count*100//total}%)")
        print(f"Общий размер:    {total_size:,} байт ({total_size/1024/1024:.1f} МБ)")
        print(f"Осталось:        {total - downloaded_count}")
        print("=" * 80)
        
        if downloaded_count >= total:
            print("\n✅ ВСЕ ФАЙЛЫ СКАЧАНЫ!")
            print("Следующий шаг: python3 reparse_images_from_excel.py")
            break
        
        # Показываем последние 5 файлов
        recent = sorted(downloaded, key=lambda x: x.stat().st_mtime, reverse=True)[:5]
        if recent:
            print("\n📁 Последние файлы:")
            for f in recent:
                size_mb = f.stat().st_size / 1024 / 1024
                print(f"  • {f.name} ({size_mb:.1f} МБ)")
        
        print("\n⏳ Обновление через 10 секунд... (Ctrl+C для выхода)")
        time.sleep(10)

if __name__ == '__main__':
    try:
        monitor()
    except KeyboardInterrupt:
        print("\n\n👋 Мониторинг остановлен")







#!/usr/bin/env python3
"""
Мониторинг загрузки и автоматический запуск очистки после завершения
"""

import sys
from pathlib import Path
from sqlalchemy import text
import time
import subprocess

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

def check_upload_progress():
    """Проверяет прогресс загрузки"""
    db = PostgreSQLManager()
    
    # Загружаем список проектов которые допарсили
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
    
    with db.get_session() as session:
        without_url = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND (pi.image_url IS NULL OR pi.image_url = '')
        """), {'ids': all_missing}).scalar()
        
        with_url = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND pi.image_url IS NOT NULL AND pi.image_url != ''
        """), {'ids': all_missing}).scalar()
        
        total = without_url + with_url
        return with_url, total, without_url

def is_upload_running():
    """Проверяет запущен ли процесс загрузки"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'upload_reparsed' in line and 'grep' not in line:
            return True
    return False

def main():
    print("=" * 80)
    print("⏱️  МОНИТОРИНГ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print("\nОжидание завершения загрузки...")
    print("Проверка каждые 30 секунд\n")
    
    check_count = 0
    
    while True:
        check_count += 1
        
        try:
            uploaded, total, remaining = check_upload_progress()
            progress = (uploaded / total * 100) if total > 0 else 0
            
            print(f"[{time.strftime('%H:%M:%S')}] Прогресс: {uploaded}/{total} ({progress:.1f}%) | Осталось: {remaining}")
            
            # Проверяем завершение
            if remaining == 0:
                print("\n" + "=" * 80)
                print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
                print("=" * 80)
                print("\n🚀 Запускаю очистку файлов Шаблона 5...")
                print("\n" + "=" * 80 + "\n")
                
                # Запускаем очистку
                subprocess.run([sys.executable, 'cleanup_template5_files.py'])
                break
            
            # Проверяем что процесс еще работает
            if not is_upload_running() and remaining > 0:
                print(f"\n⚠️  ВНИМАНИЕ: Процесс загрузки не запущен, но осталось {remaining} изображений!")
                print(f"⚠️  Возможно произошла ошибка. Проверьте лог: upload_reparsed.log")
                break
            
        except Exception as e:
            print(f"\n❌ Ошибка проверки: {e}")
            break
        
        # Ждем 30 секунд
        time.sleep(30)
    
    print("\n" + "=" * 80)
    print("✅ МОНИТОРИНГ ЗАВЕРШЕН")
    print("=" * 80)

if __name__ == '__main__':
    main()




"""
Мониторинг загрузки и автоматический запуск очистки после завершения
"""

import sys
from pathlib import Path
from sqlalchemy import text
import time
import subprocess

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

def check_upload_progress():
    """Проверяет прогресс загрузки"""
    db = PostgreSQLManager()
    
    # Загружаем список проектов которые допарсили
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
    
    with db.get_session() as session:
        without_url = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND (pi.image_url IS NULL OR pi.image_url = '')
        """), {'ids': all_missing}).scalar()
        
        with_url = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
            AND pi.image_url IS NOT NULL AND pi.image_url != ''
        """), {'ids': all_missing}).scalar()
        
        total = without_url + with_url
        return with_url, total, without_url

def is_upload_running():
    """Проверяет запущен ли процесс загрузки"""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    for line in result.stdout.split('\n'):
        if 'upload_reparsed' in line and 'grep' not in line:
            return True
    return False

def main():
    print("=" * 80)
    print("⏱️  МОНИТОРИНГ ЗАГРУЗКИ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print("\nОжидание завершения загрузки...")
    print("Проверка каждые 30 секунд\n")
    
    check_count = 0
    
    while True:
        check_count += 1
        
        try:
            uploaded, total, remaining = check_upload_progress()
            progress = (uploaded / total * 100) if total > 0 else 0
            
            print(f"[{time.strftime('%H:%M:%S')}] Прогресс: {uploaded}/{total} ({progress:.1f}%) | Осталось: {remaining}")
            
            # Проверяем завершение
            if remaining == 0:
                print("\n" + "=" * 80)
                print("✅ ЗАГРУЗКА ЗАВЕРШЕНА!")
                print("=" * 80)
                print("\n🚀 Запускаю очистку файлов Шаблона 5...")
                print("\n" + "=" * 80 + "\n")
                
                # Запускаем очистку
                subprocess.run([sys.executable, 'cleanup_template5_files.py'])
                break
            
            # Проверяем что процесс еще работает
            if not is_upload_running() and remaining > 0:
                print(f"\n⚠️  ВНИМАНИЕ: Процесс загрузки не запущен, но осталось {remaining} изображений!")
                print(f"⚠️  Возможно произошла ошибка. Проверьте лог: upload_reparsed.log")
                break
            
        except Exception as e:
            print(f"\n❌ Ошибка проверки: {e}")
            break
        
        # Ждем 30 секунд
        time.sleep(30)
    
    print("\n" + "=" * 80)
    print("✅ МОНИТОРИНГ ЗАВЕРШЕН")
    print("=" * 80)

if __name__ == '__main__':
    main()








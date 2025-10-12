#!/usr/bin/env python3
"""Мониторинг прогресса проверки"""

from pathlib import Path
import time

log_file = Path('verify_all_50.log')

print("🔍 Мониторинг проверки тиражей...")
print("=" * 70)

last_size = 0
no_change_count = 0

while True:
    if log_file.exists():
        current_size = log_file.stat().st_size
        
        if current_size > last_size:
            # Читаем последние строки
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                # Ищем прогресс
                for line in reversed(lines[-30:]):
                    if '# ' in line and '/' in line:
                        print(f"\r{line.strip()}", end='', flush=True)
                        break
                    elif 'ID' in line and 'Проверяю' in line:
                        print(f"\r{line.strip()[:60]}", end='', flush=True)
                        break
            
            last_size = current_size
            no_change_count = 0
        else:
            no_change_count += 1
            if no_change_count > 20:
                print("\n\n⚠️  Процесс завершен или остановлен")
                
                # Показываем последние 20 строк
                if log_file.exists():
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        print("\n📄 Последние строки лога:")
                        print("-" * 70)
                        for line in lines[-20:]:
                            print(line.rstrip())
                break
    else:
        print("⏳ Ожидание создания лог-файла...")
    
    time.sleep(3)





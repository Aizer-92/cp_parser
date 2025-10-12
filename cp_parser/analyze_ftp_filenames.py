#!/usr/bin/env python3
"""
Анализ имен файлов на FTP и создание структурированного списка
для выявления дублей и изображений не добавленных в БД
"""

import re
import csv
from ftplib import FTP
import os
from dotenv import load_dotenv

load_dotenv()

def parse_filename(filename):
    """
    Парсит название файла и извлекает компоненты
    
    Паттерны:
    1. {sheet_id}_{position}_{hash}.png
       Пример: 1fwvX9lN3tRlhmI_X0Ie9b-W1wX8B-2sh-vDSfc9NdbY_O4_04a64599.png
       
    2. {sheet_id}_{position}_{suffix}_{hash}.png
       Пример: 16t27DZ6EnQVx7DeHN9F1GKr4Ae9o5KL9luBS_rQ8WKg_Q8_3_62b0f70c.png
       
    3. {sheet_id}_{position}_{suffix}_{additional_hash}.png
       Пример: 1dsi__IfdxC-e1mhEGTWC72M0LLu8ZDaTQ2pcssebdI8_J3_1_acecbcc28340b119.png
    """
    
    if not filename.endswith('.png'):
        return None
    
    # Убираем .png
    name = filename[:-4]
    
    # Разбиваем по подчеркиванию
    parts = name.split('_')
    
    if len(parts) < 3:
        return None
    
    # Sheet ID - все до предпоследнего подчеркивания перед позицией
    # Позиция - буква + цифры (A4, O18, Q8, S76, etc)
    
    result = {
        'filename': filename,
        'sheet_id': None,
        'position': None,
        'suffix': None,
        'hash': None
    }
    
    # Ищем позицию (буква/буквы + цифры)
    position_pattern = r'^[A-Z]+\d+$'
    
    for i in range(1, len(parts)):
        if re.match(position_pattern, parts[i]):
            # Нашли позицию
            result['sheet_id'] = '_'.join(parts[:i])
            result['position'] = parts[i]
            
            # Остальное - суффикс и/или хеш
            remaining = parts[i+1:]
            
            if len(remaining) == 1:
                # Только хеш
                result['hash'] = remaining[0]
            elif len(remaining) == 2:
                # Суффикс и хеш (или два хеша)
                # Проверяем - если первый элемент короткий (1-2 символа), это суффикс
                if len(remaining[0]) <= 3 and remaining[0].isdigit():
                    result['suffix'] = remaining[0]
                    result['hash'] = remaining[1]
                else:
                    # Оба хеша
                    result['hash'] = '_'.join(remaining)
            elif len(remaining) > 2:
                # Суффикс + составной хеш
                if len(remaining[0]) <= 3 and remaining[0].isdigit():
                    result['suffix'] = remaining[0]
                    result['hash'] = '_'.join(remaining[1:])
                else:
                    result['hash'] = '_'.join(remaining)
            
            break
    
    return result if result['sheet_id'] and result['position'] else None


def get_ftp_files():
    """Получить список файлов с FTP"""
    print("🔌 Подключение к FTP...")
    
    ftp = FTP()
    ftp.connect(os.getenv('FTP_HOST'), int(os.getenv('FTP_PORT', 21)))
    ftp.login(os.getenv('FTP_USER'), os.getenv('FTP_PASSWORD'))
    
    # Переходим в директорию с изображениями
    ftp.cwd('/73d16f7545b3-promogoods/images')
    
    print("📥 Получаю список файлов...")
    files = []
    ftp.retrlines('NLST', files.append)
    
    ftp.quit()
    
    print(f"✅ Получено {len(files):,} файлов")
    return files


def main():
    print("=" * 80)
    print("📊 АНАЛИЗ ИМЕН ФАЙЛОВ НА FTP")
    print("=" * 80)
    print()
    
    # Получаем список файлов
    files = get_ftp_files()
    
    print("\n🔍 Парсинг имен файлов...")
    
    results = []
    failed = []
    
    for i, filename in enumerate(files, 1):
        if i % 1000 == 0:
            print(f"   Обработано: {i:,} / {len(files):,} ({i/len(files)*100:.1f}%)")
        
        parsed = parse_filename(filename)
        
        if parsed:
            # Формируем полный URL
            full_url = f"https://ftp.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}"
            
            results.append({
                'image_url': full_url,
                'sheet_id': parsed['sheet_id'],
                'position': parsed['position'],
                'suffix': parsed['suffix'] or '',
                'hash': parsed['hash'],
                'filename': filename
            })
        else:
            failed.append(filename)
    
    print(f"\n✅ Успешно распарсено: {len(results):,}")
    print(f"❌ Не удалось распарсить: {len(failed):,}")
    
    # Сохраняем результаты в CSV
    csv_file = 'FTP_FILES_ANALYSIS.csv'
    print(f"\n💾 Сохраняю в {csv_file}...")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['image_url', 'sheet_id', 'position', 'suffix'])
        writer.writeheader()
        
        for row in results:
            writer.writerow({
                'image_url': row['image_url'],
                'sheet_id': row['sheet_id'],
                'position': row['position'],
                'suffix': row['suffix']
            })
    
    print(f"✅ Сохранено {len(results):,} записей")
    
    # Статистика
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА")
    print("=" * 80)
    
    # Группируем по sheet_id
    sheets = {}
    for row in results:
        sid = row['sheet_id']
        if sid not in sheets:
            sheets[sid] = 0
        sheets[sid] += 1
    
    print(f"\n📁 Уникальных таблиц: {len(sheets):,}")
    
    # Файлы с суффиксами (дубли)
    with_suffix = [r for r in results if r['suffix']]
    print(f"🔄 Файлов с суффиксами (потенциальные дубли): {len(with_suffix):,}")
    
    # ТОП-10 таблиц по количеству изображений
    print(f"\n🔝 ТОП-10 таблиц по количеству изображений:")
    top_sheets = sorted(sheets.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (sheet_id, count) in enumerate(top_sheets, 1):
        print(f"   {i:2d}. {sheet_id[:50]:50s} - {count:4d} файлов")
    
    # Сохраняем не распарсенные
    if failed:
        failed_file = 'FTP_FAILED_PARSING.txt'
        print(f"\n⚠️  Сохраняю не распарсенные файлы в {failed_file}...")
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed))
        print(f"   Сохранено: {len(failed)} файлов")
    
    print("\n" + "=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\n📄 Результаты: {csv_file}")
    print(f"📊 Формат: image_url | sheet_id | position | suffix")


if __name__ == '__main__':
    main()


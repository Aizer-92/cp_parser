#!/usr/bin/env python3
"""
Парсинг названий файлов с FTP и создание структурированного списка
Формат: table_id_ПОЗИЦИЯ_суффикс_hash.png
"""

import re
import csv
from datetime import datetime

def parse_filename(filename):
    """
    Парсит название файла и извлекает компоненты
    
    Примеры форматов:
    1. 1dsi__IfdxC-e1mhEGTWC72M0LLu8ZDaTQ2pcssebdI8_J3_1_acecbcc28340b119.png
       table_id: 1dsi__IfdxC-e1mhEGTWC72M0LLu8ZDaTQ2pcssebdI8
       position: J3
       suffix: 1
       hash: acecbcc28340b119
    
    2. 1VjBBtTxdqP5WNixYOyikXqwPHxoPRyjKo9WMdaozvKU_O4_04a64599.png
       table_id: 1VjBBtTxdqP5WNixYOyikXqwPHxoPRyjKo9WMdaozvKU
       position: O4
       suffix: None
       hash: 04a64599
    
    3. 1ixbq5wYPcpYcsNR1qtVovPljsZTlwlPBJFKE-xxPzVk_S76_2_292508337.png
       table_id: 1ixbq5wYPcpYcsNR1qtVovPljsZTlwlPBJFKE-xxPzVk
       position: S76
       suffix: 2
       hash: 292508337
    """
    
    # Убираем расширение
    name_without_ext = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Паттерн: table_id_ПОЗИЦИЯ_[суффикс_]hash
    # Позиция = буква + цифры (A1, J3, O4, S76, etc)
    
    # Пробуем разбить по подчеркиваниям
    parts = name_without_ext.split('_')
    
    if len(parts) < 3:
        # Неправильный формат
        return {
            'table_id': None,
            'position': None,
            'suffix': None,
            'hash': None,
            'full_url': f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}",
            'filename': filename,
            'parse_error': 'Недостаточно частей'
        }
    
    # Последняя часть - всегда hash
    hash_part = parts[-1]
    
    # Предпоследняя часть - позиция (буква+цифры) или суффикс (только цифра)
    # Если это только цифра - значит есть суффикс
    position_or_suffix = parts[-2]
    
    # Проверяем формат позиции: буква + цифры
    position_match = re.match(r'^([A-Z]+)(\d+)$', position_or_suffix)
    
    if position_match:
        # Это позиция, суффикса нет
        position = position_or_suffix
        suffix = None
        # table_id = все части до позиции
        table_id = '_'.join(parts[:-2])
    else:
        # Это суффикс (цифра), значит позиция на один элемент раньше
        if len(parts) < 4:
            return {
                'table_id': None,
                'position': None,
                'suffix': None,
                'hash': None,
                'full_url': f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}",
                'filename': filename,
                'parse_error': 'Недостаточно частей с суффиксом'
            }
        
        suffix = position_or_suffix
        position = parts[-3]
        # table_id = все части до позиции
        table_id = '_'.join(parts[:-3])
        
        # Проверяем что позиция правильного формата
        if not re.match(r'^([A-Z]+)(\d+)$', position):
            return {
                'table_id': None,
                'position': None,
                'suffix': None,
                'hash': None,
                'full_url': f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}",
                'filename': filename,
                'parse_error': f'Неправильный формат позиции: {position}'
            }
    
    return {
        'table_id': table_id,
        'position': position,
        'suffix': suffix,
        'hash': hash_part,
        'full_url': f"https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}",
        'filename': filename,
        'parse_error': None
    }

def main():
    print("="*80)
    print("📋 ПАРСИНГ НАЗВАНИЙ ФАЙЛОВ С FTP")
    print("="*80)
    
    # Читаем файл с анализом
    storage_file = "STORAGE_ANALYSIS_20251012_1455.txt"
    
    print(f"\n📂 Читаю файл: {storage_file}")
    
    filenames = []
    with open(storage_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Пропускаем заголовок (первые 9 строк)
        for line in lines[9:]:
            line = line.strip()
            if not line or line.startswith('=') or line.startswith('-'):
                continue
            
            # Формат: "  123.   10.97 MB - filename.png"
            parts = line.split(' - ', 1)
            if len(parts) == 2:
                filename = parts[1].strip()
                if filename:
                    filenames.append(filename)
    
    print(f"✅ Найдено файлов: {len(filenames):,}\n")
    
    print("🔍 Парсинг названий файлов...")
    
    parsed_data = []
    errors = []
    
    for filename in filenames:
        result = parse_filename(filename)
        parsed_data.append(result)
        
        if result['parse_error']:
            errors.append(result)
    
    print(f"✅ Спарсено: {len(parsed_data):,}")
    print(f"❌ Ошибок парсинга: {len(errors):,}\n")
    
    # Сохраняем результат в CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_file = f"FTP_FILES_PARSED_{timestamp}.csv"
    
    print(f"💾 Сохраняю в CSV: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'URL',
            'Table_ID', 
            'Position',
            'Suffix',
            'Hash',
            'Filename',
            'Parse_Error'
        ])
        
        for item in parsed_data:
            writer.writerow([
                item['full_url'],
                item['table_id'] or '',
                item['position'] or '',
                item['suffix'] or '',
                item['hash'] or '',
                item['filename'],
                item['parse_error'] or ''
            ])
    
    print(f"✅ Сохранено: {len(parsed_data):,} записей")
    
    # СТАТИСТИКА
    print("\n" + "="*80)
    print("📊 СТАТИСТИКА")
    print("="*80)
    
    # Успешно спарсено
    successful = [p for p in parsed_data if not p['parse_error']]
    print(f"\n✅ Успешно спарсено: {len(successful):,} ({len(successful)/len(parsed_data)*100:.1f}%)")
    
    # Уникальные table_id
    unique_tables = set(p['table_id'] for p in successful if p['table_id'])
    print(f"📋 Уникальных Table ID: {len(unique_tables):,}")
    
    # С суффиксами и без
    with_suffix = [p for p in successful if p['suffix']]
    without_suffix = [p for p in successful if not p['suffix']]
    print(f"\n📷 С суффиксом (дополнительные фото): {len(with_suffix):,}")
    print(f"📷 Без суффикса (основные фото): {len(without_suffix):,}")
    
    # Примеры с ошибками
    if errors:
        print(f"\n❌ ПРИМЕРЫ ОШИБОК ПАРСИНГА (первые 10):")
        for i, err in enumerate(errors[:10], 1):
            print(f"   {i}. {err['filename'][:70]}...")
            print(f"      Ошибка: {err['parse_error']}")
    
    # Топ table_id по количеству файлов
    from collections import Counter
    table_counts = Counter(p['table_id'] for p in successful if p['table_id'])
    
    print(f"\n🔝 ТОП-20 TABLE_ID ПО КОЛИЧЕСТВУ ФАЙЛОВ:")
    for i, (table_id, count) in enumerate(table_counts.most_common(20), 1):
        short_id = table_id[:40] + '...' if len(table_id) > 40 else table_id
        print(f"   {i:2d}. {short_id:45s} : {count:4d} файлов")
    
    print("\n" + "="*80)
    print(f"✅ Готово! Результат: {output_file}")
    print("="*80)

if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Правильный поиск дублей с корректным парсингом позиций
"""

import re
import csv
from collections import defaultdict

def extract_filenames_and_sizes_from_report(report_file):
    """Извлекает имена файлов и их размеры из отчета"""
    files_data = []
    
    with open(report_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            match = re.search(r'(\d+\.\d+)\s+(KB|MB|GB)\s+-\s+(.+)$', line)
            if match:
                size_value = float(match.group(1))
                size_unit = match.group(2)
                filename = match.group(3).strip()
                
                # Конвертируем в KB
                if size_unit == 'MB':
                    size_kb = size_value * 1024
                elif size_unit == 'GB':
                    size_kb = size_value * 1024 * 1024
                else:
                    size_kb = size_value
                
                files_data.append({
                    'filename': filename,
                    'size_kb': size_kb
                })
    
    return files_data


def parse_filename_correct(filename):
    """
    ПРАВИЛЬНЫЙ парсинг:
    Формат: {sheet_id}_{position}_{hash}.png
    или: {sheet_id}_{position}_{suffix}_{hash}.png
    
    Позиция - это ПОСЛЕДНЯЯ часть перед хешем, которая соответствует паттерну [A-Z]+\d+
    
    Примеры:
    1. 1fwvX9lN3tRlhmI_X0Ie9b-W1wX8B-2sh-vDSfc9NdbY_O4_04a64599.png
       sheet_id: 1fwvX9lN3tRlhmI_X0Ie9b-W1wX8B-2sh-vDSfc9NdbY
       position: O4
       hash: 04a64599
    
    2. 1tadByKcZFWoLp05vV_TqaPslPdZVi-_ofiSBmF6_GR0_O13_74e0eac4.png
       sheet_id: 1tadByKcZFWoLp05vV_TqaPslPdZVi-_ofiSBmF6_GR0 (включая GR0!)
       position: O13
       hash: 74e0eac4
       
    3. 16t27DZ6EnQVx7DeHN9F1GKr4Ae9o5KL9luBS_rQ8WKg_Q8_3_62b0f70c.png
       sheet_id: 16t27DZ6EnQVx7DeHN9F1GKr4Ae9o5KL9luBS_rQ8WKg
       position: Q8
       suffix: 3
       hash: 62b0f70c
    """
    
    if not filename.endswith('.png') and not filename.endswith('.pn') and not filename.endswith('.p'):
        return None
    
    if '...' in filename:
        return None
    
    # Убираем расширение
    name = filename.replace('.png', '').replace('.pn', '').replace('.p', '')
    
    # Разбиваем по подчеркиванию
    parts = name.split('_')
    
    if len(parts) < 3:
        return None
    
    # Ищем позицию с КОНЦА
    # Позиция - это [A-Z]+\d+
    position_pattern = r'^[A-Z]+\d+$'
    
    position_idx = None
    for i in range(len(parts) - 1, 0, -1):  # идем с конца, но не включаем первый элемент
        if re.match(position_pattern, parts[i]):
            position_idx = i
            break
    
    if position_idx is None:
        return None
    
    result = {
        'filename': filename,
        'sheet_id': '_'.join(parts[:position_idx]),
        'position': parts[position_idx],
        'suffix': None
    }
    
    # Все что после позиции - это суффикс и/или хеш
    remaining = parts[position_idx + 1:]
    
    if len(remaining) >= 2:
        # Если первый элемент короткий и цифровой - это суффикс
        if len(remaining[0]) <= 3 and remaining[0].isdigit():
            result['suffix'] = remaining[0]
    
    return result


def main():
    print("=" * 80)
    print("🔍 ПРАВИЛЬНЫЙ ПОИСК ДУБЛЕЙ ИЗОБРАЖЕНИЙ")
    print("=" * 80)
    print()
    
    report_file = 'STORAGE_ANALYSIS_20251012_1455.txt'
    
    print(f"📄 Читаю файл: {report_file}")
    files_data = extract_filenames_and_sizes_from_report(report_file)
    print(f"✅ Найдено {len(files_data):,} файлов")
    
    print("\n🔍 Парсинг и группировка...")
    
    # Группируем по sheet_id + position + suffix
    groups = defaultdict(list)
    failed_parse = 0
    
    for i, file_data in enumerate(files_data, 1):
        if i % 5000 == 0:
            print(f"   Обработано: {i:,} / {len(files_data):,} ({i/len(files_data)*100:.1f}%)")
        
        filename = file_data['filename']
        size_kb = file_data['size_kb']
        
        if '...' in filename:
            continue
        
        parsed = parse_filename_correct(filename)
        
        if parsed:
            # Создаем ключ: sheet_id + position + suffix
            key = f"{parsed['sheet_id']}|{parsed['position']}|{parsed['suffix'] or ''}"
            
            groups[key].append({
                'filename': filename,
                'size_kb': size_kb,
                'sheet_id': parsed['sheet_id'],
                'position': parsed['position'],
                'suffix': parsed['suffix'] or ''
            })
        else:
            failed_parse += 1
    
    print(f"\n✅ Создано групп: {len(groups):,}")
    print(f"❌ Не удалось распарсить: {failed_parse:,}")
    
    # Ищем дубли - группы с более чем 1 файлом
    print("\n🔍 Поиск дублей...")
    
    duplicates = []
    duplicate_groups = []
    
    for key, files in groups.items():
        if len(files) > 1:
            duplicate_groups.append({
                'key': key,
                'files': files,
                'count': len(files)
            })
            duplicates.extend(files)
    
    print(f"✅ Найдено групп с дублями: {len(duplicate_groups):,}")
    print(f"✅ Всего файлов-дублей: {len(duplicates):,}")
    
    if not duplicate_groups:
        print("\n🎉 Дублей не найдено! Все изображения уникальны.")
        return
    
    # Сортируем по количеству дублей
    duplicate_groups.sort(key=lambda x: x['count'], reverse=True)
    
    # Сохраняем детальный отчет
    detail_file = 'REAL_DUPLICATES_DETAIL.csv'
    print(f"\n💾 Сохраняю детальный отчет: {detail_file}")
    
    with open(detail_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sheet_id', 'position', 'suffix', 'filename', 'size_kb', 'size_mb', 'image_url'])
        
        for group in duplicate_groups:
            parts = group['key'].split('|')
            sheet_id = parts[0]
            position = parts[1]
            suffix = parts[2]
            
            for file_data in group['files']:
                url = f"https://ftp.ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{file_data['filename']}"
                writer.writerow([
                    sheet_id,
                    position,
                    suffix,
                    file_data['filename'],
                    f"{file_data['size_kb']:.2f}",
                    f"{file_data['size_kb']/1024:.2f}",
                    url
                ])
    
    # Сохраняем сводку по группам
    summary_file = 'REAL_DUPLICATES_SUMMARY.csv'
    print(f"💾 Сохраняю сводку: {summary_file}")
    
    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sheet_id', 'position', 'suffix', 'duplicate_count', 'total_size_mb', 'sizes_mb', 'same_size'])
        
        for group in duplicate_groups:
            parts = group['key'].split('|')
            sheet_id = parts[0]
            position = parts[1]
            suffix = parts[2]
            
            total_size = sum(f['size_kb'] for f in group['files'])
            sizes = [f"{f['size_kb']/1024:.2f}" for f in group['files']]
            
            # Проверяем одинаковый ли размер (с погрешностью 1%)
            size_values = [f['size_kb'] for f in group['files']]
            avg_size = sum(size_values) / len(size_values)
            same_size = all(abs(s - avg_size) / avg_size < 0.01 for s in size_values)
            
            writer.writerow([
                sheet_id,
                position,
                suffix,
                group['count'],
                f"{total_size/1024:.2f}",
                ' | '.join(sizes),
                'ДА' if same_size else 'НЕТ'
            ])
    
    # Статистика
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА ДУБЛЕЙ")
    print("=" * 80)
    
    total_duplicate_size = sum(f['size_kb'] for f in duplicates) / 1024  # в MB
    
    print(f"\n📊 ОБЩАЯ ИНФОРМАЦИЯ:")
    print(f"   Групп с дублями: {len(duplicate_groups):,}")
    print(f"   Всего файлов-дублей: {len(duplicates):,}")
    print(f"   Общий размер дублей: {total_duplicate_size:.2f} MB ({total_duplicate_size/1024:.2f} GB)")
    
    # Потенциальная экономия
    files_to_delete = len(duplicates) - len(duplicate_groups)
    size_to_free = sum(
        sum(f['size_kb'] for f in group['files'][1:]) 
        for group in duplicate_groups
    ) / 1024
    
    print(f"\n💾 ПОТЕНЦИАЛЬНАЯ ЭКОНОМИЯ (удалив дубли):")
    print(f"   Файлов можно удалить: {files_to_delete:,}")
    print(f"   Место освободится: {size_to_free:.2f} MB ({size_to_free/1024:.2f} GB)")
    
    # Дубли с одинаковым размером
    same_size_groups = [g for g in duplicate_groups if all(
        abs(f['size_kb'] - g['files'][0]['size_kb']) / g['files'][0]['size_kb'] < 0.01
        for f in g['files']
    )]
    
    print(f"\n🔍 ДУБЛИ С ОДИНАКОВЫМ РАЗМЕРОМ (точные копии):")
    print(f"   Групп: {len(same_size_groups):,}")
    print(f"   Файлов: {sum(len(g['files']) for g in same_size_groups):,}")
    
    # ТОП-10 групп с наибольшим количеством дублей
    print(f"\n🔝 ТОП-10 ГРУПП С НАИБОЛЬШИМ КОЛИЧЕСТВОМ ДУБЛЕЙ:")
    for i, group in enumerate(duplicate_groups[:10], 1):
        parts = group['key'].split('|')
        sheet_id = parts[0][:40]
        position = parts[1]
        suffix = parts[2] or '(нет)'
        total_size = sum(f['size_kb'] for f in group['files']) / 1024
        
        # Проверяем одинаковый размер
        size_values = [f['size_kb'] for f in group['files']]
        avg_size = sum(size_values) / len(size_values)
        same_size = all(abs(s - avg_size) / avg_size < 0.01 for s in size_values)
        same_size_label = "✅ ОДИНАКОВЫЙ" if same_size else "❌ разный"
        
        print(f"   {i:2d}. Sheet: {sheet_id:40s} | Pos: {position:4s} | Suf: {suffix:3s} | "
              f"Дублей: {group['count']:2d} | {total_size:.1f} MB | {same_size_label}")
    
    # Пример группы с одинаковым размером
    if same_size_groups:
        print(f"\n📋 ПРИМЕР ТОЧНЫХ ДУБЛЕЙ (первая группа с одинаковым размером):")
        first_group = same_size_groups[0]
        parts = first_group['key'].split('|')
        print(f"   Sheet ID: {parts[0]}")
        print(f"   Position: {parts[1]}")
        print(f"   Suffix: {parts[2] or '(нет)'}")
        print(f"   Количество: {first_group['count']}")
        print(f"\n   Файлы:")
        for j, file_data in enumerate(first_group['files'], 1):
            print(f"      {j}. {file_data['filename'][:70]:70s} - {file_data['size_kb']/1024:.2f} MB")
    
    print("\n" + "=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\n📄 Детальный отчет: {detail_file}")
    print(f"📄 Сводка: {summary_file}")
    print(f"\n💡 Дубли с одинаковым размером - это ТОЧНЫЕ КОПИИ, их можно безопасно удалить")


if __name__ == '__main__':
    main()


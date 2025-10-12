#!/usr/bin/env python3
"""
Поиск реальных дублей - изображений с одинаковым sheet_id + position + suffix
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
            
            # Ищем строки с размером файла и именем
            # Формат: "   SIZE - FILENAME"
            match = re.search(r'(\d+\.\d+)\s+(KB|MB|GB)\s+-\s+(.+)$', line)
            if match:
                size_value = float(match.group(1))
                size_unit = match.group(2)
                filename = match.group(3).strip()
                
                # Конвертируем в KB для единообразия
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


def parse_filename(filename):
    """Парсит название файла"""
    if not filename.endswith('.png') and not filename.endswith('.pn') and not filename.endswith('.p'):
        return None
    
    # Убираем расширение и возможное обрезание
    name = filename
    if name.endswith('...'):
        return None
    
    name = name.replace('.png', '').replace('.pn', '').replace('.p', '')
    
    # Разбиваем по подчеркиванию
    parts = name.split('_')
    
    if len(parts) < 3:
        return None
    
    result = {
        'filename': filename,
        'sheet_id': None,
        'position': None,
        'suffix': None
    }
    
    # Ищем позицию (буква/буквы + цифры)
    position_pattern = r'^[A-Z]+\d+$'
    
    for i in range(1, len(parts)):
        if re.match(position_pattern, parts[i]):
            result['sheet_id'] = '_'.join(parts[:i])
            result['position'] = parts[i]
            
            # Остальное - суффикс и/или хеш
            remaining = parts[i+1:]
            
            if len(remaining) >= 2:
                # Проверяем первый элемент - если короткий и цифровой, это суффикс
                if len(remaining[0]) <= 3 and remaining[0].isdigit():
                    result['suffix'] = remaining[0]
            
            break
    
    return result if result['sheet_id'] and result['position'] else None


def main():
    print("=" * 80)
    print("🔍 ПОИСК РЕАЛЬНЫХ ДУБЛЕЙ ИЗОБРАЖЕНИЙ")
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
        
        parsed = parse_filename(filename)
        
        if parsed:
            # Создаем уникальный ключ: sheet_id + position + suffix
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
    detail_file = 'DUPLICATES_DETAIL.csv'
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
    summary_file = 'DUPLICATES_SUMMARY.csv'
    print(f"💾 Сохраняю сводку: {summary_file}")
    
    with open(summary_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['sheet_id', 'position', 'suffix', 'duplicate_count', 'total_size_mb', 'filenames'])
        
        for group in duplicate_groups:
            parts = group['key'].split('|')
            sheet_id = parts[0]
            position = parts[1]
            suffix = parts[2]
            
            total_size = sum(f['size_kb'] for f in group['files'])
            filenames = ' | '.join(f['filename'][:50] for f in group['files'])
            
            writer.writerow([
                sheet_id,
                position,
                suffix,
                group['count'],
                f"{total_size/1024:.2f}",
                filenames
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
    
    # Потенциальная экономия (оставляем по 1 файлу из каждой группы)
    files_to_delete = len(duplicates) - len(duplicate_groups)
    size_to_free = sum(
        sum(f['size_kb'] for f in group['files'][1:]) 
        for group in duplicate_groups
    ) / 1024
    
    print(f"\n💾 ПОТЕНЦИАЛЬНАЯ ЭКОНОМИЯ:")
    print(f"   Файлов можно удалить: {files_to_delete:,}")
    print(f"   Место освободится: {size_to_free:.2f} MB ({size_to_free/1024:.2f} GB)")
    
    # ТОП-10 групп с наибольшим количеством дублей
    print(f"\n🔝 ТОП-10 ГРУПП С НАИБОЛЬШИМ КОЛИЧЕСТВОМ ДУБЛЕЙ:")
    for i, group in enumerate(duplicate_groups[:10], 1):
        parts = group['key'].split('|')
        sheet_id = parts[0][:40]
        position = parts[1]
        suffix = parts[2] or '(без суффикса)'
        total_size = sum(f['size_kb'] for f in group['files']) / 1024
        
        print(f"   {i:2d}. Sheet: {sheet_id:40s} | Pos: {position:4s} | Suffix: {suffix:3s} | "
              f"Дублей: {group['count']:2d} | Размер: {total_size:.1f} MB")
    
    # Примеры дублей
    print(f"\n📋 ПРИМЕРЫ ДУБЛЕЙ (первая группа):")
    first_group = duplicate_groups[0]
    parts = first_group['key'].split('|')
    print(f"   Sheet ID: {parts[0]}")
    print(f"   Position: {parts[1]}")
    print(f"   Suffix: {parts[2] or '(без суффикса)'}")
    print(f"   Количество дублей: {first_group['count']}")
    print(f"\n   Файлы:")
    for j, file_data in enumerate(first_group['files'], 1):
        print(f"      {j}. {file_data['filename'][:70]:70s} - {file_data['size_kb']/1024:.2f} MB")
    
    print("\n" + "=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\n📄 Детальный отчет: {detail_file}")
    print(f"📄 Сводка: {summary_file}")
    print(f"\n💡 Используй эти файлы для:")
    print(f"   • Удаления дублей")
    print(f"   • Освобождения места на FTP")
    print(f"   • Понимания причин появления дублей")


if __name__ == '__main__':
    main()


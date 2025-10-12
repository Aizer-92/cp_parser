#!/usr/bin/env python3
"""
Парсинг имен файлов из отчета STORAGE_ANALYSIS и создание структурированного списка
"""

import re
import csv

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
    
    # Убираем .png и возможное обрезание
    name = filename
    if name.endswith('...'):
        # Файл был обрезан в отчете, пропускаем
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


def extract_filenames_from_report(report_file):
    """Извлекает имена файлов из отчета"""
    filenames = []
    
    with open(report_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Ищем строки с размером файла и именем
            # Формат: "   SIZE - FILENAME"
            # Пример: "   10.97 MB - 17Y5ilb95T7UPkRIOHcFajqKJS-Hi824gkeGKGjQq6m4_N31_088583bc.png"
            
            match = re.search(r'\d+\.\d+\s+(KB|MB|GB)\s+-\s+(.+)$', line)
            if match:
                filename = match.group(2).strip()
                filenames.append(filename)
    
    return filenames


def main():
    print("=" * 80)
    print("📊 ПАРСИНГ ИМЕН ФАЙЛОВ ИЗ ОТЧЕТА")
    print("=" * 80)
    print()
    
    report_file = 'STORAGE_ANALYSIS_20251012_1455.txt'
    
    print(f"📄 Читаю файл: {report_file}")
    filenames = extract_filenames_from_report(report_file)
    print(f"✅ Найдено {len(filenames):,} файлов")
    
    print("\n🔍 Парсинг имен файлов...")
    
    results = []
    failed = []
    skipped_truncated = 0
    
    for i, filename in enumerate(filenames, 1):
        if i % 1000 == 0:
            print(f"   Обработано: {i:,} / {len(filenames):,} ({i/len(filenames)*100:.1f}%)")
        
        # Пропускаем обрезанные имена
        if '...' in filename:
            skipped_truncated += 1
            continue
        
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
    print(f"⚠️  Пропущено обрезанных: {skipped_truncated:,}")
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
            sheets[sid] = []
        sheets[sid].append(row)
    
    print(f"\n📁 Уникальных таблиц: {len(sheets):,}")
    
    # Файлы с суффиксами (дубли)
    with_suffix = [r for r in results if r['suffix']]
    print(f"🔄 Файлов с суффиксами (потенциальные дубли): {len(with_suffix):,}")
    
    # ТОП-10 таблиц по количеству изображений
    print(f"\n🔝 ТОП-10 таблиц по количеству изображений:")
    top_sheets = sorted(sheets.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for i, (sheet_id, files) in enumerate(top_sheets, 1):
        suffix_count = len([f for f in files if f['suffix']])
        print(f"   {i:2d}. {sheet_id[:50]:50s} - {len(files):4d} файлов ({suffix_count} с суффиксами)")
    
    # Статистика по позициям
    positions = {}
    for row in results:
        pos = row['position']
        if pos not in positions:
            positions[pos] = 0
        positions[pos] += 1
    
    print(f"\n📍 Уникальных позиций: {len(positions):,}")
    print(f"\n🔝 ТОП-10 позиций:")
    top_positions = sorted(positions.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (pos, count) in enumerate(top_positions, 1):
        print(f"   {i:2d}. {pos:4s} - {count:5d} файлов")
    
    # Сохраняем не распарсенные
    if failed:
        failed_file = 'FTP_FAILED_PARSING.txt'
        print(f"\n⚠️  Сохраняю не распарсенные файлы в {failed_file}...")
        with open(failed_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(failed))
        print(f"   Сохранено: {len(failed)} файлов")
    
    # Примеры файлов с суффиксами
    if with_suffix:
        print(f"\n📋 ПРИМЕРЫ ФАЙЛОВ С СУФФИКСАМИ (первые 10):")
        for i, row in enumerate(with_suffix[:10], 1):
            print(f"   {i:2d}. Sheet: {row['sheet_id'][:40]:40s} | Pos: {row['position']:4s} | Suffix: {row['suffix']}")
    
    print("\n" + "=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\n📄 Результаты: {csv_file}")
    print(f"📊 Формат: image_url | sheet_id | position | suffix")
    print(f"\n💡 Используй этот CSV для сравнения с БД и выявления:")
    print(f"   • Дублей (файлы с одинаковым sheet_id + position но разными суффиксами)")
    print(f"   • Изображений не добавленных в БД")
    print(f"   • Лишних файлов на FTP")


if __name__ == '__main__':
    main()


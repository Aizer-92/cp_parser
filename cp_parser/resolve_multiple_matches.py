#!/usr/bin/env python3
"""
Обработка множественных совпадений - выбираем первый URL из дублей
"""

import csv

def process_multiple_matches(input_file, output_file):
    """
    Обработать множественные совпадения
    Выбираем первый URL из списка дублей для каждого изображения
    """
    print(f"📄 Читаю файл: {input_file}")
    
    resolved = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Берем первый URL из списка
            urls = row['ftp_urls'].split(' | ')
            first_url = urls[0]
            
            resolved.append({
                'image_id': row['image_id'],
                'product_id': row['product_id'],
                'sheet_id': row['sheet_id'],
                'position': row['position'],
                'image_type': row['image_type'],
                'row_number': row['row_number'],
                'product_name': row['product_name'],
                'ftp_url': first_url,
                'match_type': 'multiple_resolved',
                'total_duplicates': row['urls_count']
            })
    
    print(f"✅ Обработано {len(resolved):,} записей")
    
    # Сохраняем
    print(f"💾 Сохраняю в {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'image_id', 'product_id', 'sheet_id', 'position', 
            'image_type', 'row_number', 'product_name', 
            'ftp_url', 'match_type', 'total_duplicates'
        ])
        writer.writeheader()
        writer.writerows(resolved)
    
    print(f"✅ Сохранено {len(resolved):,} записей")
    return resolved


def main():
    print("=" * 80)
    print("🔍 ОБРАБОТКА МНОЖЕСТВЕННЫХ СОВПАДЕНИЙ")
    print("=" * 80)
    print()
    
    print("💡 Стратегия: выбираем первый URL из списка дублей для каждого изображения")
    print()
    
    resolved = process_multiple_matches(
        'IMAGES_MULTIPLE_MATCHES.csv',
        'IMAGES_MULTIPLE_RESOLVED.csv'
    )
    
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА")
    print("=" * 80)
    
    print(f"\n✅ Обработано записей: {len(resolved):,}")
    
    # Статистика по количеству дублей
    duplicate_counts = {}
    for item in resolved:
        count = item['total_duplicates']
        if count not in duplicate_counts:
            duplicate_counts[count] = 0
        duplicate_counts[count] += 1
    
    print(f"\n📊 Распределение по количеству дублей:")
    for count in sorted(duplicate_counts.keys(), key=lambda x: int(x), reverse=True)[:10]:
        print(f"   {count} дублей: {duplicate_counts[count]:,} записей")
    
    print("\n✅ ОБРАБОТКА ЗАВЕРШЕНА")
    print(f"\n📄 Результат: IMAGES_MULTIPLE_RESOLVED.csv")
    print(f"💡 Этот файл можно использовать для UPDATE вместе с IMAGES_TO_UPDATE_URL.csv")


if __name__ == '__main__':
    main()


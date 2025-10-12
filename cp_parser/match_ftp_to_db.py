#!/usr/bin/env python3
"""
Сравнение FTP файлов с БД для заполнения NULL URL
"""

import csv
import sys
sys.path.append('database')
from postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def get_db_images_without_url():
    """Получить изображения из БД где image_url IS NULL"""
    print("🔌 Подключение к БД...")
    
    db = PostgreSQLManager()
    
    query = text("""
        SELECT 
            i.id,
            i.product_id,
            i.table_id,
            i.cell_position,
            i.is_main_image,
            i.image_url,
            p.row_number,
            p.name as product_name
        FROM product_images i
        LEFT JOIN products p ON i.product_id = p.id
        WHERE i.image_url IS NULL
        ORDER BY i.table_id, i.cell_position
    """)
    
    print("📥 Получаю изображения без URL из БД...")
    
    with db.engine.connect() as conn:
        result = conn.execute(query)
        rows = result.fetchall()
    
    images = []
    for row in rows:
        images.append({
            'id': row[0],
            'product_id': row[1],
            'sheet_id': row[2],  # table_id
            'position': row[3],   # cell_position
            'image_type': row[4], # is_main_image
            'image_url': row[5],
            'row_number': row[6],
            'product_name': row[7]
        })
    
    print(f"✅ Найдено {len(images):,} изображений без URL")
    return images


def load_ftp_files(csv_file):
    """Загрузить список файлов с FTP из CSV"""
    print(f"\n📄 Читаю FTP файлы из {csv_file}...")
    
    ftp_files = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sheet_id = row['sheet_id']
            position = row['position']
            suffix = row['suffix']
            image_url = row['image_url']
            
            # Создаем ключи для поиска
            # 1. Без суффикса: sheet_id + position
            # 2. С суффиксом: sheet_id + position + suffix
            
            if suffix:
                # С суффиксом
                key = f"{sheet_id}|{position}|{suffix}"
            else:
                # Без суффикса (основное изображение)
                key = f"{sheet_id}|{position}|"
            
            # Храним список URL для каждого ключа (могут быть дубли)
            if key not in ftp_files:
                ftp_files[key] = []
            ftp_files[key].append(image_url)
    
    print(f"✅ Загружено {len(ftp_files):,} уникальных комбинаций (sheet_id + position + suffix)")
    return ftp_files


def match_images(db_images, ftp_files):
    """Сопоставить изображения из БД с файлами на FTP"""
    print("\n🔍 Сопоставление изображений...")
    
    matched = []
    not_matched = []
    multiple_matches = []
    
    for i, img in enumerate(db_images, 1):
        if i % 5000 == 0:
            print(f"   Обработано: {i:,} / {len(db_images):,} ({i/len(db_images)*100:.1f}%)")
        
        sheet_id = img['sheet_id']
        position = img['position']
        
        # Пытаемся найти по разным комбинациям
        # 1. Сначала ищем без суффикса (основное изображение)
        key = f"{sheet_id}|{position}|"
        
        if key in ftp_files:
            urls = ftp_files[key]
            if len(urls) == 1:
                matched.append({
                    **img,
                    'ftp_url': urls[0],
                    'match_type': 'exact',
                    'suffix': ''
                })
            else:
                # Несколько файлов для одной позиции (дубли)
                multiple_matches.append({
                    **img,
                    'ftp_urls': urls,
                    'match_type': 'multiple',
                    'count': len(urls)
                })
        else:
            # Не найдено - может быть с суффиксом?
            # Попробуем найти с любым суффиксом
            found = False
            for suffix in ['1', '2', '3', '4', '5']:
                key_with_suffix = f"{sheet_id}|{position}|{suffix}"
                if key_with_suffix in ftp_files:
                    urls = ftp_files[key_with_suffix]
                    matched.append({
                        **img,
                        'ftp_url': urls[0],  # Берем первый если есть дубли
                        'match_type': 'with_suffix',
                        'suffix': suffix
                    })
                    found = True
                    break
            
            if not found:
                not_matched.append(img)
    
    print(f"\n✅ Сопоставление завершено:")
    print(f"   Найдено совпадений: {len(matched):,}")
    print(f"   Множественных совпадений: {len(multiple_matches):,}")
    print(f"   Не найдено на FTP: {len(not_matched):,}")
    
    return matched, multiple_matches, not_matched


def main():
    print("=" * 80)
    print("🔗 СОПОСТАВЛЕНИЕ FTP ФАЙЛОВ С БД")
    print("=" * 80)
    print()
    
    # 1. Получаем изображения без URL из БД
    db_images = get_db_images_without_url()
    
    if not db_images:
        print("\n🎉 Все изображения в БД уже имеют URL!")
        return
    
    # 2. Загружаем список FTP файлов
    ftp_files = load_ftp_files('FTP_FILES_ANALYSIS.csv')
    
    # 3. Сопоставляем
    matched, multiple_matches, not_matched = match_images(db_images, ftp_files)
    
    # 4. Сохраняем результаты
    
    # 4.1. Основной файл для UPDATE - однозначные совпадения
    output_file = 'IMAGES_TO_UPDATE_URL.csv'
    print(f"\n💾 Сохраняю основной список для UPDATE: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'image_id', 
            'product_id', 
            'sheet_id', 
            'position', 
            'suffix',
            'image_type',
            'row_number',
            'product_name',
            'ftp_url',
            'match_type'
        ])
        
        for img in matched:
            writer.writerow([
                img['id'],
                img['product_id'],
                img['sheet_id'],
                img['position'],
                img.get('suffix', ''),
                img['image_type'],
                img.get('row_number', ''),
                img.get('product_name', ''),
                img['ftp_url'],
                img['match_type']
            ])
    
    print(f"✅ Сохранено {len(matched):,} записей для UPDATE")
    
    # 4.2. Множественные совпадения (дубли) - требуется ручной выбор
    if multiple_matches:
        multiple_file = 'IMAGES_MULTIPLE_MATCHES.csv'
        print(f"\n💾 Сохраняю множественные совпадения: {multiple_file}")
        
        with open(multiple_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'image_id',
                'product_id',
                'sheet_id',
                'position',
                'image_type',
                'row_number',
                'product_name',
                'urls_count',
                'ftp_urls'
            ])
            
            for img in multiple_matches:
                writer.writerow([
                    img['id'],
                    img['product_id'],
                    img['sheet_id'],
                    img['position'],
                    img['image_type'],
                    img.get('row_number', ''),
                    img.get('product_name', ''),
                    img['count'],
                    ' | '.join(img['ftp_urls'])
                ])
        
        print(f"⚠️  Сохранено {len(multiple_matches):,} записей с множественными совпадениями")
    
    # 4.3. Не найденные на FTP
    if not_matched:
        not_found_file = 'IMAGES_NOT_FOUND_ON_FTP.csv'
        print(f"\n💾 Сохраняю не найденные на FTP: {not_found_file}")
        
        with open(not_found_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'image_id',
                'product_id',
                'sheet_id',
                'position',
                'image_type',
                'row_number',
                'product_name'
            ])
            
            for img in not_matched:
                writer.writerow([
                    img['id'],
                    img['product_id'],
                    img['sheet_id'],
                    img['position'],
                    img['image_type'],
                    img.get('row_number', ''),
                    img.get('product_name', '')
                ])
        
        print(f"❌ Сохранено {len(not_matched):,} изображений не найденных на FTP")
    
    # 5. Статистика
    print("\n" + "=" * 80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    
    print(f"\n📊 ИЗОБРАЖЕНИЯ В БД БЕЗ URL:")
    print(f"   Всего: {len(db_images):,}")
    
    print(f"\n✅ НАЙДЕНО НА FTP (готово к UPDATE):")
    print(f"   Однозначные совпадения: {len(matched):,}")
    print(f"   - Точные (без суффикса): {len([m for m in matched if m['match_type'] == 'exact']):,}")
    print(f"   - С суффиксом: {len([m for m in matched if m['match_type'] == 'with_suffix']):,}")
    
    if multiple_matches:
        print(f"\n⚠️  МНОЖЕСТВЕННЫЕ СОВПАДЕНИЯ (требуют проверки):")
        print(f"   Записей: {len(multiple_matches):,}")
        print(f"   Всего файлов-дублей: {sum(m['count'] for m in multiple_matches):,}")
    
    if not_matched:
        print(f"\n❌ НЕ НАЙДЕНО НА FTP:")
        print(f"   Записей: {len(not_matched):,}")
        print(f"   Причины:")
        print(f"   - Файлы не были загружены")
        print(f"   - Ошибка парсинга имени файла")
        print(f"   - Несовпадение sheet_id или position")
    
    # Покрытие
    coverage = (len(matched) / len(db_images) * 100) if db_images else 0
    print(f"\n📈 ПОКРЫТИЕ:")
    print(f"   {coverage:.1f}% изображений можно обновить")
    
    print("\n" + "=" * 80)
    print("✅ АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)
    
    print(f"\n📄 Основной файл для UPDATE: {output_file}")
    if multiple_matches:
        print(f"📄 Множественные совпадения: {multiple_file}")
    if not_matched:
        print(f"📄 Не найденные: {not_found_file}")
    
    print(f"\n💡 СЛЕДУЮЩИЙ ШАГ:")
    print(f"   1. Проверь файл {output_file}")
    print(f"   2. Запусти UPDATE для заполнения URL в БД")
    if multiple_matches:
        print(f"   3. Обработай множественные совпадения вручную")


if __name__ == '__main__':
    main()


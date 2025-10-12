#!/usr/bin/env python3
"""
Удаление полных дублей с FTP (одинаковый размер)
Оставляем только 1 файл из каждой группы дублей
"""

import csv
from ftplib import FTP
import os
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()


def load_duplicates_summary(csv_file):
    """Загрузить сводку дублей"""
    print(f"📄 Читаю файл: {csv_file}")
    
    groups = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Фильтруем только группы с одинаковым размером (точные дубли)
            if row['same_size'] == 'ДА':
                groups.append({
                    'sheet_id': row['sheet_id'],
                    'position': row['position'],
                    'suffix': row['suffix'],
                    'duplicate_count': int(row['duplicate_count']),
                    'total_size_mb': float(row['total_size_mb']),
                    'key': f"{row['sheet_id']}|{row['position']}|{row['suffix']}"
                })
    
    print(f"✅ Найдено {len(groups):,} групп с одинаковым размером (точные дубли)")
    return groups


def load_duplicates_detail(csv_file):
    """Загрузить детали дублей"""
    print(f"📄 Читаю файл: {csv_file}")
    
    files_by_group = defaultdict(list)
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = f"{row['sheet_id']}|{row['position']}|{row['suffix']}"
            files_by_group[key].append({
                'filename': row['filename'],
                'size_mb': float(row['size_mb']),
                'url': row['image_url']
            })
    
    print(f"✅ Загружено файлов: {sum(len(files) for files in files_by_group.values()):,}")
    return files_by_group


def prepare_deletion_list(groups, files_by_group):
    """Подготовить список файлов для удаления"""
    print("\n🔍 Подготовка списка для удаления...")
    
    to_keep = []
    to_delete = []
    
    for group in groups:
        key = group['key']
        files = files_by_group.get(key, [])
        
        if len(files) > 1:
            # Оставляем первый файл, остальные удаляем
            to_keep.append(files[0])
            to_delete.extend(files[1:])
    
    print(f"✅ Будет оставлено: {len(to_keep):,} файлов")
    print(f"🗑️  Будет удалено: {len(to_delete):,} файлов")
    
    # Подсчет освобождаемого места
    space_freed = sum(f['size_mb'] for f in to_delete)
    print(f"💾 Освободится места: {space_freed:.2f} MB ({space_freed/1024:.2f} GB)")
    
    return to_keep, to_delete


def delete_files_from_ftp(files_to_delete, dry_run=True):
    """Удалить файлы с FTP"""
    if dry_run:
        print("\n⚠️  DRY RUN MODE - файлы НЕ будут удалены!")
        print("   Только симуляция для проверки")
        return 0, 0
    
    print("\n🔌 Подключение к FTP...")
    
    try:
        ftp = FTP()
        ftp.connect(os.getenv('FTP_HOST'), int(os.getenv('FTP_PORT', 21)))
        ftp.login(os.getenv('FTP_USER'), os.getenv('FTP_PASSWORD'))
        ftp.cwd('/73d16f7545b3-promogoods/images')
        
        print("✅ Подключено к FTP")
        print(f"\n🗑️  Удаление {len(files_to_delete):,} файлов...")
        
        deleted = 0
        failed = 0
        
        for i, file_info in enumerate(files_to_delete, 1):
            filename = file_info['filename']
            
            try:
                ftp.delete(filename)
                deleted += 1
                
                if i % 100 == 0:
                    progress = i / len(files_to_delete) * 100
                    print(f"   Удалено: {deleted:,} / {len(files_to_delete):,} ({progress:.1f}%)")
                    
            except Exception as e:
                failed += 1
                if failed <= 10:  # Показываем первые 10 ошибок
                    print(f"   ❌ Ошибка удаления {filename}: {e}")
        
        ftp.quit()
        
        print(f"\n✅ Удалено: {deleted:,}")
        if failed > 0:
            print(f"❌ Ошибок: {failed:,}")
        
        return deleted, failed
        
    except Exception as e:
        print(f"❌ Ошибка подключения к FTP: {e}")
        return 0, len(files_to_delete)


def save_deletion_list(files_to_delete, output_file):
    """Сохранить список файлов для удаления"""
    print(f"\n💾 Сохраняю список для удаления: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'size_mb', 'url'])
        
        for file_info in files_to_delete:
            writer.writerow([
                file_info['filename'],
                file_info['size_mb'],
                file_info['url']
            ])
    
    print(f"✅ Сохранено {len(files_to_delete):,} записей")


def main():
    print("=" * 80)
    print("🗑️  УДАЛЕНИЕ ДУБЛЕЙ С FTP")
    print("=" * 80)
    print()
    
    # 1. Загружаем сводку и детали дублей
    groups = load_duplicates_summary('REAL_DUPLICATES_SUMMARY.csv')
    files_by_group = load_duplicates_detail('REAL_DUPLICATES_DETAIL.csv')
    
    # 2. Подготавливаем список для удаления
    to_keep, to_delete = prepare_deletion_list(groups, files_by_group)
    
    # 3. Сохраняем список
    save_deletion_list(to_delete, 'FTP_FILES_TO_DELETE.csv')
    
    # 4. Статистика
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА")
    print("=" * 80)
    
    print(f"\n📁 Групп дублей с одинаковым размером: {len(groups):,}")
    print(f"✅ Файлов будет оставлено: {len(to_keep):,}")
    print(f"🗑️  Файлов будет удалено: {len(to_delete):,}")
    
    space_freed = sum(f['size_mb'] for f in to_delete)
    print(f"\n💾 ОСВОБОЖДЕНИЕ МЕСТА:")
    print(f"   {space_freed:.2f} MB ({space_freed/1024:.2f} GB)")
    
    # 5. Подтверждение удаления
    print("\n" + "=" * 80)
    print("⚠️  ВНИМАНИЕ!")
    print("=" * 80)
    print(f"\n🗑️  Будет БЕЗВОЗВРАТНО удалено {len(to_delete):,} файлов с FTP")
    print(f"💾 Освободится {space_freed/1024:.2f} GB")
    print(f"\n📄 Список файлов сохранен в: FTP_FILES_TO_DELETE.csv")
    
    print("\n❓ Выберите действие:")
    print("   1 - Dry run (симуляция без удаления)")
    print("   2 - УДАЛИТЬ файлы")
    print("   3 - Отмена")
    
    choice = input("\nВаш выбор (1/2/3): ").strip()
    
    if choice == '1':
        print("\n🔍 DRY RUN MODE...")
        delete_files_from_ftp(to_delete, dry_run=True)
        print("\n✅ Dry run завершен. Файлы НЕ были удалены.")
        
    elif choice == '2':
        print("\n⚠️⚠️⚠️  ПОСЛЕДНЕЕ ПРЕДУПРЕЖДЕНИЕ! ⚠️⚠️⚠️")
        print(f"Вы собираетесь БЕЗВОЗВРАТНО удалить {len(to_delete):,} файлов!")
        confirm = input("\nВведите 'DELETE' для подтверждения: ").strip()
        
        if confirm == 'DELETE':
            deleted, failed = delete_files_from_ftp(to_delete, dry_run=False)
            
            print("\n" + "=" * 80)
            print("📊 ИТОГИ УДАЛЕНИЯ")
            print("=" * 80)
            print(f"\n✅ Удалено файлов: {deleted:,}")
            if failed > 0:
                print(f"❌ Ошибок: {failed:,}")
            
            actual_freed = sum(f['size_mb'] for f in to_delete[:deleted])
            print(f"\n💾 Освобождено места: {actual_freed:.2f} MB ({actual_freed/1024:.2f} GB)")
        else:
            print("\n❌ Неверное подтверждение. Отменено.")
    else:
        print("\n❌ Отменено пользователем")
    
    print("\n✅ ЗАВЕРШЕНО")


if __name__ == '__main__':
    main()


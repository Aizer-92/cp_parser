#!/usr/bin/env python3
"""
UPDATE скрипт для заполнения image_url в БД
"""

import csv
import sys
sys.path.append('database')
from postgresql_manager import PostgreSQLManager
from sqlalchemy import text

def load_updates(csv_file):
    """Загрузить список изображений для обновления"""
    print(f"📄 Читаю файл: {csv_file}")
    
    updates = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            updates.append({
                'image_id': int(row['image_id']),
                'ftp_url': row['ftp_url']
            })
    
    print(f"✅ Загружено {len(updates):,} записей для UPDATE")
    return updates


def update_urls_in_batches(updates, batch_size=100):
    """Обновить URL в БД батчами"""
    db = PostgreSQLManager()
    
    total = len(updates)
    updated = 0
    failed = 0
    
    print(f"\n🔄 Начинаю UPDATE (батчами по {batch_size})...")
    
    for i in range(0, total, batch_size):
        batch = updates[i:i+batch_size]
        
        try:
            with db.engine.connect() as conn:
                # Начинаем транзакцию
                trans = conn.begin()
                
                try:
                    for item in batch:
                        query = text("""
                            UPDATE product_images
                            SET image_url = :url,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :id
                        """)
                        
                        conn.execute(query, {'url': item['ftp_url'], 'id': item['image_id']})
                    
                    # Коммитим батч
                    trans.commit()
                    updated += len(batch)
                    
                    # Прогресс
                    progress = (i + len(batch)) / total * 100
                    print(f"   ✅ Обновлено: {updated:,} / {total:,} ({progress:.1f}%)")
                    
                except Exception as e:
                    trans.rollback()
                    print(f"   ❌ Ошибка в батче {i}-{i+len(batch)}: {e}")
                    failed += len(batch)
                    
        except Exception as e:
            print(f"   ❌ Ошибка подключения: {e}")
            failed += len(batch)
    
    return updated, failed


def main():
    print("=" * 80)
    print("🔄 UPDATE IMAGE URLs В БД")
    print("=" * 80)
    print()
    
    # 1. Загружаем список для обновления
    updates = load_updates('IMAGES_ALL_UPDATES.csv')
    
    # 2. Подтверждение
    print(f"\n⚠️  ВНИМАНИЕ!")
    print(f"   Будет обновлено {len(updates):,} записей в таблице product_images")
    print(f"   Поле image_url будет заполнено")
    
    response = input("\n❓ Продолжить? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Отменено пользователем")
        return
    
    # 3. Выполняем UPDATE
    updated, failed = update_urls_in_batches(updates, batch_size=100)
    
    # 4. Итоги
    print("\n" + "=" * 80)
    print("📊 ИТОГИ UPDATE")
    print("=" * 80)
    print(f"\n✅ Успешно обновлено: {updated:,}")
    if failed > 0:
        print(f"❌ Ошибок: {failed:,}")
    
    success_rate = (updated / len(updates) * 100) if updates else 0
    print(f"\n📈 Успешность: {success_rate:.1f}%")
    
    print("\n✅ UPDATE ЗАВЕРШЕН")


if __name__ == '__main__':
    main()


#!/usr/bin/env python3
"""
Восстановление тиражей из бэкапа
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv as csv_lib

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def restore_from_backup(db, backup_file):
    """Восстанавливает quantity из бэкапа"""
    print(f"\n📂 Читаю бэкап: {backup_file}", flush=True)
    
    updates = []
    with open(backup_file, 'r', encoding='utf-8') as f:
        reader = csv_lib.DictReader(f)
        for row in reader:
            updates.append({
                'id': int(row['ID_Оффера']),
                'quantity': int(row['Quantity_OLD'])
            })
    
    print(f"✅ Найдено записей: {len(updates)}", flush=True)
    
    print(f"\n🔧 Восстанавливаю тиражи...", flush=True)
    
    with db.get_session() as session:
        for upd in updates:
            session.execute(text("""
                UPDATE price_offers
                SET quantity = :qty
                WHERE id = :id
            """), {'id': upd['id'], 'qty': upd['quantity']})
        
        session.commit()
    
    print(f"✅ Восстановлено: {len(updates)} офферов", flush=True)

def main():
    if len(sys.argv) < 2:
        print("❌ Использование: python3 restore_backup.py <backup_file.csv>", flush=True)
        return
    
    backup_file = sys.argv[1]
    
    if not Path(backup_file).exists():
        print(f"❌ Файл не найден: {backup_file}", flush=True)
        return
    
    print("="*80, flush=True)
    print("🔄 ВОССТАНОВЛЕНИЕ ИЗ БЭКАПА", flush=True)
    print("="*80, flush=True)
    
    db = PostgreSQLManager()
    
    print("\n⚠️  ВНИМАНИЕ! Будут восстановлены старые значения quantity", flush=True)
    response = input("❓ Продолжить? (введите 'ДА'): ")
    
    if response.strip().upper() != 'ДА':
        print("\n❌ Операция отменена", flush=True)
        return
    
    restore_from_backup(db, backup_file)
    
    print("\n✅ ВОССТАНОВЛЕНИЕ ЗАВЕРШЕНО!", flush=True)

if __name__ == '__main__':
    main()


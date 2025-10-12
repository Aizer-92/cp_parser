#!/usr/bin/env python3
"""
Исправление ошибок x10 в тиражах Template 4
БЕЗОПАСНОЕ исправление с бэкапом и возможностью отката
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import os
import csv as csv_lib
from datetime import datetime

# Railway DB
os.environ['USE_RAILWAY_DB'] = 'true'

def create_backup(db, offer_ids):
    """Создает бэкап офферов перед изменением"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"BACKUP_BEFORE_FIX_{timestamp}.csv"
    
    print(f"\n📦 Создаю бэкап...", flush=True)
    
    with db.get_session() as session:
        # Получаем данные офферов
        offers = session.execute(text("""
            SELECT 
                po.id,
                po.product_id,
                po.quantity,
                po.route,
                po.price_usd,
                po.price_rub,
                p.project_id,
                pr.project_name
            FROM price_offers po
            INNER JOIN products p ON po.product_id = p.id
            INNER JOIN projects pr ON p.project_id = pr.id
            WHERE po.id = ANY(:ids)
            ORDER BY po.id
        """), {'ids': offer_ids}).fetchall()
        
        # Сохраняем в CSV
        with open(backup_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv_lib.writer(f)
            writer.writerow(['ID_Оффера', 'ID_Товара', 'ID_Проекта', 'Название_Проекта',
                           'Quantity_OLD', 'Маршрут', 'Price_USD', 'Price_RUB'])
            
            for offer in offers:
                writer.writerow([
                    offer.id,
                    offer.product_id,
                    offer.project_id,
                    offer.project_name,
                    offer.quantity,
                    offer.route,
                    offer.price_usd,
                    offer.price_rub
                ])
        
        print(f"✅ Бэкап создан: {backup_file}", flush=True)
        print(f"   Сохранено: {len(offers)} офферов", flush=True)
        
        return backup_file

def update_quantities(db, offer_ids):
    """Обновляет quantity для офферов (делит на 10)"""
    print(f"\n🔧 Исправляю тиражи...", flush=True)
    
    with db.get_session() as session:
        result = session.execute(text("""
            UPDATE price_offers
            SET quantity = quantity / 10
            WHERE id = ANY(:ids)
            RETURNING id, quantity
        """), {'ids': offer_ids})
        
        updated = result.fetchall()
        session.commit()
        
        print(f"✅ Обновлено: {len(updated)} офферов", flush=True)
        
        # Показываем примеры
        print(f"\n📊 Примеры обновленных тиражей (первые 10):", flush=True)
        for i, row in enumerate(updated[:10], 1):
            print(f"   {i}. Оффер {row.id}: новый тираж = {row.quantity}", flush=True)
        
        if len(updated) > 10:
            print(f"   ... и еще {len(updated) - 10} офферов", flush=True)
        
        return len(updated)

def verify_update(db, offer_ids):
    """Проверяет что обновление прошло успешно"""
    print(f"\n🔍 Проверяю результаты...", flush=True)
    
    with db.get_session() as session:
        # Проверяем что тиражи делятся на 10 (т.е. не были исправлены)
        still_x10 = session.execute(text("""
            SELECT COUNT(*)
            FROM price_offers
            WHERE id = ANY(:ids)
            AND quantity >= 300
            AND quantity % 10 = 0
        """), {'ids': offer_ids}).scalar()
        
        if still_x10 > 0:
            print(f"⚠️  ВНИМАНИЕ: {still_x10} офферов все еще делятся на 10", flush=True)
            print(f"   Это нормально если там были корректные тиражи (3000, 5000 и т.д.)", flush=True)
        else:
            print(f"✅ Все офферы успешно исправлены!", flush=True)
        
        # Статистика по новым тиражам
        stats = session.execute(text("""
            SELECT 
                COUNT(*) as total,
                MIN(quantity) as min_qty,
                MAX(quantity) as max_qty,
                AVG(quantity) as avg_qty
            FROM price_offers
            WHERE id = ANY(:ids)
        """), {'ids': offer_ids}).first()
        
        print(f"\n📊 Статистика после исправления:", flush=True)
        print(f"   Всего офферов: {stats.total}", flush=True)
        print(f"   Мин. тираж: {stats.min_qty}", flush=True)
        print(f"   Макс. тираж: {stats.max_qty}", flush=True)
        print(f"   Средний: {stats.avg_qty:.1f}", flush=True)

def main():
    print("="*80, flush=True)
    print("🔧 ИСПРАВЛЕНИЕ ОШИБОК x10 В ТИРАЖАХ", flush=True)
    print("="*80, flush=True)
    
    # Читаем список офферов для исправления
    fix_file = "ИСПРАВИТЬ_SMART_20251012_1358.csv"
    
    if not Path(fix_file).exists():
        print(f"❌ Файл не найден: {fix_file}", flush=True)
        print(f"💡 Сначала запустите: python3 check_quantities_smart.py", flush=True)
        return
    
    print(f"\n📂 Читаю файл: {fix_file}", flush=True)
    
    offer_ids = []
    with open(fix_file, 'r', encoding='utf-8') as f:
        reader = csv_lib.DictReader(f)
        for row in reader:
            offer_ids.append(int(row['ID_Оффера']))
    
    print(f"✅ Найдено офферов для исправления: {len(offer_ids)}", flush=True)
    
    # Подключаемся к БД
    print(f"\n📊 Подключаюсь к Railway БД...", flush=True)
    db = PostgreSQLManager()
    
    # Создаем бэкап
    backup_file = create_backup(db, offer_ids)
    
    # КРИТИЧЕСКИЙ МОМЕНТ - подтверждение
    print("\n" + "="*80, flush=True)
    print("⚠️  ВНИМАНИЕ! КРИТИЧЕСКИЙ МОМЕНТ!", flush=True)
    print("="*80, flush=True)
    print(f"Будет изменено: {len(offer_ids)} офферов", flush=True)
    print(f"Операция: quantity = quantity / 10", flush=True)
    print(f"Бэкап создан: {backup_file}", flush=True)
    print(f"\nДля отката используйте скрипт restore с бэкап-файлом", flush=True)
    print("="*80, flush=True)
    
    response = input("\n❓ Продолжить? (введите 'ДА' для подтверждения): ")
    
    if response.strip().upper() != 'ДА':
        print("\n❌ Операция отменена пользователем", flush=True)
        print(f"💾 Бэкап сохранен: {backup_file}", flush=True)
        return
    
    # Выполняем обновление
    print("\n🚀 НАЧИНАЮ ОБНОВЛЕНИЕ...", flush=True)
    updated_count = update_quantities(db, offer_ids)
    
    # Проверяем результаты
    verify_update(db, offer_ids)
    
    # Итоговый отчет
    print("\n" + "="*80, flush=True)
    print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО!", flush=True)
    print("="*80, flush=True)
    print(f"📊 Обновлено офферов: {updated_count}", flush=True)
    print(f"💾 Бэкап: {backup_file}", flush=True)
    print(f"\n💡 Для отката используйте:", flush=True)
    print(f"   python3 restore_backup.py {backup_file}", flush=True)
    print("="*80, flush=True)

if __name__ == '__main__':
    main()


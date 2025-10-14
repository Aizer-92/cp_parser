#!/usr/bin/env python3
"""
Отслеживание прогресса парсинга Template 7
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import json
import time
from datetime import datetime

# Загружаем список Template 7
with open('TEMPLATE7_FILTERED_RESULTS.json', 'r') as f:
    data = json.load(f)
template7_ids = [int(pid) for pid in data.get('template7_projects', [])]

# ID последнего товара из тестового запуска (проект 1188)
BASELINE_ID = 25680

db = PostgreSQLManager()

print(f"\n{'='*80}")
print(f"📊 МОНИТОРИНГ ПАРСИНГА TEMPLATE 7")
print(f"{'='*80}")
print(f"Всего проектов Template 7: {len(template7_ids)}")
print(f"Базовый ID (последний из теста): {BASELINE_ID}")
print(f"Обновление каждые 10 секунд. Нажми Ctrl+C для выхода.")
print(f"{'='*80}\n")

try:
    prev_products = 0
    start_time = time.time()
    
    while True:
        with db.get_session() as session:
            # Текущий прогресс
            stats = session.execute(
                text("""
                    SELECT 
                        COUNT(DISTINCT p.project_id) as projects,
                        COUNT(p.id) as products,
                        COUNT(po.id) as offers,
                        COUNT(pi.id) as images,
                        MAX(p.id) as max_id
                    FROM products p
                    LEFT JOIN price_offers po ON p.id = po.product_id
                    LEFT JOIN product_images pi ON p.id = pi.product_id
                    WHERE p.id > :baseline
                      AND p.project_id = ANY(:pids)
                """),
                {'baseline': BASELINE_ID, 'pids': template7_ids}
            ).fetchone()
            
            projects, products, offers, images, max_id = stats
            
            # Скорость
            elapsed = time.time() - start_time
            speed = (products - prev_products) / 10 if elapsed > 10 else 0
            prev_products = products
            
            # Примерное время до конца
            remaining_projects = len(template7_ids) - projects - 1  # -1 это проект 1188
            eta_minutes = (remaining_projects / (projects / (elapsed / 60))) if projects > 0 and elapsed > 60 else 0
            
            # Очищаем экран (для macOS/Linux)
            print("\033[2J\033[H", end="")
            
            print(f"{'='*80}")
            print(f"📊 ПРОГРЕСС ПАРСИНГА TEMPLATE 7 - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*80}\n")
            
            print(f"✅ Обработано проектов:  {projects:>4} / 405  ({projects*100//405:>2}%)")
            print(f"   {'▓' * (projects * 60 // 405)}{'░' * (60 - projects * 60 // 405)}\n")
            
            print(f"📦 Товаров:       {products:>6,}")
            print(f"💰 Офферов:       {offers:>6,}")
            print(f"🖼️  Изображений:   {images:>6,}\n")
            
            if products > 0:
                print(f"📈 Средние показатели:")
                print(f"   Офферов на товар:      {offers/products:.1f}")
                print(f"   Изображений на товар:  {images/products:.1f}\n")
            
            print(f"⚡ Скорость:      {speed:.1f} товаров/10 сек")
            
            if eta_minutes > 0:
                hours = int(eta_minutes // 60)
                mins = int(eta_minutes % 60)
                print(f"⏱️  Осталось:      ~{hours}ч {mins}мин")
            
            print(f"\n💾 Последний ID товара: {max_id}")
            
            # Последние 5 обработанных проектов
            recent = session.execute(
                text("""
                    SELECT 
                        p.project_id,
                        COUNT(p.id) as products,
                        MAX(p.id) as last_id
                    FROM products p
                    WHERE p.id > :baseline
                      AND p.project_id = ANY(:pids)
                    GROUP BY p.project_id
                    ORDER BY last_id DESC
                    LIMIT 5
                """),
                {'baseline': BASELINE_ID, 'pids': template7_ids}
            ).fetchall()
            
            print(f"\n🆕 Последние 5 проектов:")
            for proj_id, prods, last_id in recent:
                print(f"   #{proj_id:<5} → {prods:>3} товаров")
            
            print(f"\n{'='*80}")
            print(f"Обновлено: {datetime.now().strftime('%H:%M:%S')} | Следующее через 10 сек...")
            
        time.sleep(10)

except KeyboardInterrupt:
    print(f"\n\n✅ Мониторинг остановлен\n")
except Exception as e:
    print(f"\n\n❌ Ошибка: {e}\n")


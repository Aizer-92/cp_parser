#!/usr/bin/env python3
"""
Мониторинг прогресса парсинга Template 7 (новые проекты)
"""
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text

db = PostgreSQLManager()

# Базовый ID - до запуска новых
BASELINE_ID = 25680

print("\n" + "="*80)
print("📊 МОНИТОРИНГ ПАРСИНГА TEMPLATE 7 (НОВЫЕ ПРОЕКТЫ)")
print("="*80)
print("Обновление каждые 10 секунд. Ctrl+C для выхода\n")

start_time = datetime.now()
prev_products = 0

try:
    while True:
        with db.get_session() as session:
            # Статистика новых товаров
            stats = session.execute(
                text("""
                    SELECT 
                        COUNT(DISTINCT p.project_id) as projects,
                        COUNT(p.id) as products,
                        COUNT(po.id) as offers,
                        COUNT(pi.id) as images
                    FROM products p
                    LEFT JOIN price_offers po ON p.id = po.product_id
                    LEFT JOIN product_images pi ON p.id = pi.product_id
                    WHERE p.id > :baseline
                """),
                {'baseline': BASELINE_ID}
            ).fetchone()
            
            projects, products, offers, images = stats
            
            # Скорость
            elapsed = (datetime.now() - start_time).total_seconds()
            speed = products / elapsed if elapsed > 0 else 0
            
            # Прогресс
            total_projects = 95
            progress_pct = (projects / total_projects * 100) if total_projects > 0 else 0
            
            # ETA
            remaining = total_projects - projects
            eta_seconds = remaining / (projects / elapsed) if projects > 0 and elapsed > 0 else 0
            eta_str = f"{int(eta_seconds // 60)}м {int(eta_seconds % 60)}с"
            
            # Прирост
            delta = products - prev_products
            prev_products = products
            
            # Вывод
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Проекты: {projects}/{total_projects} ({progress_pct:.1f}%) | "
                  f"Товары: {products:,} (+{delta}) | "
                  f"Офферы: {offers:,} | "
                  f"Изображения: {images:,} | "
                  f"Скорость: {speed:.1f} тов/сек | "
                  f"ETA: {eta_str}", end='', flush=True)
        
        time.sleep(10)
        
except KeyboardInterrupt:
    print("\n\n✅ Мониторинг остановлен\n")


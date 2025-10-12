#!/usr/bin/env python3
"""Мониторинг процесса допарсинга изображений"""

import sys
from pathlib import Path
from sqlalchemy import text
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()

# Читаем список проектов
with open('projects_need_images.txt', 'r') as f:
    project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]

total = len(project_ids)

print("=" * 80)
print("📊 МОНИТОРИНГ ДОПАРСИНГА ИЗОБРАЖЕНИЙ")
print("=" * 80)
print(f"\n📋 Всего проектов: {total}")

while True:
    with db.get_session() as session:
        # Считаем сколько товаров без изображений осталось
        products_no_images = session.execute(text("""
            SELECT COUNT(DISTINCT p.id)
            FROM products p
            WHERE p.project_id = ANY(:ids)
            AND NOT EXISTS (SELECT 1 FROM product_images pi WHERE pi.product_id = p.id)
        """), {'ids': project_ids}).scalar()
        
        # Всего изображений в этих проектах
        total_images = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
        """), {'ids': project_ids}).scalar()
    
    print(f"\n[{time.strftime('%H:%M:%S')}]")
    print(f"  📦 Товаров БЕЗ изображений: {products_no_images}")
    print(f"  🖼️  Всего изображений: {total_images}")
    
    # Проверяем процесс
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if 'redownload_and_reparse_images' in result.stdout:
        print(f"  ✅ Процесс работает")
    else:
        print(f"  ⏹️  Процесс завершен или не запущен")
        break
    
    time.sleep(30)

print("\n" + "=" * 80)



import sys
from pathlib import Path
from sqlalchemy import text
import time

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()

# Читаем список проектов
with open('projects_need_images.txt', 'r') as f:
    project_ids = [int(line.strip()) for line in f if line.strip().isdigit()]

total = len(project_ids)

print("=" * 80)
print("📊 МОНИТОРИНГ ДОПАРСИНГА ИЗОБРАЖЕНИЙ")
print("=" * 80)
print(f"\n📋 Всего проектов: {total}")

while True:
    with db.get_session() as session:
        # Считаем сколько товаров без изображений осталось
        products_no_images = session.execute(text("""
            SELECT COUNT(DISTINCT p.id)
            FROM products p
            WHERE p.project_id = ANY(:ids)
            AND NOT EXISTS (SELECT 1 FROM product_images pi WHERE pi.product_id = p.id)
        """), {'ids': project_ids}).scalar()
        
        # Всего изображений в этих проектах
        total_images = session.execute(text("""
            SELECT COUNT(*)
            FROM product_images pi
            JOIN products p ON pi.product_id = p.id
            WHERE p.project_id = ANY(:ids)
        """), {'ids': project_ids}).scalar()
    
    print(f"\n[{time.strftime('%H:%M:%S')}]")
    print(f"  📦 Товаров БЕЗ изображений: {products_no_images}")
    print(f"  🖼️  Всего изображений: {total_images}")
    
    # Проверяем процесс
    import subprocess
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if 'redownload_and_reparse_images' in result.stdout:
        print(f"  ✅ Процесс работает")
    else:
        print(f"  ⏹️  Процесс завершен или не запущен")
        break
    
    time.sleep(30)

print("\n" + "=" * 80)


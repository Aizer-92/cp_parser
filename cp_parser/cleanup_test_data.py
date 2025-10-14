#!/usr/bin/env python3
"""
Удаляет тестовые данные Template 7 из БД перед новым запуском
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from database.postgresql_manager import PostgreSQLManager
from sqlalchemy import text
import json

# Загружаем список тестовых проектов
with open('TEMPLATE7_FILTERED_RESULTS.json', 'r', encoding='utf-8') as f:
    template7_data = json.load(f)

project_ids = [int(pid) for pid in template7_data.get('template7_projects', [])[:10]]

print(f"\n🗑️  УДАЛЕНИЕ ТЕСТОВЫХ ДАННЫХ")
print(f"{'='*80}")
print(f"Проекты для очистки: {project_ids}")

db = PostgreSQLManager()

with db.get_session() as session:
    # Удаляем все товары из тестовых проектов
    for project_id in project_ids:
        # Сначала получаем ID товаров
        result = session.execute(
            text("SELECT id FROM products WHERE project_id = :pid"),
            {'pid': project_id}
        )
        product_ids = [row[0] for row in result.fetchall()]
        
        if product_ids:
            print(f"\n📦 Проект #{project_id}: {len(product_ids)} товаров")
            
            # Удаляем изображения
            images_deleted = session.execute(
                text("DELETE FROM product_images WHERE product_id = ANY(:pids)"),
                {'pids': product_ids}
            ).rowcount
            print(f"   🖼️  Удалено изображений: {images_deleted}")
            
            # Удаляем офферы
            offers_deleted = session.execute(
                text("DELETE FROM price_offers WHERE product_id = ANY(:pids)"),
                {'pids': product_ids}
            ).rowcount
            print(f"   💰 Удалено офферов: {offers_deleted}")
            
            # Удаляем товары
            products_deleted = session.execute(
                text("DELETE FROM products WHERE project_id = :pid"),
                {'pid': project_id}
            ).rowcount
            print(f"   ✅ Удалено товаров: {products_deleted}")
    
    session.commit()

print(f"\n{'='*80}")
print(f"✅ Тестовые данные удалены!")
print(f"{'='*80}\n")


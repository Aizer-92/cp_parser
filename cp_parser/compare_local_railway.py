#!/usr/bin/env python3
"""
Сравнение локальной БД и Railway для Шаблона 4
"""

import sys
from pathlib import Path
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

# Локальная БД
local_db = PostgreSQLManager()

# Railway БД
railway_engine = create_engine(
    'postgresql://postgres:dyLiJiVKlMSYHXdVOGzfXmCZZoQqhHTg@junction.proxy.rlwy.net:57758/railway',
    pool_pre_ping=True,
    pool_size=1,
    max_overflow=0
)
RailwaySession = sessionmaker(bind=railway_engine)

print("=" * 100)
print("🔍 СРАВНЕНИЕ ЛОКАЛЬНОЙ БД И RAILWAY - ШАБЛОН 4")
print("=" * 100)

with open('template_4_perfect_ids.txt', 'r') as f:
    project_ids = [int(line.strip()) for line in f if line.strip()]

print(f"\n📋 Проектов Шаблона 4: {len(project_ids)}")

# ЛОКАЛЬНАЯ БД
print("\n🏠 ЛОКАЛЬНАЯ БД:")
print("-" * 100)
with local_db.get_session() as session:
    local_stats = session.execute(text('''
        SELECT 
            COUNT(DISTINCT pr.id) as projects,
            COUNT(DISTINCT p.id) as products,
            COUNT(DISTINCT po.id) as offers,
            COUNT(DISTINCT pi.id) as images,
            COUNT(DISTINCT CASE WHEN pi.image_url IS NOT NULL AND pi.image_url != '' THEN pi.id END) as images_with_url
        FROM projects pr
        LEFT JOIN products p ON pr.id = p.project_id
        LEFT JOIN price_offers po ON p.id = po.product_id
        LEFT JOIN product_images pi ON p.id = pi.product_id
        WHERE pr.id = ANY(:ids)
    '''), {'ids': project_ids}).fetchone()
    
    local_projects, local_products, local_offers, local_images, local_images_url = local_stats
    
    # Образцы и дополнительные фото
    local_samples = session.execute(text('''
        SELECT COUNT(*) FROM products p
        WHERE p.project_id = ANY(:ids) AND custom_field LIKE '%Образец%'
    '''), {'ids': project_ids}).fetchone()[0]
    
    # Дополнительные фото (с суффиксами)
    all_images = session.execute(text('''
        SELECT image_filename FROM product_images pi
        JOIN products p ON pi.product_id = p.id
        WHERE p.project_id = ANY(:ids)
    '''), {'ids': project_ids}).fetchall()
    
    local_additional = sum(1 for (fn,) in all_images 
                          if len(fn.replace('.png','').split('_')) >= 4 
                          and fn.replace('.png','').split('_')[-2].isdigit())
    
    print(f"   Проекты:                   {local_projects:,}")
    print(f"   Товары:                    {local_products:,}")
    print(f"   Предложения:               {local_offers:,} ({local_offers/local_products:.2f} на товар)")
    print(f"   Изображения всего:         {local_images:,}")
    print(f"   - с URL:                   {local_images_url:,} ({local_images_url/local_images*100:.1f}%)")
    print(f"   - дополнительные (суфф.):  {local_additional:,}")
    print(f"   Товары с 'Образец':        {local_samples:,} ({local_samples/local_products*100:.1f}%)")

# RAILWAY БД
print("\n🚂 RAILWAY БД:")
print("-" * 100)
try:
    railway_session = RailwaySession()
    railway_stats = railway_session.execute(text('''
        SELECT 
            COUNT(DISTINCT pr.id) as projects,
            COUNT(DISTINCT p.id) as products,
            COUNT(DISTINCT po.id) as offers,
            COUNT(DISTINCT pi.id) as images,
            COUNT(DISTINCT CASE WHEN pi.image_url IS NOT NULL AND pi.image_url != '' THEN pi.id END) as images_with_url
        FROM projects pr
        LEFT JOIN products p ON pr.id = p.project_id
        LEFT JOIN price_offers po ON p.id = po.product_id
        LEFT JOIN product_images pi ON p.id = pi.product_id
        WHERE pr.id = ANY(:ids)
    '''), {'ids': project_ids}).fetchone()
    
    railway_projects, railway_products, railway_offers, railway_images, railway_images_url = railway_stats
    
    # Образцы
    railway_samples = railway_session.execute(text('''
        SELECT COUNT(*) FROM products p
        WHERE p.project_id = ANY(:ids) AND custom_field LIKE '%Образец%'
    '''), {'ids': project_ids}).fetchone()[0]
    
    # Дополнительные фото
    railway_all_images = railway_session.execute(text('''
        SELECT image_filename FROM product_images pi
        JOIN products p ON pi.product_id = p.id
        WHERE p.project_id = ANY(:ids)
    '''), {'ids': project_ids}).fetchall()
    
    railway_additional = sum(1 for (fn,) in railway_all_images 
                            if len(fn.replace('.png','').split('_')) >= 4 
                            and fn.replace('.png','').split('_')[-2].isdigit())
    
    print(f"   Проекты:                   {railway_projects:,}")
    print(f"   Товары:                    {railway_products:,}")
    print(f"   Предложения:               {railway_offers:,} ({railway_offers/railway_products:.2f} на товар если > 0)")
    print(f"   Изображения всего:         {railway_images:,}")
    print(f"   - с URL:                   {railway_images_url:,} ({railway_images_url/railway_images*100 if railway_images > 0 else 0:.1f}%)")
    print(f"   - дополнительные (суфф.):  {railway_additional:,}")
    print(f"   Товары с 'Образец':        {railway_samples:,} ({railway_samples/railway_products*100 if railway_products > 0 else 0:.1f}%)")
    
    # СРАВНЕНИЕ
    print("\n" + "=" * 100)
    print("📊 РАЗНИЦА (Railway - Локальная):")
    print("-" * 100)
    print(f"   Проекты:                   {railway_projects - local_projects:+,}")
    print(f"   Товары:                    {railway_products - local_products:+,}")
    print(f"   Предложения:               {railway_offers - local_offers:+,}")
    print(f"   Изображения всего:         {railway_images - local_images:+,}")
    print(f"   - с URL:                   {railway_images_url - local_images_url:+,}")
    print(f"   - дополнительные (суфф.):  {railway_additional - local_additional:+,}")
    print(f"   Товары с 'Образец':        {railway_samples - local_samples:+,}")
    
    print("\n" + "=" * 100)
    if railway_products == local_products and railway_offers == local_offers and railway_images_url == local_images_url:
        print("✅ БАЗЫ ИДЕНТИЧНЫ! Миграция уже выполнена корректно.")
    elif railway_products > 0:
        print("⚠️  На Railway уже есть данные Шаблона 4, но они отличаются.")
        print("    Возможно нужна синхронизация или данные обновлены частично.")
    else:
        print("📦 На Railway НЕТ данных Шаблона 4. Нужна полная миграция.")
    print("=" * 100)
    
    railway_session.close()
    
except Exception as e:
    print(f"❌ ОШИБКА подключения к Railway: {type(e).__name__}")
    print(f"   {str(e)}")
    print("\n⚠️  Не удалось получить данные с Railway для сравнения")
    print("=" * 100)





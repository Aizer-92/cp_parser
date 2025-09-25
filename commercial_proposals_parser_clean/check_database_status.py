#!/usr/bin/env python3
"""
Проверка статуса базы данных - что уже есть и что нужно сделать
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import ProjectMetadata, SheetMetadata, Product, ProductImage, PriceOffer
from sqlalchemy import func
from config import STORAGE_DIR

def check_database_status():
    """Проверяем полный статус базы данных"""
    
    session = DatabaseManager.get_session()
    
    try:
        print("📊 ПОЛНЫЙ СТАТУС БАЗЫ ДАННЫХ")
        print("=" * 80)
        
        # 1. ProjectMetadata (мастер-таблица)
        total_projects = session.query(ProjectMetadata).count()
        projects_with_urls = session.query(ProjectMetadata).filter(
            ProjectMetadata.google_sheets_url.isnot(None),
            ProjectMetadata.google_sheets_url != ''
        ).count()
        
        print(f"📋 МАСТЕР-ТАБЛИЦА (ProjectMetadata):")
        print(f"   📊 Всего записей: {total_projects}")
        print(f"   🔗 С URL таблиц: {projects_with_urls}")
        print()
        
        # 2. SheetMetadata (локальные таблицы)
        total_sheets = session.query(SheetMetadata).count()
        
        # Статусы (общий статус в модели)
        statuses = session.query(
            SheetMetadata.status,
            func.count(SheetMetadata.id)
        ).group_by(SheetMetadata.status).all()
        
        # Наличие локальных файлов
        with_files = session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.isnot(None)
        ).count()
        without_files = total_sheets - with_files
        
        print(f"📑 ЛОКАЛЬНЫЕ ТАБЛИЦЫ (SheetMetadata):")
        print(f"   📊 Всего записей: {total_sheets}")
        print(f"   📁 Локальные файлы:")
        print(f"      Скачаны: {with_files}")
        print(f"      Не скачаны: {without_files}")
        print(f"   ⚙️  Общий статус:")
        for status, count in statuses:
            status_name = status or "pending" 
            print(f"      {status_name}: {count}")
        print()
        
        # 3. Скачанные файлы
        excel_dir = STORAGE_DIR / "excel_files"
        if excel_dir.exists():
            downloaded_files = list(excel_dir.glob("*.xlsx"))
            print(f"💾 СКАЧАННЫЕ ФАЙЛЫ:")
            print(f"   📁 Папка: {excel_dir}")
            print(f"   📄 Файлов: {len(downloaded_files)}")
        else:
            print(f"💾 СКАЧАННЫЕ ФАЙЛЫ: папка не найдена")
        print()
        
        # 4. Парсенные данные
        total_products = session.query(Product).count()
        total_images = session.query(ProductImage).count()
        
        # Продукты с ценами (через PriceOffer)
        products_with_prices = session.query(Product).join(PriceOffer).filter(
            PriceOffer.price_usd.isnot(None),
            PriceOffer.price_usd > 0
        ).count()
        
        print(f"📦 ПАРСЕННЫЕ ДАННЫЕ:")
        print(f"   🛍️  Всего товаров: {total_products}")
        price_percentage = (products_with_prices/total_products*100) if total_products > 0 else 0
        print(f"   💰 С ценами: {products_with_prices} ({price_percentage:.1f}%)")
        print(f"   🖼️  Изображений: {total_images}")
        print()
        
        # 5. Рекомендации
        print(f"🎯 РЕКОМЕНДАЦИИ:")
        
        # Нужно ли скачивать файлы?
        sheets_need_download = session.query(SheetMetadata).filter(
            SheetMetadata.local_file_path.is_(None)
        ).count()
        
        if sheets_need_download > 0:
            print(f"   📥 Нужно скачать файлов: {sheets_need_download}")
        else:
            print(f"   ✅ Все файлы скачаны")
            
        # Нужно ли парсить?
        sheets_need_parsing = session.query(SheetMetadata).filter(
            SheetMetadata.status != 'completed',
            SheetMetadata.local_file_path.isnot(None)  # Только скачанные
        ).count()
        
        if sheets_need_parsing > 0:
            print(f"   ⚙️  Нужно парсить таблиц: {sheets_need_parsing}")
        else:
            print(f"   ✅ Все таблицы парсены")
        
        print()
        
        # Показать следующие 10 таблиц для парсинга
        if sheets_need_parsing > 0:
            next_to_parse = session.query(SheetMetadata).filter(
                SheetMetadata.status != 'completed',
                SheetMetadata.local_file_path.isnot(None)
            ).limit(10).all()
            
            print(f"🎯 СЛЕДУЮЩИЕ 10 ТАБЛИЦ ДЛЯ ПАРСИНГА:")
            print("-" * 60)
            for i, sheet in enumerate(next_to_parse, 1):
                print(f"{i:2d}. {sheet.sheet_title}")
                print(f"     ID: {sheet.sheet_id}")
                print(f"     Файл: {'✅' if sheet.local_file_path else '❌'}")
                print(f"     Статус: {sheet.status or 'pending'}")
                print()
        
    finally:
        session.close()

if __name__ == "__main__":
    check_database_status()

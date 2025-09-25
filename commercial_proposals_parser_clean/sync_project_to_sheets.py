#!/usr/bin/env python3
"""
Синхронизация ProjectMetadata -> SheetMetadata
Создает записи в SheetMetadata из неимпортированных ProjectMetadata
"""

import sys
import os
from datetime import datetime
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import ProjectMetadata, SheetMetadata

def extract_sheet_id(url):
    """Извлекает ID Google Sheets из URL"""
    if not url:
        return None
    
    # Паттерн для извлечения ID из различных форматов URL
    patterns = [
        r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
        r'key=([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def generate_sheet_title(project_title, project_date=None):
    """Генерирует название листа на основе названия и даты"""
    if not project_title:
        project_title = "Unknown"
    
    # Очищаем название от лишних символов
    clean_title = re.sub(r'[^\w\s\-.]', '', project_title)[:50]
    
    if project_date:
        try:
            if isinstance(project_date, str):
                # Пытаемся парсить дату из строки
                date_str = project_date[:10]  # Берем первые 10 символов (YYYY-MM-DD)
            else:
                date_str = project_date.strftime('%Y%m%d')
            return f"google_sheet_{date_str}_{clean_title}".replace(' ', '_')
        except:
            pass
    
    # Если дата не определена, используем текущую
    current_date = datetime.now().strftime('%Y%m%d')
    return f"google_sheet_{current_date}_{clean_title}".replace(' ', '_')

def sync_projects_to_sheets():
    """Синхронизирует ProjectMetadata с SheetMetadata"""
    
    session = DatabaseManager.get_session()
    
    try:
        # Получаем проекты с URL, которых еще нет в SheetMetadata
        projects_with_urls = session.query(ProjectMetadata).filter(
            ProjectMetadata.google_sheets_url.isnot(None),
            ProjectMetadata.google_sheets_url != ''
        ).all()
        
        print(f"📋 Найдено проектов с URL: {len(projects_with_urls)}")
        
        # Получаем существующие sheet_id из SheetMetadata
        existing_sheet_ids = set()
        existing_sheets = session.query(SheetMetadata).all()
        for sheet in existing_sheets:
            if sheet.sheet_id:
                existing_sheet_ids.add(sheet.sheet_id)
        
        print(f"🔍 Уже есть в SheetMetadata: {len(existing_sheet_ids)} записей")
        
        added_count = 0
        skipped_count = 0
        
        for project in projects_with_urls:
            sheet_id = extract_sheet_id(project.google_sheets_url)
            
            if not sheet_id:
                skipped_count += 1
                continue
                
            if sheet_id in existing_sheet_ids:
                skipped_count += 1
                continue
            
            # Создаем новую запись SheetMetadata
            sheet_title = generate_sheet_title(
                project.project_name or project.project_title, 
                project.created_at
            )
            
            new_sheet = SheetMetadata(
                sheet_id=sheet_id,
                sheet_title=sheet_title,
                sheet_url=project.google_sheets_url,  # Правильное поле в модели
                status='pending',  # Еще не парсен
                created_at=datetime.now()
            )
            
            session.add(new_sheet)
            existing_sheet_ids.add(sheet_id)  # Добавляем в локальный set
            added_count += 1
            
            if added_count % 100 == 0:
                print(f"   ➕ Добавлено {added_count} записей...")
        
        # Сохраняем изменения
        session.commit()
        
        print(f"\n✅ СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА:")
        print(f"   ➕ Добавлено новых: {added_count}")
        print(f"   ⏭  Пропущено (дубли): {skipped_count}")
        print(f"   📊 Всего в SheetMetadata: {len(existing_sheet_ids)}")
        
        return added_count > 0
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка синхронизации: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("🔄 СИНХРОНИЗАЦИЯ ПРОЕКТОВ С ТАБЛИЦАМИ")
    print("=" * 60)
    
    success = sync_projects_to_sheets()
    
    if success:
        print("\n🎉 Теперь можно скачивать и парсить новые таблицы!")
    else:
        print("\n⚠️  Новых таблиц для добавления не найдено.")

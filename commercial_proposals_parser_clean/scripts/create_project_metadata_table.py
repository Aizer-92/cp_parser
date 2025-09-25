#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания таблицы project_metadata
"""

import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager_v4 import DatabaseManager
from database.models_v4 import Base, ProjectMetadata
from sqlalchemy import create_engine

def create_project_metadata_table():
    """Создает таблицу project_metadata"""
    print("🔧 Создание таблицы project_metadata...")
    
    try:
        # Получаем движок базы данных
        engine = DatabaseManager.engine
        
        # Создаем только таблицу ProjectMetadata
        ProjectMetadata.__table__.create(engine, checkfirst=True)
        
        print("✅ Таблица project_metadata создана успешно!")
        
        # Проверяем создание
        session = DatabaseManager.get_session()
        try:
            count = session.query(ProjectMetadata).count()
            print(f"📊 Записей в таблице: {count}")
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ Ошибка создания таблицы: {e}")
        raise

if __name__ == "__main__":
    create_project_metadata_table()

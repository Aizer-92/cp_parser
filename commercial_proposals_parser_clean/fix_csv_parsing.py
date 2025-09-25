#!/usr/bin/env python3
"""
Исправление парсинга CSV файлов от AdvancedDownloader
"""

import os
import pandas as pd
from pathlib import Path
import shutil
from database.manager_v4 import DatabaseManager
from database.models_v4 import SheetMetadata
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_csv_files():
    """Исправляем CSV файлы - переименовываем их в .csv и создаем Excel версии"""
    
    print("🔧 ИСПРАВЛЕНИЕ CSV ФАЙЛОВ")
    print("=" * 60)
    
    storage_path = Path("storage/excel_files")
    csv_files_fixed = 0
    
    # Находим файлы которые на самом деле CSV
    for file_path in storage_path.glob("*.xlsx"):
        if file_path.stat().st_size == 0:
            continue
            
        # Пробуем определить если это CSV файл
        try:
            # Если файл имеет размер < 10KB и не открывается как Excel - вероятно CSV
            if file_path.stat().st_size < 10000:
                # Пробуем прочитать как CSV
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if ',' in first_line or ';' in first_line:
                        logger.info(f"📄 Найден CSV файл: {file_path.name}")
                        
                        # Читаем CSV
                        try:
                            # Пробуем разные разделители
                            for sep in [',', ';', '\t']:
                                try:
                                    df = pd.read_csv(file_path, sep=sep, encoding='utf-8')
                                    if len(df.columns) > 1:
                                        break
                                except:
                                    continue
                            else:
                                # Если не получилось ни с одним разделителем
                                df = pd.read_csv(file_path, sep=',', encoding='utf-8')
                            
                            if not df.empty:
                                # Создаем Excel версию
                                excel_path = file_path.with_suffix('.xlsx')
                                temp_excel_path = file_path.with_name(f"{file_path.stem}_fixed.xlsx")
                                
                                df.to_excel(temp_excel_path, index=False, engine='openpyxl')
                                
                                # Переименовываем старый файл в CSV
                                csv_path = file_path.with_suffix('.csv')
                                if csv_path.exists():
                                    csv_path.unlink()
                                    
                                shutil.move(str(file_path), str(csv_path))
                                
                                # Переименовываем новый Excel файл
                                shutil.move(str(temp_excel_path), str(file_path))
                                
                                logger.info(f"   ✅ Создан Excel файл: {df.shape[0]} строк, {df.shape[1]} колонок")
                                csv_files_fixed += 1
                                
                        except Exception as e:
                            logger.error(f"   ❌ Ошибка обработки CSV: {e}")
                            
        except Exception as e:
            # Если не CSV файл - пропускаем
            continue
    
    print(f"\n📊 РЕЗУЛЬТАТ:")
    print(f"   Исправлено CSV файлов: {csv_files_fixed}")
    
    return csv_files_fixed

def update_database_paths():
    """Обновляем пути в базе данных для исправленных файлов"""
    
    session = DatabaseManager.get_session()
    try:
        # Обновляем пути для файлов которые были исправлены
        sheets = session.query(SheetMetadata).filter(
            SheetMetadata.status == 'downloaded',
            SheetMetadata.local_file_path.isnot(None)
        ).all()
        
        updated = 0
        for sheet in sheets:
            file_path = Path(sheet.local_file_path)
            if file_path.exists() and file_path.stat().st_size > 0:
                # Проверяем что файл теперь можно открыть
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(file_path, read_only=True)
                    wb.close()
                    
                    # Если файл открывается - обновляем статус
                    if sheet.status != 'pending':
                        sheet.status = 'pending'
                        updated += 1
                        
                except Exception as e:
                    logger.warning(f"Файл {file_path.name} все еще не открывается: {e}")
        
        session.commit()
        print(f"   Обновлено записей в БД: {updated}")
        
    finally:
        session.close()

if __name__ == "__main__":
    fixed_count = fix_csv_files()
    if fixed_count > 0:
        update_database_paths()
        print(f"\n🚀 Готово! Теперь можно перепарсить исправленные файлы.")
        print(f"   Команда: python3 parse_existing_tables.py")



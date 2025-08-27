#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Простая загрузка Excel файла в Google Sheets
"""

import os
import sys
import logging
import pandas as pd
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Главная функция"""
    try:
        # Параметры
        excel_file = "output/unified_task_comparison_20250827_121620.xlsx"
        spreadsheet_id = "1qcWRIw1sGqrzfVGPBylKF0hubeczmIWQ9uVbmLQpYKs"
        
        # Проверяем существование файла
        if not os.path.exists(excel_file):
            logger.error(f"❌ Файл {excel_file} не найден")
            return False
        
        logger.info(f"📤 Подготовка к загрузке файла {excel_file} в Google Sheets...")
        
        # Читаем Excel файл
        excel_data = pd.read_excel(excel_file, sheet_name=None)
        logger.info(f"📊 Прочитано {len(excel_data)} листов из Excel файла")
        
        # Создаем инструкции для пользователя
        logger.info("=" * 80)
        logger.info("📋 ИНСТРУКЦИИ ДЛЯ ЗАГРУЗКИ В GOOGLE SHEETS:")
        logger.info("=" * 80)
        
        for sheet_name, df in excel_data.items():
            logger.info(f"")
            logger.info(f"📝 ЛИСТ: {sheet_name}")
            logger.info(f"📊 Размер: {df.shape[0]} строк, {df.shape[1]} колонок")
            logger.info(f"📋 Колонки: {', '.join(df.columns.tolist())}")
            
            # Создаем CSV файл для загрузки
            csv_filename = f"temp_{sheet_name.replace(' ', '_')}.csv"
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            logger.info(f"💾 CSV файл создан: {csv_filename}")
            
            logger.info(f"📤 ДЛЯ ЗАГРУЗКИ В GOOGLE SHEETS:")
            logger.info(f"1. Откройте: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
            logger.info(f"2. Создайте новый лист с названием: {sheet_name}")
            logger.info(f"3. Импортируйте файл {csv_filename}")
            logger.info(f"4. Или скопируйте данные из {csv_filename} и вставьте в лист")
        
        logger.info("")
        logger.info("🎯 АЛЬТЕРНАТИВНЫЙ СПОСОБ:")
        logger.info("1. Откройте Excel файл в браузере")
        logger.info("2. Скопируйте данные из каждого листа")
        logger.info("3. Вставьте в соответствующие листы Google Sheets")
        
        logger.info("")
        logger.info("📁 ФАЙЛЫ ДЛЯ ЗАГРУЗКИ:")
        for sheet_name in excel_data.keys():
            csv_filename = f"temp_{sheet_name.replace(' ', '_')}.csv"
            logger.info(f"- {csv_filename}")
        
        logger.info("=" * 80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

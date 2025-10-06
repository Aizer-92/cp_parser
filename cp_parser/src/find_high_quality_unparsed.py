#!/usr/bin/env python3
"""
Поиск файлов с высоким процентом качества структуры, которые не парсятся.
Эти файлы должны быть приоритетными для исправления парсера.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям проекта
sys.path.append(str(Path(__file__).parent.parent))

from src.structure_parser import CommercialProposalParser
from loguru import logger

class HighQualityUnparsedFinder:
    """Поиск файлов с высоким качеством, которые не парсятся"""
    
    def __init__(self):
        self.structure_parser = CommercialProposalParser()
        self.logger = logger
        
    def find_high_quality_unparsed_files(self, min_quality=70):
        """Находит файлы с высоким качеством структуры, которые не парсятся"""
        
        # Получаем анализ всех файлов
        analysis_results = self.structure_parser.analyze_test_files()
        
        # Берем только непрошедшие валидацию файлы
        failed_files = analysis_results.get('non_parseable_files', [])
        error_files = analysis_results.get('error_files', [])
        
        # Объединяем все проблемные файлы
        all_failed = failed_files + error_files
        
        # Фильтруем файлы с высоким качеством
        high_quality_files = []
        
        for file_result in all_failed:
            matches = file_result.get('structure_matches', 0)
            total = file_result.get('total_expected', 15)
            quality_percentage = round((matches / total) * 100, 1) if total > 0 else 0
            
            if quality_percentage >= min_quality:
                high_quality_files.append({
                    'file_name': file_result.get('file_name', 'Unknown'),
                    'quality': quality_percentage,
                    'matches': matches,
                    'total': total,
                    'error': file_result.get('error', 'No error info'),
                    'sheet_name': file_result.get('sheet_name', 'Unknown'),
                    'file_path': file_result.get('file_path', '')
                })
        
        # Сортируем по качеству (от высокого к низкому)
        high_quality_files.sort(key=lambda x: x['quality'], reverse=True)
        
        return high_quality_files
    
    def print_analysis_report(self, min_quality=70):
        """Выводит отчет по файлам с высоким качеством, которые не парсятся"""
        
        high_quality_files = self.find_high_quality_unparsed_files(min_quality)
        
        print(f"\n🎯 ФАЙЛЫ С ВЫСОКИМ КАЧЕСТВОМ СТРУКТУРЫ (≥{min_quality}%), КОТОРЫЕ НЕ ПАРСЯТСЯ")
        print(f"=" * 90)
        
        if not high_quality_files:
            print(f"✅ Все файлы с качеством ≥{min_quality}% успешно парсятся!")
            return []
        
        print(f"Найдено {len(high_quality_files)} файлов с высоким качеством, которые требуют внимания:")
        print()
        
        # Группируем по типу ошибки
        by_error_type = {}
        for file_info in high_quality_files:
            error = file_info['error']
            if 'не найдены листы' in error.lower():
                error_type = "Не найдены листы"
            elif 'низкий рейтинг' in error.lower():
                error_type = "Низкий рейтинг соответствия"
            elif 'file is not a zip file' in error.lower():
                error_type = "Поврежденный файл"
            else:
                error_type = "Другая ошибка"
            
            if error_type not in by_error_type:
                by_error_type[error_type] = []
            by_error_type[error_type].append(file_info)
        
        # Выводим по группам
        for error_type, files in by_error_type.items():
            print(f"🔍 {error_type.upper()} ({len(files)} файлов):")
            print(f"   {'№':>2} | {'Качество':>8} | {'Совпадения':>10} | {'Файл':50} | {'Лист'}")
            print(f"   {'-' * 2}-+-{'-' * 8}-+-{'-' * 10}-+-{'-' * 50}-+-{'-' * 20}")
            
            for i, file_info in enumerate(files, 1):
                file_name = file_info['file_name']
                if len(file_name) > 50:
                    file_name = file_name[:47] + "..."
                
                sheet_name = file_info['sheet_name']
                if len(sheet_name) > 20:
                    sheet_name = sheet_name[:17] + "..."
                
                quality = f"{file_info['quality']:5.1f}%"
                matches = f"{file_info['matches']:2d}/{file_info['total']:2d}"
                
                print(f"   {i:2d} | {quality:>8} | {matches:>10} | {file_name:50} | {sheet_name}")
            
            print()
        
        # Приоритетные рекомендации
        print(f"💡 ПРИОРИТЕТНЫЕ РЕКОМЕНДАЦИИ:")
        
        # Файлы с качеством >= 90%
        top_quality = [f for f in high_quality_files if f['quality'] >= 90]
        if top_quality:
            print(f"   🔥 КРИТИЧЕСКИ ВАЖНО: {len(top_quality)} файлов с качеством ≥90%")
            for file_info in top_quality[:3]:  # Показываем топ-3
                print(f"      • {file_info['file_name']} ({file_info['quality']}%)")
        
        # Файлы с качеством 80-89%
        high_quality = [f for f in high_quality_files if 80 <= f['quality'] < 90]
        if high_quality:
            print(f"   ⚡ ВЫСОКИЙ ПРИОРИТЕТ: {len(high_quality)} файлов с качеством 80-89%")
        
        # Файлы с качеством 70-79%
        medium_quality = [f for f in high_quality_files if 70 <= f['quality'] < 80]
        if medium_quality:
            print(f"   📋 СРЕДНИЙ ПРИОРИТЕТ: {len(medium_quality)} файлов с качеством 70-79%")
        
        print(f"\n🎯 СЛЕДУЮЩИЕ ШАГИ:")
        print(f"   1. Начните с файлов качеством ≥90% - они почти готовы к парсингу")
        print(f"   2. Проанализируйте конкретные файлы: python analyze_specific_file.py <имя_файла>")
        print(f"   3. Исправьте парсер для поддержки найденных паттернов")
        
        return high_quality_files

if __name__ == "__main__":
    finder = HighQualityUnparsedFinder()
    
    # Проверяем разные пороги качества
    print("🔍 Поиск файлов с высоким качеством структуры...")
    
    # Сначала ищем файлы с очень высоким качеством (≥80%)
    high_files = finder.print_analysis_report(min_quality=80)
    
    if not high_files:
        # Если нет файлов с качеством ≥80%, проверяем ≥70%
        print(f"\n" + "="*50)
        high_files = finder.print_analysis_report(min_quality=70)



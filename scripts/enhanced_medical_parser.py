#!/usr/bin/env python3
"""
Улучшенный парсер медицинских анализов из PDF
Поддерживает различные форматы PDF, включие проблемные кодировки
"""

import argparse
import re
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    import pdfplumber
    import PyPDF2
    import pandas as pd
except ImportError:
    print("❌ Необходимо установить зависимости:")
    print("py -m pip install PyPDF2 pdfplumber pandas openpyxl")
    sys.exit(1)

class EnhancedMedicalParser:
    def __init__(self):
        # Расширенный список медицинских показателей для поиска
        self.medical_indicators = {
            # Гематологические показатели
            'erythrocytes': ['эритроциты', 'rbc', 'red blood cells'],
            'hemoglobin': ['гемоглобин', 'hemoglobin', 'hgb', 'hb'],
            'hematocrit': ['гематокрит', 'hematocrit', 'hct'],
            'mcv': ['mcv', 'средний объем эритроцитов'],
            'mch': ['mch', 'среднее содержание гемоглобина'],
            'mchc': ['mchc', 'средняя концентрация'],
            'rdw': ['rdw', 'ширина распределения'],
            
            'platelets': ['тромбоциты', 'platelets', 'plt'],
            'mpv': ['mpv', 'средний объем тромбоцитов'],
            'pct': ['pct', 'тромбокрит'],
            'pdw': ['pdw', 'ширина распределения тромбоцитов'],
            
            'leukocytes': ['лейкоциты', 'leukocytes', 'wbc', 'white blood cells'],
            'neutrophils': ['нейтрофилы', 'neutrophils', 'neu'],
            'lymphocytes': ['лимфоциты', 'lymphocytes', 'lym'],
            'monocytes': ['моноциты', 'monocytes', 'mon'],
            'eosinophils': ['эозинофилы', 'eosinophils', 'eos'],
            'basophils': ['базофилы', 'basophils', 'bas'],
            
            # Биохимические показатели
            'glucose': ['глюкоза', 'glucose'],
            'cholesterol': ['холестерин', 'cholesterol'],
            'triglycerides': ['триглицериды', 'triglycerides'],
            'alt': ['алт', 'alt', 'sgpt'],
            'ast': ['аст', 'ast', 'sgot'],
            'bilirubin': ['билирубин', 'bilirubin'],
            'creatinine': ['креатинин', 'creatinine'],
            'urea': ['мочевина', 'urea'],
            
            # Гормоны
            'tsh': ['ттг', 'tsh'],
            't4': ['т4', 't4', 'тироксин'],
            't3': ['т3', 't3'],
            'testosterone': ['тестостерон', 'testosterone'],
            'cortisol': ['кортизол', 'cortisol'],
            
            # Витамины
            'vitamin_d': ['витамин d', 'vitamin d', '25(oh)d'],
            'b12': ['b12', 'витамин b12'],
            'folate': ['фолиевая кислота', 'folate'],
            
            # Иммунология
            'ige': ['ige', 'иммуноглобулин e'],
            'iga': ['iga', 'иммуноглобулин a'],
            'igg': ['igg', 'иммуноглобулин g'],
        }
        
        # Единицы измерения
        self.units = [
            'г/л', 'g/l', 'мг/дл', 'mg/dl', 'ммоль/л', 'mmol/l',
            '10*12/л', '10*9/л', '10^12/l', '10^9/l',
            '%', 'фл', 'fl', 'пг', 'pg', 'пг/кл', 'pg/cell',
            'мкмоль/л', 'nmol/l', 'пмоль/л', 'pmol/l',
            'нг/мл', 'ng/ml', 'мкг/л', 'ug/l', 'ме/л', 'iu/l'
        ]
    
    def extract_text_multiple_methods(self, pdf_path):
        """Извлечение текста различными методами"""
        texts = []
        
        # Метод 1: pdfplumber
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        texts.append(("pdfplumber", text))
        except Exception as e:
            print(f"⚠️ pdfplumber ошибка: {e}")
        
        # Метод 2: PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        texts.append(("PyPDF2", text))
        except Exception as e:
            print(f"⚠️ PyPDF2 ошибка: {e}")
        
        # Метод 3: pdfplumber с таблицами
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            table_text = "\n".join([" | ".join([str(cell) if cell else "" for cell in row]) for row in table])
                            texts.append(("pdfplumber_tables", table_text))
        except Exception as e:
            print(f"⚠️ pdfplumber таблицы ошибка: {e}")
        
        return texts
    
    def find_medical_values(self, text):
        """Поиск медицинских показателей в тексте"""
        results = {}
        text_lower = text.lower()
        
        # Поиск числовых значений с единицами
        number_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(?:' + '|'.join(re.escape(unit) for unit in self.units) + ')',
            r'(\d+(?:[.,]\d+)?)\s*(?:×10[¹²⁹]?/?л|x10\^[129]/l)',
        ]
        
        found_numbers = []
        for pattern in number_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                found_numbers.append((match.group(), match.start(), match.end()))
        
        print(f"🔢 Найдено числовых значений: {len(found_numbers)}")
        
        # Поиск по ключевым словам
        for param_key, keywords in self.medical_indicators.items():
            for keyword in keywords:
                pattern = rf'{re.escape(keyword)}\s*:?\s*(\d+(?:[.,]\d+)?)'
                matches = re.finditer(pattern, text_lower)
                
                for match in matches:
                    value_str = match.group(1).replace(',', '.')
                    try:
                        value = float(value_str)
                        if param_key not in results:
                            results[param_key] = []
                        results[param_key].append({
                            'value': value,
                            'context': text[max(0, match.start()-50):match.end()+50],
                            'keyword': keyword
                        })
                    except ValueError:
                        continue
        
        return results, found_numbers
    
    def manual_extraction_help(self, pdf_path):
        """Помощь для ручного извлечения данных"""
        print(f"\n📋 ПОМОЩЬ ДЛЯ РУЧНОГО ИЗВЛЕЧЕНИЯ: {pdf_path}")
        print("=" * 80)
        
        texts = self.extract_text_multiple_methods(pdf_path)
        
        if not texts:
            print("❌ Не удалось извлечь текст из PDF")
            return
        
        print(f"✅ Извлечено {len(texts)} вариантов текста")
        
        for i, (method, text) in enumerate(texts):
            print(f"\n📄 МЕТОД {i+1}: {method}")
            print("-" * 40)
            
            # Показываем первые 500 символов
            preview = text[:500] if len(text) > 500 else text
            print(f"Превью: {preview}")
            
            if len(text) > 500:
                print(f"... (всего {len(text)} символов)")
            
            # Ищем возможные показатели
            results, numbers = self.find_medical_values(text)
            
            if results:
                print(f"\n🎯 Найденные показатели:")
                for param, values in results.items():
                    for value_info in values:
                        print(f"  {param}: {value_info['value']} (ключевое слово: {value_info['keyword']})")
            
            if numbers:
                print(f"\n🔢 Найденные числа с единицами ({len(numbers)} шт.):")
                for num_text, start, end in numbers[:10]:  # Показываем первые 10
                    print(f"  {num_text}")
                if len(numbers) > 10:
                    print(f"  ... и еще {len(numbers) - 10}")
            
            print("\n" + "="*40)
        
        # Рекомендации
        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("1. Если текст нечитаемый (много (cid:XX)) - PDF имеет проблемы с кодировкой")
        print("2. Если есть таблицы - попробуйте скопировать данные из PDF вручную")
        print("3. Если числа найдены - можно создать шаблон для парсинга")
        print("4. Для лучшего результата - переконвертируйте PDF в более простой формат")
    
    def suggest_manual_template(self):
        """Предложение шаблона для ручного ввода"""
        print("\n📝 ШАБЛОН ДЛЯ РУЧНОГО ВВОДА ДАННЫХ:")
        print("=" * 50)
        
        template = {
            "date": "YYYY-MM-DD",
            "order_number": "",
            "laboratory": "",
            "values": {
                # Гематология
                "erythrocytes": {"value": 0.0, "unit": "10*12/л"},
                "hemoglobin": {"value": 0, "unit": "г/л"},
                "hematocrit": {"value": 0.0, "unit": "%"},
                "platelets": {"value": 0, "unit": "10*9/л"},
                "leukocytes": {"value": 0.0, "unit": "10*9/л"},
                
                # Биохимия (если есть)
                "glucose": {"value": 0.0, "unit": "ммоль/л"},
                "cholesterol": {"value": 0.0, "unit": "ммоль/л"},
                "creatinine": {"value": 0, "unit": "мкмоль/л"},
                
                # Добавьте другие показатели по необходимости
            }
        }
        
        template_file = Path("Docs/Health/manual_input_template.json")
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"Шаблон сохранен: {template_file}")
        print("\nОткройте файл и заполните значения вручную")

def main():
    parser = argparse.ArgumentParser(description='Улучшенный парсер медицинских анализов')
    parser.add_argument('pdf_file', help='Путь к PDF файлу с анализом')
    parser.add_argument('--help-extract', action='store_true', help='Помощь для ручного извлечения')
    parser.add_argument('--template', action='store_true', help='Создать шаблон для ручного ввода')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_file)
    if not pdf_path.exists():
        print(f"❌ Файл не найден: {pdf_path}")
        return
    
    medical_parser = EnhancedMedicalParser()
    
    if args.template:
        medical_parser.suggest_manual_template()
        return
    
    if args.help_extract:
        medical_parser.manual_extraction_help(pdf_path)
        return
    
    # Обычный парсинг
    print(f"🔍 Анализирую PDF: {pdf_path}")
    texts = medical_parser.extract_text_multiple_methods(pdf_path)
    
    all_results = {}
    for method, text in texts:
        results, numbers = medical_parser.find_medical_values(text)
        if results:
            print(f"✅ {method}: найдено {len(results)} показателей")
            all_results.update(results)
    
    if all_results:
        print("\n🎯 ИТОГОВЫЕ РЕЗУЛЬТАТЫ:")
        for param, values in all_results.items():
            for value_info in values:
                print(f"{param}: {value_info['value']}")
    else:
        print("\n⚠️ Автоматический парсинг не дал результатов")
        print("Используйте --help-extract для диагностики")

if __name__ == "__main__":
    main()

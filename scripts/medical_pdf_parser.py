#!/usr/bin/env python3
"""
Парсер медицинских анализов из PDF файлов

Использование:
    python scripts/medical_pdf_parser.py "path/to/analysis.pdf"
    python scripts/medical_pdf_parser.py --batch "path/to/folder/"
    python scripts/medical_pdf_parser.py --analyze "path/to/analysis.pdf"  # для анализа структуры

Требования:
    pip install PyPDF2 pdfplumber pandas openpyxl
"""

import argparse
import re
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

try:
    import pdfplumber
    import PyPDF2
except ImportError:
    print("❌ Необходимо установить зависимости:")
    print("pip install PyPDF2 pdfplumber pandas openpyxl")
    sys.exit(1)

# Регулярные выражения для поиска медицинских показателей
MEDICAL_PATTERNS = {
    # Общий анализ крови
    'hemoglobin': [
        r'(?:гемоглобин|hemoglobin|hgb|hb)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:г/л|g/l)?',
        r'(?:гемоглобин|hemoglobin|hgb|hb)\s+(\d+(?:[.,]\d+)?)'
    ],
    'erythrocytes': [
        r'(?:эритроциты|erythrocytes|rbc)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:×10¹²/л|10\^12/l)?',
        r'(?:эритроциты|erythrocytes|rbc)\s+(\d+(?:[.,]\d+)?)'
    ],
    'leukocytes': [
        r'(?:лейкоциты|leukocytes|wbc)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:×10⁹/л|10\^9/l)?',
        r'(?:лейкоциты|leukocytes|wbc)\s+(\d+(?:[.,]\d+)?)'
    ],
    'platelets': [
        r'(?:тромбоциты|platelets|plt)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:×10⁹/л|10\^9/l)?',
        r'(?:тромбоциты|platelets|plt)\s+(\d+(?:[.,]\d+)?)'
    ],
    
    # Биохимический анализ
    'glucose': [
        r'(?:глюкоза|glucose|glu)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ммоль/л|mmol/l|мг/дл|mg/dl)?',
        r'(?:глюкоза|glucose|glu)\s+(\d+(?:[.,]\d+)?)'
    ],
    'cholesterol_total': [
        r'(?:холестерин общий|total cholesterol|chol)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ммоль/л|mmol/l|мг/дл|mg/dl)?',
        r'(?:холестерин|cholesterol)\s+(?:общий|total)?\s*(\d+(?:[.,]\d+)?)'
    ],
    'cholesterol_hdl': [
        r'(?:холестерин лпвп|hdl cholesterol|hdl)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ммоль/л|mmol/l|мг/дл|mg/dl)?',
        r'(?:лпвп|hdl)\s+(\d+(?:[.,]\d+)?)'
    ],
    'cholesterol_ldl': [
        r'(?:холестерин лпнп|ldl cholesterol|ldl)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ммоль/л|mmol/l|мг/дл|mg/dl)?',
        r'(?:лпнп|ldl)\s+(\d+(?:[.,]\d+)?)'
    ],
    'triglycerides': [
        r'(?:триглицериды|triglycerides|tg)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ммоль/л|mmol/l|мг/дл|mg/dl)?',
        r'(?:триглицериды|triglycerides|tg)\s+(\d+(?:[.,]\d+)?)'
    ],
    'creatinine': [
        r'(?:креатинин|creatinine|crea)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:мкмоль/л|μmol/l|мг/дл|mg/dl)?',
        r'(?:креатинин|creatinine|crea)\s+(\d+(?:[.,]\d+)?)'
    ],
    'urea': [
        r'(?:мочевина|urea)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ммоль/л|mmol/l|мг/дл|mg/dl)?',
        r'(?:мочевина|urea)\s+(\d+(?:[.,]\d+)?)'
    ],
    'alt': [
        r'(?:алт|alt|alanine aminotransferase)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ед/л|u/l|iu/l)?',
        r'(?:алт|alt)\s+(\d+(?:[.,]\d+)?)'
    ],
    'ast': [
        r'(?:аст|ast|aspartate aminotransferase)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:ед/л|u/l|iu/l)?',
        r'(?:аст|ast)\s+(\d+(?:[.,]\d+)?)'
    ],
    
    # Гормональные показатели
    'testosterone': [
        r'(?:тестостерон|testosterone|test)\s*(?:общий|total)?\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:нмоль/л|nmol/l|нг/мл|ng/ml)?',
        r'(?:тестостерон|testosterone)\s+(?:общий|total)?\s*(\d+(?:[.,]\d+)?)'
    ],
    'testosterone_free': [
        r'(?:тестостерон свободный|free testosterone|тестостерон\s+свободный)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:пмоль/л|pmol/l|пг/мл|pg/ml)?',
        r'(?:свободный тестостерон|free\s+testosterone)\s*:?\s*(\d+(?:[.,]\d+)?)'
    ],
    'shbg': [
        r'(?:гспг|shbg|sex hormone binding globulin|глобулин связывающий половые гормоны)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:нмоль/л|nmol/l)?',
        r'(?:гспг|shbg)\s+(\d+(?:[.,]\d+)?)'
    ],
    'estradiol': [
        r'(?:эстрадиол|estradiol|e2)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:пмоль/л|pmol/l|пг/мл|pg/ml)?',
        r'(?:эстрадиол|estradiol|e2)\s+(\d+(?:[.,]\d+)?)'
    ],
    'fsh': [
        r'(?:фсг|fsh|follicle stimulating hormone|фолликулостимулирующий гормон)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:мед/л|iu/l|мме/мл|miu/ml)?',
        r'(?:фсг|fsh)\s+(\d+(?:[.,]\d+)?)'
    ],
    'lh': [
        r'(?:лг|lh|luteinizing hormone|лютеинизирующий гормон)\s*:?\s*(\d+(?:[.,]\d+)?)\s*(?:мед/л|iu/l|мме/мл|miu/ml)?',
        r'(?:лг|lh)\s+(\d+(?:[.,]\d+)?)'
    ],
}

# Нормы для медицинских показателей (базовые)
NORMAL_RANGES = {
    'hemoglobin': {'min': 120, 'max': 160, 'unit': 'г/л'},
    'glucose': {'min': 3.3, 'max': 5.5, 'unit': 'ммоль/л'},
    'cholesterol_total': {'min': 3.0, 'max': 5.2, 'unit': 'ммоль/л'},
    'cholesterol_hdl': {'min': 1.0, 'max': 2.2, 'unit': 'ммоль/л'},
    'cholesterol_ldl': {'min': 1.4, 'max': 3.3, 'unit': 'ммоль/л'},
    'triglycerides': {'min': 0.45, 'max': 1.7, 'unit': 'ммоль/л'},
    'creatinine': {'min': 62, 'max': 115, 'unit': 'мкмоль/л'},
    'alt': {'min': 7, 'max': 56, 'unit': 'Ед/л'},
    'ast': {'min': 10, 'max': 40, 'unit': 'Ед/л'},
    
    # Гормональные показатели (мужские нормы)
    'testosterone': {'min': 8.64, 'max': 29.0, 'unit': 'нмоль/л'},  # общий тестостерон
    'testosterone_free': {'min': 250, 'max': 836, 'unit': 'пмоль/л'},  # свободный тестостерон
    'shbg': {'min': 13, 'max': 71, 'unit': 'нмоль/л'},  # ГСПГ
    'estradiol': {'min': 40, 'max': 162, 'unit': 'пмоль/л'},  # эстрадиол у мужчин
    'fsh': {'min': 1.5, 'max': 12.4, 'unit': 'мЕд/л'},  # ФСГ
    'lh': {'min': 1.7, 'max': 8.6, 'unit': 'мЕд/л'},  # ЛГ
}

def extract_text_from_pdf(pdf_path):
    """Извлекает текст из PDF файла"""
    text = ""
    
    try:
        # Используем pdfplumber для лучшего извлечения текста
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"⚠️  Ошибка при извлечении текста с pdfplumber: {e}")
        
        # Fallback на PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e2:
            print(f"❌ Ошибка при извлечении текста с PyPDF2: {e2}")
            return None
    
    return text

def extract_date_from_filename(filename):
    """Извлекает дату из имени файла"""
    # Ищем timestamp в имени файла
    timestamp_match = re.search(r'дата-(\d+)', filename)
    if timestamp_match:
        timestamp = int(timestamp_match.group(1))
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    
    # Ищем дату в формате YYYY-MM-DD или DD.MM.YYYY
    date_patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{2}\.\d{2}\.\d{4})',
        r'(\d{2}/\d{2}/\d{4})'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            # Конвертируем в стандартный формат
            if '.' in date_str:
                day, month, year = date_str.split('.')
                return f"{year}-{month}-{day}"
            elif '/' in date_str:
                day, month, year = date_str.split('/')
                return f"{year}-{month}-{day}"
            else:
                return date_str
    
    return datetime.now().strftime('%Y-%m-%d')

def extract_order_number(filename):
    """Извлекает номер заказа из имени файла"""
    match = re.search(r'заказНомер-(\d+)', filename)
    return match.group(1) if match else "Unknown"

def parse_medical_values(text):
    """Парсит медицинские показатели из текста"""
    results = {}
    text_lower = text.lower()
    
    for parameter, patterns in MEDICAL_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                value_str = match.group(1).replace(',', '.')
                try:
                    value = float(value_str)
                    results[parameter] = {
                        'value': value,
                        'original_text': match.group(0),
                        'unit': NORMAL_RANGES.get(parameter, {}).get('unit', ''),
                        'normal_range': NORMAL_RANGES.get(parameter),
                        'in_range': check_normal_range(parameter, value)
                    }
                    break  # Берем первое найденное значение
                except ValueError:
                    continue
    
    return results

def check_normal_range(parameter, value):
    """Проверяет, находится ли значение в норме"""
    if parameter not in NORMAL_RANGES:
        return None
    
    range_info = NORMAL_RANGES[parameter]
    return range_info['min'] <= value <= range_info['max']

def analyze_pdf_structure(pdf_path):
    """Анализирует структуру PDF для понимания формата"""
    print(f"🔍 Анализирую структуру PDF: {pdf_path}")
    
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return
    
    print("\n📄 Извлеченный текст (первые 1000 символов):")
    print("-" * 50)
    print(text[:1000])
    print("-" * 50)
    
    # Поиск всех чисел с возможными единицами измерения
    number_patterns = re.findall(r'\d+(?:[.,]\d+)?\s*(?:г/л|ммоль/л|мкмоль/л|ед/л|×10⁹/л|×10¹²/л)', text.lower())
    
    print(f"\n🔢 Найденные числовые значения с единицами:")
    for i, pattern in enumerate(number_patterns[:20]):  # Показываем первые 20
        print(f"{i+1}. {pattern}")
    
    # Анализируем найденные медицинские показатели
    parsed_values = parse_medical_values(text)
    
    print(f"\n🩺 Распознанные медицинские показатели:")
    for param, data in parsed_values.items():
        status = "✅ в норме" if data['in_range'] else "❌ вне нормы" if data['in_range'] is not None else "❓ норма неизвестна"
        print(f"{param}: {data['value']} {data['unit']} - {status}")

def create_medical_record(pdf_path, output_dir=None):
    """Создает медицинскую запись из PDF"""
    if output_dir is None:
        output_dir = Path("Docs/Health/lab_results")
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Извлекаем информацию из имени файла
    filename = Path(pdf_path).name
    date_str = extract_date_from_filename(filename)
    order_number = extract_order_number(filename)
    
    # Парсим PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"❌ Не удалось извлечь текст из {pdf_path}")
        return None
    
    parsed_values = parse_medical_values(text)
    
    if not parsed_values:
        print(f"⚠️  Не найдено медицинских показателей в {pdf_path}")
        return None
    
    # Создаем структурированную запись
    record = {
        'date': date_str,
        'order_number': order_number,
        'source_file': str(pdf_path),
        'values': parsed_values,
        'summary': {
            'total_parameters': len(parsed_values),
            'normal_count': sum(1 for v in parsed_values.values() if v['in_range'] is True),
            'abnormal_count': sum(1 for v in parsed_values.values() if v['in_range'] is False),
        }
    }
    
    # Сохраняем JSON
    json_filename = f"analysis_{date_str}_{order_number}.json"
    json_path = output_dir / json_filename
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    
    # Создаем markdown файл
    md_filename = f"analysis_{date_str}_{order_number}.md"
    md_path = output_dir / md_filename
    
    create_markdown_report(record, md_path)
    
    # Создаем Excel файл для удобного просмотра
    excel_filename = f"analysis_{date_str}_{order_number}.xlsx"
    excel_path = output_dir / excel_filename
    
    create_excel_report(record, excel_path)
    
    print(f"✅ Создана медицинская запись:")
    print(f"   📄 JSON: {json_path}")
    print(f"   📝 Markdown: {md_path}")
    print(f"   📊 Excel: {excel_path}")
    
    return record

def create_markdown_report(record, output_path):
    """Создает markdown отчет"""
    date_str = record['date']
    order_number = record['order_number']
    values = record['values']
    
    md_content = f"""# Анализ крови от {date_str}

**Номер заказа:** {order_number}  
**Дата:** {date_str}  
**Источник:** {record['source_file']}

## 📊 Общая статистика
- **Всего показателей:** {record['summary']['total_parameters']}
- **В норме:** {record['summary']['normal_count']} ✅
- **Вне нормы:** {record['summary']['abnormal_count']} ❌

## 🧪 Результаты анализов

| Показатель | Значение | Единица | Норма | Статус |
|------------|----------|---------|-------|--------|
"""
    
    for param, data in values.items():
        param_name = param.replace('_', ' ').title()
        value = data['value']
        unit = data['unit']
        
        if data['normal_range']:
            norm_range = f"{data['normal_range']['min']}-{data['normal_range']['max']}"
        else:
            norm_range = "—"
        
        if data['in_range'] is True:
            status = "✅ Норма"
        elif data['in_range'] is False:
            status = "❌ Вне нормы"
        else:
            status = "❓ Неизвестно"
        
        md_content += f"| {param_name} | {value} | {unit} | {norm_range} | {status} |\n"
    
    md_content += f"""

## 🔍 Проверка норм через скрипт

```bash
# Проверить показатели через наш скрипт проверки диапазонов:
"""
    
    for param, data in values.items():
        if data['normal_range']:
            min_val = data['normal_range']['min']
            max_val = data['normal_range']['max']
            value = data['value']
            md_content += f"python scripts/check_range.py {value} {min_val} {max_val}  # {param}\n"
    
    md_content += """```

## 📝 Заметки врача
[Добавьте заметки врача или свои наблюдения]

## 📈 Динамика
[Сравните с предыдущими анализами]

## 🎯 Рекомендации
- [ ] [Рекомендация 1]
- [ ] [Рекомендация 2]
- [ ] [Рекомендация 3]

---
*Файл создан автоматически из PDF анализа*
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

def create_excel_report(record, output_path):
    """Создает Excel отчет"""
    data_for_excel = []
    
    for param, data in record['values'].items():
        data_for_excel.append({
            'Показатель': param.replace('_', ' ').title(),
            'Значение': data['value'],
            'Единица': data['unit'],
            'Мин. норма': data['normal_range']['min'] if data['normal_range'] else '',
            'Макс. норма': data['normal_range']['max'] if data['normal_range'] else '',
            'В норме': 'Да' if data['in_range'] else 'Нет' if data['in_range'] is not None else 'Неизвестно',
            'Дата': record['date'],
            'Номер заказа': record['order_number']
        })
    
    df = pd.DataFrame(data_for_excel)
    df.to_excel(output_path, index=False)

def main():
    parser = argparse.ArgumentParser(description='Парсер медицинских анализов из PDF')
    parser.add_argument('pdf_path', nargs='?', help='Путь к PDF файлу с анализом')
    parser.add_argument('--analyze', help='Проанализировать структуру PDF')
    parser.add_argument('--batch', help='Обработать все PDF в папке')
    parser.add_argument('--output', help='Папка для сохранения результатов', default='Docs/Health/lab_results')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_pdf_structure(args.analyze)
    elif args.batch:
        batch_dir = Path(args.batch)
        pdf_files = list(batch_dir.glob('*.pdf'))
        
        if not pdf_files:
            print(f"❌ PDF файлы не найдены в {batch_dir}")
            return
        
        print(f"📁 Найдено {len(pdf_files)} PDF файлов")
        
        for pdf_file in pdf_files:
            print(f"\n🔄 Обрабатываю {pdf_file.name}")
            try:
                create_medical_record(pdf_file, args.output)
            except Exception as e:
                print(f"❌ Ошибка при обработке {pdf_file}: {e}")
    
    elif args.pdf_path:
        pdf_path = Path(args.pdf_path)
        if not pdf_path.exists():
            print(f"❌ Файл не найден: {pdf_path}")
            return
        
        create_medical_record(pdf_path, args.output)
    
    else:
        print("❌ Укажите путь к PDF файлу или используйте --analyze для анализа структуры")
        print("Примеры:")
        print("  python scripts/medical_pdf_parser.py 'path/to/analysis.pdf'")
        print("  python scripts/medical_pdf_parser.py --analyze 'path/to/analysis.pdf'")
        print("  python scripts/medical_pdf_parser.py --batch 'path/to/folder/'")

if __name__ == "__main__":
    main()

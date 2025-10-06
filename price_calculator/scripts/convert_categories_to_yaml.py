#!/usr/bin/env python3
"""
Конвертер categories_data.py в YAML конфигурацию
Часть ФАЗЫ 1 рефакторинга: убираем гигантский Python файл с данными
"""

import sys
import os
import yaml
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from categories_data import CATEGORIES_DATA
    print(f"Загружено {len(CATEGORIES_DATA)} категорий из categories_data.py")
except ImportError as e:
    print(f"❌ Ошибка импорта categories_data: {e}")
    sys.exit(1)

def convert_to_yaml():
    """Конвертирует CATEGORIES_DATA в YAML файл"""
    
    # Подготавливаем данные для YAML
    yaml_data = {
        "metadata": {
            "version": "1.0",
            "description": "Конфигурация категорий товаров для Price Calculator",
            "total_categories": len(CATEGORIES_DATA),
            "created_from": "categories_data.py",
            "fields_description": {
                "category": "Название категории товара",
                "material": "Материалы изготовления",
                "tnved_code": "Код ТН ВЭД для таможни",
                "density": "Плотность товара (кг/м³)",
                "rates": "Логистические ставки (USD/кг)",
                "price_ranges": "Диапазон цен в юанях и рублях",
                "quantity_ranges": "Рекомендуемый тираж",
                "weight_ranges": "Диапазон весов",
                "median_price_yuan": "Медианная цена в юанях",
                "median_price_rub": "Медианная цена в рублях",
                "avg_quantity": "Среднее количество для заказа"
            }
        },
        "categories": CATEGORIES_DATA
    }
    
    # Создаем config директорию если не существует
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    
    # Записываем в YAML файл
    yaml_file = config_dir / "categories.yaml"
    
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, 
                 default_flow_style=False,
                 allow_unicode=True,
                 sort_keys=False,
                 indent=2,
                 width=120)
    
    print(f"Категории сконвертированы в {yaml_file}")
    print(f"Размер файла: {yaml_file.stat().st_size / 1024:.1f} KB")
    
    # Создаем также компактную версию только с основными категориями
    unique_categories = {}
    for cat in CATEGORIES_DATA:
        category_name = cat['category']
        if category_name not in unique_categories:
            unique_categories[category_name] = cat
    
    compact_data = {
        "metadata": {
            "version": "1.0",
            "description": "Компактная конфигурация - только уникальные категории",
            "total_categories": len(unique_categories),
        },
        "categories": list(unique_categories.values())
    }
    
    compact_file = config_dir / "categories_compact.yaml"
    with open(compact_file, 'w', encoding='utf-8') as f:
        yaml.dump(compact_data, f,
                 default_flow_style=False,
                 allow_unicode=True,
                 sort_keys=False,
                 indent=2,
                 width=120)
    
    print(f"Компактная версия создана: {compact_file}")
    print(f"Размер компактного файла: {compact_file.stat().st_size / 1024:.1f} KB")

def validate_yaml():
    """Проверяет корректность созданного YAML"""
    config_dir = Path(__file__).parent.parent / "config"
    yaml_file = config_dir / "categories.yaml"
    
    if not yaml_file.exists():
        print("❌ YAML файл не найден")
        return False
    
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            loaded_data = yaml.safe_load(f)
        
        original_count = len(CATEGORIES_DATA)
        yaml_count = len(loaded_data['categories'])
        
        if original_count == yaml_count:
            print(f"Валидация успешна: {yaml_count} категорий")
            return True
        else:
            print(f"Ошибка валидации: {original_count} → {yaml_count}")
            return False
            
    except Exception as e:
        print(f"Ошибка валидации: {e}")
        return False

if __name__ == "__main__":
    print("Конвертация categories_data.py в YAML...")
    print("==================================================")
    
    convert_to_yaml()
    
    print("\nВалидация результата...")
    if validate_yaml():
        print("Конвертация завершена успешно!")
        print("\nСледующие шаги:")
        print("1. Обновить price_calculator.py для загрузки из YAML")
        print("2. Протестировать работу приложения") 
        print("3. Удалить categories_data.py после подтверждения")
    else:
        print("\n❌ Ошибка конвертации")
        sys.exit(1)


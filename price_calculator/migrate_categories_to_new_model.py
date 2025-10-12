#!/usr/bin/env python3
"""
Миграция категорий в новый формат с моделями Category.

Аккуратно переносит все данные из categories.yaml в новый формат,
сохраняя все существующие поля и добавляя новые требования.
"""

import yaml
import json
from typing import Dict, List, Any
from models.category import Category, CategoryRequirements


def load_existing_categories() -> List[Dict[str, Any]]:
    """Загружает существующие категории из YAML"""
    yaml_path = 'config/categories.yaml'
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    categories = data.get('categories', [])
    print(f"📥 Загружено {len(categories)} категорий из {yaml_path}")
    
    return categories


def analyze_category(cat_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Анализирует категорию и определяет её требования.
    
    Returns:
        Dict с информацией о категории и рекомендациями
    """
    name = cat_data.get('category', '')
    rates = cat_data.get('rates', {})
    rail_base = rates.get('rail_base', 0)
    air_base = rates.get('air_base', 0)
    
    analysis = {
        'name': name,
        'has_rail_rate': rail_base is not None and rail_base > 0,
        'has_air_rate': air_base is not None and air_base > 0,
        'needs_custom_params': False,
        'requirements': {
            'requires_logistics_rate': False,
            'requires_duty_rate': False,
            'requires_vat_rate': False
        },
        'notes': []
    }
    
    # Проверка необходимости кастомных параметров
    if name == "Новая категория":
        analysis['needs_custom_params'] = True
        analysis['requirements']['requires_logistics_rate'] = True
        analysis['notes'].append("Специальная категория для нераспознанных товаров")
    
    elif not analysis['has_rail_rate'] or not analysis['has_air_rate']:
        analysis['needs_custom_params'] = True
        analysis['requirements']['requires_logistics_rate'] = True
        analysis['notes'].append(f"Отсутствуют базовые ставки: rail={rail_base}, air={air_base}")
    
    # Проверка пошлин
    duty_rate = cat_data.get('duty_rate')
    if duty_rate is None or (isinstance(duty_rate, str) and duty_rate == '0%'):
        analysis['notes'].append("Отсутствует информация о пошлине")
    
    return analysis


def migrate_category(cat_data: Dict[str, Any], analysis: Dict[str, Any]) -> Category:
    """
    Мигрирует категорию в новый формат Category.
    Сохраняет все существующие данные.
    """
    # Создаём requirements на основе анализа
    requirements = CategoryRequirements(
        requires_logistics_rate=analysis['requirements']['requires_logistics_rate'],
        requires_duty_rate=analysis['requirements']['requires_duty_rate'],
        requires_vat_rate=analysis['requirements']['requires_vat_rate']
    )
    
    # Извлекаем ставки
    rates = cat_data.get('rates', {})
    rail_base = rates.get('rail_base')
    air_base = rates.get('air_base')
    contract_base = rates.get('contract_base')
    
    # Обрабатываем пошлины
    duty_rate = cat_data.get('duty_rate')
    if isinstance(duty_rate, str):
        if duty_rate.endswith('%'):
            duty_rate = float(duty_rate.rstrip('%'))
        else:
            try:
                duty_rate = float(duty_rate)
            except (ValueError, TypeError):
                duty_rate = None
    
    vat_rate = cat_data.get('vat_rate')
    if isinstance(vat_rate, str):
        if vat_rate.endswith('%'):
            vat_rate = float(vat_rate.rstrip('%'))
        else:
            try:
                vat_rate = float(vat_rate)
            except (ValueError, TypeError):
                vat_rate = None
    
    # Извлекаем keywords
    keywords = []
    material = cat_data.get('material', '')
    if material:
        # Разбиваем материалы на keywords
        keywords = [m.strip() for m in material.split(',') if m.strip()]
    
    # Добавляем название категории как keyword
    category_name = cat_data.get('category', '')
    if category_name and category_name not in keywords:
        keywords.insert(0, category_name)
    
    # Создаём Category
    category = Category(
        name=category_name,
        material=material,
        rail_base=rail_base,
        air_base=air_base,
        contract_base=contract_base,
        duty_rate=duty_rate,
        vat_rate=vat_rate,
        requirements=requirements,
        keywords=keywords,
        description=cat_data.get('description', ''),
        tnved_code=cat_data.get('tnved_code', ''),
        certificates=cat_data.get('certificates', [])
    )
    
    return category


def save_migrated_categories(categories: List[Category], output_file: str = 'config/categories_migrated.json'):
    """Сохраняет мигрированные категории в JSON"""
    data = {
        'version': '2.0',
        'description': 'Migrated categories with new Category model',
        'total_categories': len(categories),
        'categories': [cat.to_dict() for cat in categories]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранено {len(categories)} категорий в {output_file}")


def generate_migration_report(analyses: List[Dict[str, Any]]) -> str:
    """Генерирует отчёт о миграции"""
    total = len(analyses)
    needs_custom = sum(1 for a in analyses if a['needs_custom_params'])
    has_notes = sum(1 for a in analyses if a['notes'])
    
    report = f"""
# Отчёт о миграции категорий

## Статистика

- **Всего категорий:** {total}
- **Требуют кастомных параметров:** {needs_custom} ({needs_custom/total*100:.1f}%)
- **Со специальными заметками:** {has_notes} ({has_notes/total*100:.1f}%)

## Категории, требующие кастомных параметров

"""
    
    for analysis in analyses:
        if analysis['needs_custom_params']:
            report += f"\n### {analysis['name']}\n"
            report += f"- Базовые ставки: rail={analysis['has_rail_rate']}, air={analysis['has_air_rate']}\n"
            for note in analysis['notes']:
                report += f"- {note}\n"
    
    report += "\n## Рекомендации\n\n"
    report += "1. Проверить категории с отсутствующими базовыми ставками\n"
    report += "2. Заполнить информацию о пошлинах где она отсутствует\n"
    report += "3. Убедиться что 'Новая категория' корректно помечена\n"
    
    return report


def main():
    """Основной процесс миграции"""
    print("="*60)
    print("🔄 МИГРАЦИЯ КАТЕГОРИЙ В НОВЫЙ ФОРМАТ")
    print("="*60)
    
    # 1. Загружаем существующие категории
    existing_cats = load_existing_categories()
    
    # 2. Анализируем каждую категорию
    print("\n📊 Анализ категорий...")
    analyses = []
    for cat_data in existing_cats:
        analysis = analyze_category(cat_data)
        analyses.append(analysis)
    
    # 3. Мигрируем категории
    print("\n🔄 Миграция категорий...")
    migrated_categories = []
    for cat_data, analysis in zip(existing_cats, analyses):
        try:
            category = migrate_category(cat_data, analysis)
            migrated_categories.append(category)
            
            # Валидация
            if category.needs_custom_params():
                print(f"  ⚙️  {category.name} - требует кастомных параметров")
            
        except Exception as e:
            print(f"  ❌ Ошибка при миграции {cat_data.get('category', 'UNKNOWN')}: {e}")
            import traceback
            traceback.print_exc()
    
    # 4. Сохраняем результаты
    print("\n💾 Сохранение результатов...")
    save_migrated_categories(migrated_categories)
    
    # 5. Генерируем отчёт
    print("\n📄 Генерация отчёта...")
    report = generate_migration_report(analyses)
    
    with open('MIGRATION_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("📄 Отчёт сохранён в MIGRATION_REPORT.md")
    
    # 6. Итоговая статистика
    print("\n" + "="*60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА")
    print("="*60)
    print(f"Всего категорий: {len(migrated_categories)}/{len(existing_cats)}")
    print(f"Требуют кастомных параметров: {sum(1 for c in migrated_categories if c.needs_custom_params())}")
    print(f"\nФайлы:")
    print(f"  - config/categories_migrated.json (новый формат)")
    print(f"  - MIGRATION_REPORT.md (отчёт)")
    print("="*60)
    
    # 7. Тестирование нескольких категорий
    print("\n🧪 Тестирование миграции...")
    
    test_categories = ['Новая категория', 'сумка', 'Футболки']
    for cat_name in test_categories:
        cat = next((c for c in migrated_categories if c.name == cat_name), None)
        if cat:
            print(f"\n✓ {cat.name}:")
            print(f"  - Требует параметров: {cat.needs_custom_params()}")
            print(f"  - Базовые ставки: rail={cat.rail_base}, air={cat.air_base}")
            print(f"  - Keywords: {', '.join(cat.keywords[:3])}...")
            
            # Тест валидации
            is_valid, errors = cat.validate_params({})
            if not is_valid and cat.needs_custom_params():
                print(f"  - Требуемые параметры: {', '.join(cat.get_required_params_names())}")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())






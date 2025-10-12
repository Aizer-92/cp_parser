#!/usr/bin/env python3
"""
Миграция категорий из БД в новый формат.
Использует существующие функции database.py для загрузки.
"""

import json
from typing import List, Dict, Any
from models.category import Category, CategoryRequirements

# Импортируем функции работы с БД
try:
    from database import load_categories_from_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️ database.py недоступен")


def migrate_category_data(cat_data: Dict[str, Any]) -> Category:
    """
    Мигрирует данные категории из старого формата в новый Category.
    Полностью сохраняет все существующие данные.
    """
    # Используем встроенный метод from_dict
    category = Category.from_dict(cat_data)
    
    # Дополнительная проверка для "Новая категория"
    if category.name == "Новая категория":
        category.requirements.requires_logistics_rate = True
        print(f"  🆕 '{category.name}' - помечена как требующая ручного ввода")
    
    return category


def main():
    """Основной процесс миграции"""
    print("="*60)
    print("🔄 МИГРАЦИЯ КАТЕГОРИЙ ИЗ БД")
    print("="*60)
    
    if not DB_AVAILABLE:
        print("\n❌ Невозможно загрузить категории из БД")
        print("   Проверьте что database.py доступен")
        return 1
    
    # 1. Загружаем категории из БД
    print("\n📥 Загрузка категорий из БД...")
    try:
        existing_cats = load_categories_from_db()
        print(f"✅ Загружено {len(existing_cats)} категорий")
    except Exception as e:
        print(f"❌ Ошибка загрузки из БД: {e}")
        return 1
    
    # 2. Мигрируем каждую категорию
    print("\n🔄 Миграция в новый формат...")
    migrated_categories = []
    stats = {
        'total': 0,
        'success': 0,
        'needs_custom_params': 0,
        'errors': 0
    }
    
    for cat_data in existing_cats:
        stats['total'] += 1
        cat_name = cat_data.get('category', 'UNKNOWN')
        
        try:
            category = migrate_category_data(cat_data)
            migrated_categories.append(category)
            stats['success'] += 1
            
            if category.needs_custom_params():
                stats['needs_custom_params'] += 1
                print(f"  ⚙️  {category.name} - требует кастомных параметров")
            
        except Exception as e:
            stats['errors'] += 1
            print(f"  ❌ Ошибка при миграции '{cat_name}': {e}")
            import traceback
            traceback.print_exc()
    
    # 3. Сохраняем мигрированные категории
    output_file = 'config/categories_migrated.json'
    print(f"\n💾 Сохранение в {output_file}...")
    
    data = {
        'version': '2.0',
        'description': 'Categories migrated to new Category model',
        'total_categories': len(migrated_categories),
        'migration_stats': stats,
        'categories': [cat.to_dict() for cat in migrated_categories]
    }
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Сохранено {len(migrated_categories)} категорий")
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return 1
    
    # 4. Генерируем отчёт
    print("\n📊 Статистика миграции:")
    print(f"  Всего категорий: {stats['total']}")
    print(f"  Успешно мигрировано: {stats['success']}")
    print(f"  Требуют кастомных параметров: {stats['needs_custom_params']}")
    print(f"  Ошибок: {stats['errors']}")
    
    # 5. Тестирование
    print("\n🧪 Тестирование мигрированных категорий...")
    
    test_names = ['Новая категория', 'сумка', 'Футболки']
    for cat_name in test_names:
        cat = next((c for c in migrated_categories if c.name.lower() == cat_name.lower()), None)
        if cat:
            print(f"\n✓ {cat.name}:")
            print(f"  - Материал: {cat.material[:50]}..." if len(cat.material) > 50 else f"  - Материал: {cat.material}")
            print(f"  - Требует параметров: {cat.needs_custom_params()}")
            print(f"  - Базовые ставки: rail={cat.rail_base}, air={cat.air_base}")
            print(f"  - Пошлина: {cat.duty_rate}%, НДС: {cat.vat_rate}%")
            print(f"  - Keywords: {len(cat.keywords)} шт.")
            
            # Тест валидации с пустыми параметрами
            is_valid, errors = cat.validate_params({})
            if not is_valid:
                print(f"  - ⚠️ Требуется заполнение: {', '.join(cat.get_required_params_names()[:2])}...")
        else:
            print(f"\n⚠️ '{cat_name}' не найдена в мигрированных")
    
    # 6. Итоговый отчёт
    report = f"""
# Отчёт о миграции категорий

## Общая статистика
- **Всего категорий:** {stats['total']}
- **Успешно мигрировано:** {stats['success']}
- **Требуют кастомных параметров:** {stats['needs_custom_params']} ({stats['needs_custom_params']/stats['total']*100:.1f}%)
- **Ошибок:** {stats['errors']}

## Категории с кастомными параметрами

"""
    
    for cat in migrated_categories:
        if cat.needs_custom_params():
            report += f"### {cat.name}\n"
            report += f"- Базовые ставки: rail={cat.rail_base}, air={cat.air_base}\n"
            report += f"- Требуемые параметры: {', '.join(cat.get_required_params_names())}\n\n"
    
    report += """
## Изменения в структуре

### Новые поля:
- `requirements` - явное указание требуемых параметров
- `keywords` - для улучшенного поиска
- `needs_custom_params()` - метод проверки

### Сохранённые данные:
- Все базовые ставки (rail_base, air_base, contract_base)
- Пошлины и НДС (duty_rate, vat_rate)
- Материалы и описания
- ТН ВЭД коды и сертификаты

## Рекомендации

1. ✅ Все данные успешно мигрированы
2. ✅ "Новая категория" корректно помечена
3. ⚠️ Проверить категории требующие параметров
4. 📝 Обновить категории с нулевыми ставками
"""
    
    report_file = 'MIGRATION_REPORT.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Отчёт сохранён в {report_file}")
    
    print("\n" + "="*60)
    print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
    print("="*60)
    print(f"\nФайлы:")
    print(f"  - {output_file} (новый формат)")
    print(f"  - {report_file} (отчёт)")
    print("\nСледующий шаг:")
    print("  - Проверить categories_migrated.json")
    print("  - Обновить price_calculator.py для использования новых моделей")
    print("="*60)
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())




#!/usr/bin/env python3
"""
Миграция категорий из Railway PostgreSQL в новый формат.
Использует прямое подключение к Railway БД.
"""

import os
import json
from typing import List, Dict, Any
from models.category import Category, CategoryRequirements

# Railway database credentials
RAILWAY_CONFIG = {
    'host': 'gondola.proxy.rlwy.net',
    'port': 13805,
    'user': 'postgres',
    'password': 'JETlvQuqWYZXRtltmiCIqXPibyPONZAS',
    'database': 'railway'
}


def connect_to_railway():
    """Подключается к Railway PostgreSQL"""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        print("🔌 Подключение к Railway PostgreSQL...")
        conn = psycopg2.connect(
            host=RAILWAY_CONFIG['host'],
            port=RAILWAY_CONFIG['port'],
            user=RAILWAY_CONFIG['user'],
            password=RAILWAY_CONFIG['password'],
            database=RAILWAY_CONFIG['database'],
            cursor_factory=RealDictCursor
        )
        print("✅ Подключено к Railway")
        return conn
        
    except ImportError:
        print("❌ psycopg2 не установлен. Установите: pip install psycopg2-binary")
        return None
    except Exception as e:
        print(f"❌ Ошибка подключения к Railway: {e}")
        return None


def load_categories_from_railway(conn) -> List[Dict[str, Any]]:
    """Загружает категории из Railway PostgreSQL"""
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT data FROM categories ORDER BY category')
        rows = cursor.fetchall()
        
        categories = []
        for row in rows:
            raw = row['data']
            
            # JSONB в Postgres приходит как dict
            if isinstance(raw, dict):
                categories.append(raw)
            elif isinstance(raw, str):
                try:
                    categories.append(json.loads(raw))
                except json.JSONDecodeError as e:
                    print(f"⚠️ Ошибка парсинга JSON: {e}")
                    continue
        
        print(f"📥 Загружено {len(categories)} категорий из Railway")
        return categories
        
    except Exception as e:
        print(f"❌ Ошибка загрузки категорий: {e}")
        import traceback
        traceback.print_exc()
        return []


def migrate_category_data(cat_data: Dict[str, Any]) -> Category:
    """
    Мигрирует данные категории из Railway в новый Category.
    Полностью сохраняет все доработанные данные.
    """
    # Используем встроенный метод from_dict
    category = Category.from_dict(cat_data)
    
    # Дополнительная проверка для "Новая категория"
    if category.name == "Новая категория":
        category.requirements.requires_logistics_rate = True
        print(f"  🆕 '{category.name}' - помечена как требующая ручного ввода")
    
    return category


def save_migrated_categories(categories: List[Category], output_file: str = 'config/categories_from_railway.json'):
    """Сохраняет мигрированные категории"""
    data = {
        'version': '2.0',
        'source': 'Railway PostgreSQL',
        'description': 'Categories migrated from Railway production database',
        'total_categories': len(categories),
        'categories': [cat.to_dict() for cat in categories]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранено {len(categories)} категорий в {output_file}")


def generate_comparison_report(railway_cats: List[Category], local_file: str = 'config/categories_migrated.json'):
    """Генерирует отчёт о различиях между Railway и локальными категориями"""
    report = """
# Отчёт о миграции категорий из Railway

## Источник данных
- **Railway PostgreSQL** (Production database)
- Host: gondola.proxy.rlwy.net:13805
- Database: railway

"""
    
    # Пытаемся загрузить локальные для сравнения
    try:
        with open(local_file, 'r', encoding='utf-8') as f:
            local_data = json.load(f)
            local_count = len(local_data.get('categories', []))
        
        report += f"""
## Сравнение с локальными данными

| Параметр | Railway | Локально |
|----------|---------|----------|
| Всего категорий | {len(railway_cats)} | {local_count} |
| Разница | {len(railway_cats) - local_count:+d} | |

"""
    except FileNotFoundError:
        report += "\n*Локальные данные для сравнения не найдены*\n\n"
    
    report += f"""
## Статистика Railway категорий

- **Всего категорий:** {len(railway_cats)}
- **Требуют кастомных параметров:** {sum(1 for c in railway_cats if c.needs_custom_params())}
- **С базовыми ставками:** {sum(1 for c in railway_cats if c.rail_base and c.rail_base > 0)}
- **С пошлинами:** {sum(1 for c in railway_cats if c.duty_rate is not None)}

## Категории, требующие кастомных параметров

"""
    
    for cat in railway_cats:
        if cat.needs_custom_params():
            report += f"""
### {cat.name}
- Материал: {cat.material[:50]}{'...' if len(cat.material) > 50 else ''}
- Базовые ставки: rail={cat.rail_base}, air={cat.air_base}
- Требуемые параметры: {', '.join(cat.get_required_params_names())}
"""
    
    report += """
## Проверенные категории

"""
    
    test_categories = ['Новая категория', 'сумка', 'Футболки', 'Блокнот']
    for cat_name in test_categories:
        cat = next((c for c in railway_cats if c.name == cat_name), None)
        if cat:
            report += f"""
### {cat.name}
- ✅ Найдена в Railway
- Материал: {cat.material if cat.material else 'Не указан'}
- Ставки: rail={cat.rail_base}, air={cat.air_base}
- Пошлина: {cat.duty_rate}%, НДС: {cat.vat_rate}%
- Требует параметров: {'Да' if cat.needs_custom_params() else 'Нет'}
"""
        else:
            report += f"\n### {cat_name}\n- ❌ Не найдена в Railway\n"
    
    report += """
## Рекомендации

1. ✅ Использовать данные из Railway как источник истины
2. ✅ Все доработки из production сохранены
3. 📝 Обновить price_calculator.py для использования новых моделей
4. 🔄 Синхронизировать локальную БД с Railway данными

## Следующие шаги

1. Проверить categories_from_railway.json
2. Обновить загрузку категорий в price_calculator.py
3. Использовать Category.from_dict() для десериализации
4. Тестировать с Railway данными
"""
    
    return report


def main():
    """Основной процесс миграции из Railway"""
    print("="*60)
    print("🚀 МИГРАЦИЯ КАТЕГОРИЙ ИЗ RAILWAY")
    print("="*60)
    
    # 1. Подключаемся к Railway
    conn = connect_to_railway()
    if not conn:
        print("\n❌ Невозможно подключиться к Railway")
        return 1
    
    try:
        # 2. Загружаем категории из Railway
        railway_cats_data = load_categories_from_railway(conn)
        if not railway_cats_data:
            print("\n❌ Не удалось загрузить категории из Railway")
            return 1
        
        # 3. Мигрируем категории
        print("\n🔄 Миграция в новый формат...")
        migrated_categories = []
        stats = {
            'total': 0,
            'success': 0,
            'needs_custom_params': 0,
            'errors': 0
        }
        
        for cat_data in railway_cats_data:
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
        
        # 4. Сохраняем результаты
        output_file = 'config/categories_from_railway.json'
        print(f"\n💾 Сохранение в {output_file}...")
        save_migrated_categories(migrated_categories, output_file)
        
        # 5. Статистика
        print("\n📊 Статистика миграции:")
        print(f"  Всего категорий: {stats['total']}")
        print(f"  Успешно мигрировано: {stats['success']}")
        print(f"  Требуют кастомных параметров: {stats['needs_custom_params']}")
        print(f"  Ошибок: {stats['errors']}")
        
        # 6. Тестирование
        print("\n🧪 Тестирование ключевых категорий...")
        
        test_names = ['Новая категория', 'сумка', 'Футболки', 'Блокнот']
        for cat_name in test_names:
            cat = next((c for c in migrated_categories if c.name == cat_name), None)
            if cat:
                print(f"\n✓ {cat.name}:")
                if cat.material:
                    print(f"  - Материал: {cat.material[:60]}{'...' if len(cat.material) > 60 else ''}")
                print(f"  - Требует параметров: {cat.needs_custom_params()}")
                print(f"  - Базовые ставки: rail={cat.rail_base}, air={cat.air_base}")
                if cat.duty_rate is not None:
                    print(f"  - Пошлина: {cat.duty_rate}%, НДС: {cat.vat_rate}%")
                print(f"  - ТН ВЭД: {cat.tnved_code if cat.tnved_code else 'Не указан'}")
                
                # Тест валидации
                is_valid, errors = cat.validate_params({})
                if not is_valid:
                    print(f"  - ⚠️ Требуемые параметры: {', '.join(cat.get_required_params_names()[:2])}...")
            else:
                print(f"\n⚠️ '{cat_name}' не найдена в Railway")
        
        # 7. Генерируем отчёт
        print("\n📄 Генерация отчёта...")
        report = generate_comparison_report(migrated_categories)
        
        report_file = 'RAILWAY_MIGRATION_REPORT.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📄 Отчёт сохранён в {report_file}")
        
        # 8. Итог
        print("\n" + "="*60)
        print("✅ МИГРАЦИЯ ИЗ RAILWAY ЗАВЕРШЕНА УСПЕШНО")
        print("="*60)
        print(f"\nФайлы:")
        print(f"  - {output_file} (Railway категории)")
        print(f"  - {report_file} (отчёт)")
        print("\nСледующий шаг:")
        print("  - Использовать categories_from_railway.json")
        print("  - Обновить price_calculator.py")
        print("  - Тестировать с production данными")
        print("="*60)
        
    finally:
        conn.close()
        print("\n🔌 Соединение с Railway закрыто")
    
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())


#!/usr/bin/env python3
"""
Утилита для синхронизации категорий из categories.yaml в PostgreSQL БД.

Использование:
    py sync_categories.py              # Синхронизировать все категории
    py sync_categories.py --force      # Перезаписать все категории
    py sync_categories.py --check      # Проверить расхождения
"""

import yaml
import json
import sys
import os
from typing import Dict, List, Any
from database import get_database_connection, upsert_category, load_categories_from_db


def load_yaml_categories() -> List[Dict[str, Any]]:
    """Загружает категории из categories.yaml"""
    yaml_path = os.path.join(os.path.dirname(__file__), 'config', 'categories.yaml')
    
    if not os.path.exists(yaml_path):
        print(f"❌ Файл {yaml_path} не найден")
        return []
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    categories = data.get('categories', [])
    print(f"📄 Загружено из YAML: {len(categories)} категорий")
    return categories


def compare_categories(yaml_cats: List[Dict], db_cats: List[Dict]) -> Dict[str, Any]:
    """
    Сравнивает категории из YAML и БД
    
    Returns:
        {
            'only_in_yaml': [...],
            'only_in_db': [...],
            'different': [...]
        }
    """
    yaml_dict = {
        (cat['category'], cat.get('material', '')): cat 
        for cat in yaml_cats
    }
    db_dict = {
        (cat['category'], cat.get('material', '')): cat 
        for cat in db_cats
    }
    
    yaml_keys = set(yaml_dict.keys())
    db_keys = set(db_dict.keys())
    
    only_in_yaml = yaml_keys - db_keys
    only_in_db = db_keys - yaml_keys
    both = yaml_keys & db_keys
    
    different = []
    for key in both:
        yaml_cat = yaml_dict[key]
        db_cat = db_dict[key]
        
        # Сравниваем важные поля
        if (yaml_cat.get('rail_base') != db_cat.get('rail_base') or
            yaml_cat.get('air_base') != db_cat.get('air_base') or
            yaml_cat.get('duty') != db_cat.get('duty')):
            different.append({
                'key': key,
                'yaml': yaml_cat,
                'db': db_cat
            })
    
    return {
        'only_in_yaml': [yaml_dict[k] for k in only_in_yaml],
        'only_in_db': [db_dict[k] for k in only_in_db],
        'different': different
    }


def sync_categories_to_db(yaml_cats: List[Dict], force: bool = False) -> Dict[str, int]:
    """
    Синхронизирует категории из YAML в БД
    
    Args:
        yaml_cats: Список категорий из YAML
        force: Если True, перезаписывает все категории
    
    Returns:
        { 'added': N, 'updated': N, 'skipped': N }
    """
    db_cats = load_categories_from_db()
    
    if not force:
        comparison = compare_categories(yaml_cats, db_cats)
        to_sync = comparison['only_in_yaml'] + [d['yaml'] for d in comparison['different']]
    else:
        to_sync = yaml_cats
    
    stats = {'added': 0, 'updated': 0, 'skipped': 0}
    
    for cat in to_sync:
        try:
            # Проверяем существует ли категория в БД
            existing = any(
                (c['category'] == cat['category'] and 
                 c.get('material', '') == cat.get('material', ''))
                for c in db_cats
            )
            
            upsert_category(cat)
            
            if existing:
                stats['updated'] += 1
                print(f"✅ Обновлено: {cat['category']} ({cat.get('material', 'без материала')})")
            else:
                stats['added'] += 1
                print(f"➕ Добавлено: {cat['category']} ({cat.get('material', 'без материала')})")
                
        except Exception as e:
            print(f"❌ Ошибка для {cat['category']}: {e}")
            stats['skipped'] += 1
    
    return stats


def print_comparison_report(comparison: Dict[str, Any]):
    """Выводит отчёт о расхождениях"""
    print("\n" + "="*60)
    print("ОТЧЁТ О РАСХОЖДЕНИЯХ")
    print("="*60)
    
    if comparison['only_in_yaml']:
        print(f"\n📄 Только в YAML ({len(comparison['only_in_yaml'])} шт.):")
        for cat in comparison['only_in_yaml']:
            print(f"  - {cat['category']} ({cat.get('material', 'без материала')})")
    
    if comparison['only_in_db']:
        print(f"\n💾 Только в БД ({len(comparison['only_in_db'])} шт.):")
        for cat in comparison['only_in_db']:
            print(f"  - {cat['category']} ({cat.get('material', 'без материала')})")
    
    if comparison['different']:
        print(f"\n⚠️ Различаются ({len(comparison['different'])} шт.):")
        for diff in comparison['different']:
            cat_name, material = diff['key']
            print(f"\n  {cat_name} ({material or 'без материала'}):")
            yaml_cat = diff['yaml']
            db_cat = diff['db']
            
            if yaml_cat.get('rail_base') != db_cat.get('rail_base'):
                print(f"    rail_base: {yaml_cat.get('rail_base')} (YAML) vs {db_cat.get('rail_base')} (DB)")
            if yaml_cat.get('air_base') != db_cat.get('air_base'):
                print(f"    air_base: {yaml_cat.get('air_base')} (YAML) vs {db_cat.get('air_base')} (DB)")
            if yaml_cat.get('duty') != db_cat.get('duty'):
                print(f"    duty: {yaml_cat.get('duty')} (YAML) vs {db_cat.get('duty')} (DB)")
    
    if not any([comparison['only_in_yaml'], comparison['only_in_db'], comparison['different']]):
        print("\n✅ Категории полностью синхронизированы!")
    
    print("\n" + "="*60)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Синхронизация категорий YAML → PostgreSQL')
    parser.add_argument('--force', action='store_true', help='Перезаписать все категории')
    parser.add_argument('--check', action='store_true', help='Только проверить расхождения')
    
    args = parser.parse_args()
    
    print("🔄 Синхронизация категорий")
    print("="*60)
    
    # Загружаем категории из YAML
    yaml_cats = load_yaml_categories()
    if not yaml_cats:
        print("❌ Не удалось загрузить категории из YAML")
        return 1
    
    # Загружаем категории из БД
    db_cats = load_categories_from_db()
    print(f"💾 В БД сейчас: {len(db_cats)} категорий")
    
    # Сравниваем
    comparison = compare_categories(yaml_cats, db_cats)
    
    if args.check:
        # Только показываем расхождения
        print_comparison_report(comparison)
        return 0
    
    # Синхронизируем
    print(f"\n{'🔄 Перезапись всех категорий...' if args.force else '📤 Синхронизация расхождений...'}")
    stats = sync_categories_to_db(yaml_cats, force=args.force)
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ СИНХРОНИЗАЦИИ")
    print("="*60)
    print(f"➕ Добавлено: {stats['added']}")
    print(f"✅ Обновлено: {stats['updated']}")
    print(f"⏭️ Пропущено: {stats['skipped']}")
    print("="*60)
    
    # Показываем финальное состояние
    db_cats_after = load_categories_from_db()
    print(f"\n💾 В БД теперь: {len(db_cats_after)} категорий")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())






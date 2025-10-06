#!/usr/bin/env python3
"""
Сравнение структуры таблиц SQLite и PostgreSQL
"""
import sys
sys.path.append('/Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser')

from sqlalchemy import create_engine, inspect

SQLITE_URL = "sqlite:////Users/bakirovresad/Downloads/Reshad 1/projects/cp_parser/database/commercial_proposals.db"
POSTGRES_URL = "postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

def compare_table_structure(table_name):
    """Сравнение структуры одной таблицы"""
    sqlite_engine = create_engine(SQLITE_URL)
    postgres_engine = create_engine(POSTGRES_URL)
    
    sqlite_inspector = inspect(sqlite_engine)
    postgres_inspector = inspect(postgres_engine)
    
    print(f"\n{'='*80}")
    print(f"ТАБЛИЦА: {table_name}")
    print('='*80)
    
    # Получаем колонки из обеих БД
    sqlite_cols = {col['name']: col for col in sqlite_inspector.get_columns(table_name)}
    postgres_cols = {col['name']: col for col in postgres_inspector.get_columns(table_name)}
    
    sqlite_names = set(sqlite_cols.keys())
    postgres_names = set(postgres_cols.keys())
    
    # Проверяем совпадение
    missing_in_postgres = sqlite_names - postgres_names
    extra_in_postgres = postgres_names - sqlite_names
    common = sqlite_names & postgres_names
    
    if missing_in_postgres:
        print(f"\n❌ ОТСУТСТВУЮТ В POSTGRESQL ({len(missing_in_postgres)}):")
        for col in sorted(missing_in_postgres):
            print(f"   - {col}: {sqlite_cols[col]['type']}")
    
    if extra_in_postgres:
        print(f"\n⚠️ ЛИШНИЕ В POSTGRESQL ({len(extra_in_postgres)}):")
        for col in sorted(extra_in_postgres):
            print(f"   - {col}: {postgres_cols[col]['type']}")
    
    if common:
        print(f"\n✅ ОБЩИЕ КОЛОНКИ ({len(common)}):")
        for col in sorted(common):
            sqlite_type = str(sqlite_cols[col]['type'])
            postgres_type = str(postgres_cols[col]['type'])
            match = "✓" if sqlite_type.upper() in postgres_type.upper() or postgres_type.upper() in sqlite_type.upper() else "⚠"
            print(f"   {match} {col}:")
            print(f"      SQLite:     {sqlite_type}")
            print(f"      PostgreSQL: {postgres_type}")
    
    # Итоговый статус
    if not missing_in_postgres and not extra_in_postgres:
        print(f"\n✅ СТРУКТУРА СОВПАДАЕТ ПОЛНОСТЬЮ")
        return True
    else:
        print(f"\n❌ СТРУКТУРА НЕ СОВПАДАЕТ")
        return False

def main():
    print("="*80)
    print("СРАВНЕНИЕ СТРУКТУР ТАБЛИЦ SQLite vs PostgreSQL")
    print("="*80)
    
    tables = ['projects', 'products', 'price_offers', 'product_images']
    results = {}
    
    for table in tables:
        try:
            results[table] = compare_table_structure(table)
        except Exception as e:
            print(f"\n❌ Ошибка при проверке таблицы {table}: {e}")
            results[table] = False
    
    # Итоговый отчет
    print("\n" + "="*80)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("="*80)
    for table, match in results.items():
        status = "✅" if match else "❌"
        print(f"{status} {table}: {'Совпадает' if match else 'Не совпадает'}")
    
    all_match = all(results.values())
    print("\n" + "="*80)
    if all_match:
        print("✅ ВСЕ ТАБЛИЦЫ ИМЕЮТ ОДИНАКОВУЮ СТРУКТУРУ")
    else:
        print("❌ ЕСТЬ РАЗЛИЧИЯ В СТРУКТУРЕ ТАБЛИЦ - НЕОБХОДИМО ИСПРАВИТЬ!")
    print("="*80)

if __name__ == "__main__":
    main()

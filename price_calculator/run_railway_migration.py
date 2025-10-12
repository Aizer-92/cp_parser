#!/usr/bin/env python3
"""
Скрипт для выполнения миграций на Railway PostgreSQL

Использование:
    python3 run_railway_migration.py migrations/001_add_custom_logistics_and_forced_category.py
"""

import os
import sys

# Устанавливаем переменные окружения для Railway (временно)
# В продакшене эти значения должны быть в .env файле!
if not os.getenv('RAILWAY_DB_PASSWORD'):
    print("⚠️ Внимание: Используем временные credentials")
    print("⚠️ Для продакшена установите переменные окружения в .env")
    os.environ['DATABASE_PUBLIC_URL'] = 'postgresql://postgres:JETlvQuqWYZXRtltmiCIqXPibyPONZAS@gondola.proxy.rlwy.net:13805/railway'

# Запускаем миграцию
if len(sys.argv) < 2:
    print("❌ Укажите путь к файлу миграции")
    print(f"   Использование: python3 {sys.argv[0]} migrations/001_...py")
    sys.exit(1)

migration_file = sys.argv[1]

if not os.path.exists(migration_file):
    print(f"❌ Файл {migration_file} не найден!")
    sys.exit(1)

print(f"🚀 Запуск миграции: {migration_file}")
print("🎯 Цель: Railway PostgreSQL")
print("-" * 60)

# Запускаем миграцию как модуль
import importlib.util
spec = importlib.util.spec_from_file_location("migration", migration_file)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)

# Вызываем функцию миграции
if hasattr(migration, 'run_migration'):
    success = migration.run_migration()
    sys.exit(0 if success else 1)
else:
    print("❌ Файл миграции не содержит функцию run_migration()")
    sys.exit(1)





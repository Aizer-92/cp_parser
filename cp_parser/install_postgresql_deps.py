#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Установка зависимостей для работы с PostgreSQL
"""

import subprocess
import sys

def install_package(package):
    """Устанавливает пакет через pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} установлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package}: {e}")
        return False

def main():
    """Устанавливает все необходимые зависимости"""
    print("📦 Установка зависимостей для PostgreSQL...")
    print("=" * 50)
    
    packages = [
        "psycopg2-binary",  # PostgreSQL адаптер для Python
        "sqlalchemy",       # ORM (если еще не установлен)
        "pandas",           # Для работы с данными
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print("=" * 50)
    print(f"📊 Результат: {success_count}/{len(packages)} пакетов установлено")
    
    if success_count == len(packages):
        print("🎉 Все зависимости установлены успешно!")
        print("✅ Теперь можно запускать миграцию базы данных")
    else:
        print("⚠️  Некоторые пакеты не удалось установить")
        print("🔧 Попробуйте установить их вручную:")

if __name__ == "__main__":
    main()

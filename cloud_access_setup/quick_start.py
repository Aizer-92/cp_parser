#!/usr/bin/env python3
"""
Быстрый старт для настройки облачного доступа
Запустите: python quick_start.py
"""

import os
import sys
import subprocess
from pathlib import Path

def print_step(step, description):
    """Выводит шаг с описанием"""
    print(f"\n{'='*50}")
    print(f"🔄 Шаг {step}: {description}")
    print(f"{'='*50}")

def run_command(command, description=""):
    """Выполняет команду и выводит результат"""
    print(f"💻 Выполняю: {command}")
    if description:
        print(f"📝 {description}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Успешно выполнено")
            if result.stdout:
                print(f"📤 Вывод: {result.stdout.strip()}")
        else:
            print(f"❌ Ошибка: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"❌ Исключение: {e}")
        return False

def check_git_installed():
    """Проверяет установлен ли git"""
    return run_command("git --version", "Проверка установки Git")

def check_python_dependencies():
    """Проверяет и устанавливает Python зависимости"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if requirements_file.exists():
        print("📦 Устанавливаю Python зависимости...")
        return run_command(f"pip install -r {requirements_file}", "Установка зависимостей")
    return True

def setup_git_repository():
    """Настраивает git репозиторий"""
    project_root = Path(__file__).parent.parent.parent
    
    # Проверяем есть ли уже git репозиторий
    if (project_root / ".git").exists():
        print("ℹ️ Git репозиторий уже существует")
        return True
    
    # Инициализируем git
    if not run_command(f"cd {project_root} && git init", "Инициализация Git репозитория"):
        return False
    
    # Создаем .gitignore
    gitignore_content = """# Виртуальные окружения
venv/
.venv/
env/
.env/

# Кэш Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Временные файлы
temp/
tmp/
*.tmp
*.temp

# Конфиденциальные данные
*.json
credentials/
config.json
personal_account.session
.env
.env.local

# Логи
*.log
logs/
log/

# Выходные файлы
output/
*.xlsx
*.png
*.jpg
*.jpeg
*.pdf

# Системные файлы
.DS_Store
Thumbs.db
desktop.ini

# IDE файлы
.vscode/
.idea/
*.swp
*.swo

# Архивы
*.tar.gz
*.zip
*.rar

# Базы данных
*.db
*.sqlite
*.sqlite3
"""
    
    gitignore_path = project_root / ".gitignore"
    with open(gitignore_path, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("✅ Создан .gitignore файл")
    
    return True

def create_initial_commit():
    """Создает первый коммит"""
    project_root = Path(__file__).parent.parent.parent
    
    commands = [
        f"cd {project_root} && git add .",
        f"cd {project_root} && git commit -m 'Initial commit: Personal projects setup'"
    ]
    
    for cmd in commands:
        if not run_command(cmd, "Создание первого коммита"):
            return False
    
    return True

def show_next_steps():
    """Показывает следующие шаги"""
    print(f"\n{'='*50}")
    print("🎉 Базовая настройка завершена!")
    print(f"{'='*50}")
    
    print("""
📋 Следующие шаги:

1. 🌐 Создайте аккаунт на GitHub:
   - Перейдите на https://github.com
   - Нажмите "Sign up" и создайте аккаунт

2. 📁 Создайте репозиторий на GitHub:
   - Нажмите "+" → "New repository"
   - Название: reshad-personal-projects
   - Выберите Public или Private
   - НЕ ставьте галочки на README, .gitignore, license

3. 🔗 Подключите локальный репозиторий к GitHub:
   ```bash
   cd /Users/bakirovresad/Downloads/Reshad
   git remote add origin https://github.com/YOUR_USERNAME/reshad-personal-projects.git
   git push -u origin main
   ```

4. 📱 Установите GitHub app на телефон:
   - iOS: https://apps.apple.com/app/github/id1477376905
   - Android: https://play.google.com/store/apps/details?id=com.github.android

5. ☁️ Для синхронизации с Google Drive:
   - Следуйте инструкциям в SETUP_GUIDE.md
   - Или запустите: python google_drive_sync.py

📖 Подробные инструкции: projects/cloud_access_setup/SETUP_GUIDE.md
""")

def main():
    """Основная функция"""
    print("🚀 Быстрый старт настройки облачного доступа")
    print("Этот скрипт настроит базовую структуру для синхронизации")
    
    # Шаг 1: Проверка Git
    print_step(1, "Проверка Git")
    if not check_git_installed():
        print("❌ Git не установлен. Установите Git и повторите.")
        return
    
    # Шаг 2: Установка зависимостей
    print_step(2, "Установка Python зависимостей")
    if not check_python_dependencies():
        print("❌ Ошибка установки зависимостей")
        return
    
    # Шаг 3: Настройка Git репозитория
    print_step(3, "Настройка Git репозитория")
    if not setup_git_repository():
        print("❌ Ошибка настройки Git репозитория")
        return
    
    # Шаг 4: Первый коммит
    print_step(4, "Создание первого коммита")
    if not create_initial_commit():
        print("❌ Ошибка создания первого коммита")
        return
    
    # Показываем следующие шаги
    show_next_steps()

if __name__ == "__main__":
    main()

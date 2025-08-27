#!/usr/bin/env python3
"""
Автоматическая синхронизация проекта с GitHub
Использование: python auto_sync.py [--force] [--message "custom message"]
"""

import subprocess
import os
import sys
import argparse
from datetime import datetime
import json

class ProjectSync:
    def __init__(self, project_root=None):
        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.gitignore_path = os.path.join(self.project_root, '.gitignore')
        
    def check_git_status(self):
        """Проверяет статус git репозитория"""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None
            
    def create_gitignore(self):
        """Создает .gitignore файл если его нет"""
        if os.path.exists(self.gitignore_path):
            return
            
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
        
        with open(self.gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        print(f"✅ Создан .gitignore файл")
        
    def init_git_repo(self):
        """Инициализирует git репозиторий если его нет"""
        git_dir = os.path.join(self.project_root, '.git')
        if os.path.exists(git_dir):
            return True
            
        try:
            subprocess.run(['git', 'init'], cwd=self.project_root, check=True)
            print("✅ Git репозиторий инициализирован")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка инициализации git: {e}")
            return False
            
    def add_files(self):
        """Добавляет файлы в git"""
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.project_root, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка добавления файлов: {e}")
            return False
            
    def commit_changes(self, message=None):
        """Создает коммит"""
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Auto sync: {timestamp}"
            
        try:
            subprocess.run(['git', 'commit', '-m', message], 
                         cwd=self.project_root, check=True)
            print(f"✅ Коммит создан: {message}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка создания коммита: {e}")
            return False
            
    def push_changes(self):
        """Отправляет изменения на GitHub"""
        try:
            subprocess.run(['git', 'push'], cwd=self.project_root, check=True)
            print("✅ Изменения отправлены на GitHub")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка отправки на GitHub: {e}")
            print("💡 Убедитесь что репозиторий подключен к GitHub")
            return False
            
    def setup_remote(self, repo_url):
        """Настраивает удаленный репозиторий"""
        try:
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], 
                         cwd=self.project_root, check=True)
            print(f"✅ Удаленный репозиторий добавлен: {repo_url}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка добавления удаленного репозитория: {e}")
            return False
            
    def sync(self, force=False, message=None):
        """Основная функция синхронизации"""
        print("🔄 Начинаю синхронизацию...")
        
        # Проверяем и создаем .gitignore
        self.create_gitignore()
        
        # Инициализируем git если нужно
        if not self.init_git_repo():
            return False
            
        # Проверяем статус
        status = self.check_git_status()
        if not status and not force:
            print("ℹ️ Нет изменений для синхронизации")
            return True
            
        # Добавляем файлы
        if not self.add_files():
            return False
            
        # Создаем коммит
        if not self.commit_changes(message):
            return False
            
        # Отправляем на GitHub
        if not self.push_changes():
            return False
            
        print("✅ Синхронизация завершена успешно!")
        return True

def main():
    parser = argparse.ArgumentParser(description='Автоматическая синхронизация с GitHub')
    parser.add_argument('--force', action='store_true', 
                       help='Принудительная синхронизация даже без изменений')
    parser.add_argument('--message', '-m', type=str,
                       help='Кастомное сообщение для коммита')
    parser.add_argument('--setup', type=str,
                       help='URL GitHub репозитория для первоначальной настройки')
    
    args = parser.parse_args()
    
    sync = ProjectSync()
    
    if args.setup:
        if sync.setup_remote(args.setup):
            print("🎉 Настройка завершена! Теперь можете использовать --force для первой синхронизации")
        return
        
    success = sync.sync(force=args.force, message=args.message)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

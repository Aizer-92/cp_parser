#!/bin/bash

echo "🚀 Запуск Planfix Dashboard 2025..."

# Переходим в папку проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем дашборд
python3 final_dashboard.py

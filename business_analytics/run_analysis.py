#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Главный скрипт для запуска всех видов бизнес-анализа
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Запуск скрипта с обработкой ошибок"""
    print(f"\n{'='*60}")
    print(f"🚀 ЗАПУСК: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True, 
                              check=True)
        print(f"✅ Завершен: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка в {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Файл не найден: {script_name}")
        return False

def main():
    print("📊 ФИНАЛЬНАЯ БИЗНЕС-АНАЛИТИКА")
    print("=" * 60)
    print("Гауссовские диапазоны для каждой категории отдельно")
    print("Чистые бизнес-отчеты без технических деталей")
    print()
    print("Выберите тип отчета:")
    print()
    print("1. 🎯 Финальный Бизнес-Анализ")
    print("   • Анализ с гауссовскими диапазонами для каждой категории")
    print("   • 70% значений для планирования закупок")
    print("   • Покрытие: 70.7% товаров")
    print()
    print("2. 📊 Создать Excel отчет")
    print("   • 4 листа: категории, топ-20, детальные диапазоны, сводка")
    print("   • 575 гауссовских распределений по всем категориям")
    print("   • Готовые таблицы для бизнес-анализа")
    print()
    print("3. 📋 Создать чистый бизнес-отчет")
    print("   • Markdown отчет без технических подробностей")
    print("   • Готовые рекомендации для принятия решений")
    print("   • Структурированный анализ для презентаций")
    print()
    print("0. Выход")
    print()
    
    while True:
        try:
            choice = input("Ваш выбор (0-3): ").strip()
            
            if choice == "0":
                print("👋 До свидания!")
                break
                
            elif choice == "1":
                run_script("business_final_analyzer.py", "🎯 ФИНАЛЬНЫЙ БИЗНЕС-АНАЛИЗ")
                
            elif choice == "2":
                run_script("create_business_excel.py", "📊 СОЗДАНИЕ EXCEL ОТЧЕТА")
                
            elif choice == "3":
                run_script("create_clean_business_report.py", "📋 СОЗДАНИЕ ЧИСТОГО БИЗНЕС-ОТЧЕТА")
                
            else:
                print("❌ Неверный выбор. Попробуйте снова.")
                continue
                
            print("\nХотите создать еще один отчет? (y/n): ", end="")
            continue_choice = input().strip().lower()
            if continue_choice not in ['y', 'yes', 'д', 'да']:
                print("✅ Анализ завершен!")
                break
                
        except KeyboardInterrupt:
            print("\n\n👋 Анализ прерван пользователем.")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    # Проверяем что мы в правильной директории
    current_dir = Path(__file__).parent
    required_files = [
        "business_final_analyzer.py",
        "create_business_excel.py", 
        "create_clean_business_report.py"
    ]
    
    missing_files = [f for f in required_files if not (current_dir / f).exists()]
    if missing_files:
        print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
        print("Убедитесь что вы запускаете скрипт из папки business_analytics")
        sys.exit(1)
    
    main()
#!/usr/bin/env python3
"""
Точная проверка числовых диапазонов для Personal Super Agent

Использование:
    python3 check_range.py value min max [value2 min2 max2 ...]
    
Примеры:
    python3 check_range.py 185 125 200
    python3 check_range.py 185 125 200 92 70 100
    
Этот скрипт избегает ошибок LLM в математических вычислениях,
предоставляя точные проверки диапазонов для:
- Медицинских показателей
- Бюджетных лимитов  
- Целевых значений
- Любых числовых проверок
"""

import sys
import argparse

def check_range(value, min_val, max_val):
    """
    Проверяет, находится ли значение в заданном диапазоне.
    
    Args:
        value (float): Проверяемое значение
        min_val (float): Минимальное значение диапазона (включительно)
        max_val (float): Максимальное значение диапазона (включительно)
        
    Returns:
        bool: True если значение в диапазоне, False иначе
    """
    return min_val <= value <= max_val

def format_result(value, min_val, max_val, in_range):
    """Форматирует результат проверки для читаемого вывода."""
    status = "✅ В диапазоне" if in_range else "❌ Вне диапазона"
    return f"{value:8.1f} | [{min_val:8.1f} - {max_val:8.1f}] | {status}"

def main():
    if len(sys.argv) < 4:
        print("Использование: python3 check_range.py value min max [value2 min2 max2 ...]")
        print("Пример: python3 check_range.py 185 125 200")
        sys.exit(1)
    
    # Проверяем, что количество аргументов кратно 3
    args = sys.argv[1:]
    if len(args) % 3 != 0:
        print("Ошибка: Аргументы должны быть в формате: value min max")
        print("Количество аргументов должно быть кратно 3")
        sys.exit(1)
    
    try:
        # Конвертируем строки в числа
        numbers = [float(arg) for arg in args]
        
        print("🔍 Проверка диапазона:")
        print("=" * 50)
        
        all_in_range = True
        
        # Обрабатываем тройки (value, min, max)
        for i in range(0, len(numbers), 3):
            value = numbers[i]
            min_val = numbers[i + 1]
            max_val = numbers[i + 2]
            
            # Проверяем корректность диапазона
            if min_val > max_val:
                print(f"Ошибка: Минимум ({min_val}) больше максимума ({max_val})")
                sys.exit(1)
            
            in_range = check_range(value, min_val, max_val)
            if not in_range:
                all_in_range = False
            
            print(format_result(value, min_val, max_val, in_range))
        
        print("=" * 50)
        
        # Общий результат
        if all_in_range:
            print("✅ Все значения в норме")
            sys.exit(0)
        else:
            print("⚠️  Некоторые значения вне диапазона")
            sys.exit(1)
            
    except ValueError as e:
        print(f"Ошибка: Невозможно преобразовать аргументы в числа - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

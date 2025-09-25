#!/usr/bin/env python3
"""
Диагностика проблемы с агентом Cursor
Проблема: Агент не продолжает работу после выполнения команд в терминале,
остается в постоянном ожидании завершения команды.

Этот скрипт помогает понять и решить проблемы с:
- Блокирующими командами
- Неправильным завершением процессов
- Проблемами с выводом команд
- Таймаутами агента
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

def print_header(title):
    """Печатает заголовок секции"""
    print(f"\n{'='*60}")
    print(f"🤖 {title}")
    print(f"{'='*60}")

def print_step(step, description):
    """Печатает шаг диагностики"""
    print(f"\n📋 Шаг {step}: {description}")
    print("-" * 40)

def test_command_completion():
    """Тестирует различные типы команд на предмет правильного завершения"""
    print_header("ТЕСТИРОВАНИЕ ЗАВЕРШЕНИЯ КОМАНД")
    
    test_commands = [
        {
            "command": "echo 'Test completed'",
            "description": "Простая команда с выводом",
            "should_complete": True
        },
        {
            "command": "py -c \"print('Python test completed')\"",
            "description": "Python команда с выводом",
            "should_complete": True
        },
        {
            "command": "py -c \"import time; time.sleep(2); print('Delayed completion')\"",
            "description": "Команда с задержкой",
            "should_complete": True
        },
        {
            "command": "py -c \"print('Start'); import sys; sys.stdout.flush(); print('End')\"",
            "description": "Команда с принудительным flush",
            "should_complete": True
        },
        {
            "command": "py -c \"while True: pass\"",
            "description": "Бесконечный цикл (должен зависнуть)",
            "should_complete": False,
            "timeout": 3
        }
    ]
    
    for i, test in enumerate(test_commands, 1):
        print_step(f"Тест {i}", test["description"])
        print(f" Команда: {test['command']}")
        
        timeout = test.get("timeout", 10)
        
        try:
            # Запускаем команду с таймаутом
            result = subprocess.run(
                test["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                print("✅ Команда завершилась успешно")
                if result.stdout.strip():
                    print(f"📤 Вывод: {result.stdout.strip()}")
            else:
                print(f"❌ Команда завершилась с ошибкой (код {result.returncode})")
                if result.stderr.strip():
                    print(f"📤 Ошибка: {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            if test["should_complete"]:
                print(f"⏰ Таймаут! Команда не завершилась за {timeout} сек")
                print("   → Это может быть причиной зависания агента")
            else:
                print(f"⏰ Ожидаемый таймаут (команда должна зависнуть)")
        except Exception as e:
            print(f"❌ Исключение: {e}")

def test_interactive_commands():
    """Тестирует интерактивные команды, которые могут зависнуть"""
    print_header("ТЕСТИРОВАНИЕ ИНТЕРАКТИВНЫХ КОМАНД")
    
    interactive_commands = [
        {
            "command": "py -c \"input('Введите что-то: ')\"",
            "description": "Команда с input() - ждет ввода",
            "problem": "Ждет ввода от пользователя"
        },
        {
            "command": "py -c \"import sys; sys.stdin.read()\"",
            "description": "Команда читает stdin до EOF",
            "problem": "Ждет закрытия stdin"
        },
        {
            "command": "py -c \"while True: print('Running...'); import time; time.sleep(1)\"",
            "description": "Бесконечный цикл с выводом",
            "problem": "Никогда не завершается"
        }
    ]
    
    for i, test in enumerate(interactive_commands, 1):
        print_step(f"Интерактивный тест {i}", test["description"])
        print(f" Команда: {test['command']}")
        print(f"⚠️  Проблема: {test['problem']}")
        
        # Запускаем команду в отдельном процессе
        try:
            process = subprocess.Popen(
                test["command"],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Ждем 2 секунды
            time.sleep(2)
            
            # Проверяем, завершился ли процесс
            if process.poll() is None:
                print("⏰ Процесс все еще работает (завис)")
                print("   → Это может быть причиной зависания агента")
                # Завершаем процесс
                process.terminate()
                process.wait(timeout=5)
            else:
                print("✅ Процесс завершился")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def test_output_buffering():
    """Тестирует проблемы с буферизацией вывода"""
    print_header("ТЕСТИРОВАНИЕ БУФЕРИЗАЦИИ ВЫВОДА")
    
    buffering_tests = [
        {
            "command": "py -c \"print('Line 1'); print('Line 2'); print('Line 3')\"",
            "description": "Множественный вывод без flush",
            "expected": "Все строки должны появиться"
        },
        {
            "command": "py -c \"import sys; print('Line 1'); sys.stdout.flush(); print('Line 2'); sys.stdout.flush()\"",
            "description": "Вывод с принудительным flush",
            "expected": "Строки появляются по мере выполнения"
        },
        {
            "command": "py -c \"import sys; sys.stdout = sys.stderr; print('To stderr')\"",
            "description": "Вывод в stderr",
            "expected": "Вывод должен появиться в stderr"
        }
    ]
    
    for i, test in enumerate(buffering_tests, 1):
        print_step(f"Буферизация {i}", test["description"])
        print(f" Команда: {test['command']}")
        print(f"🎯 Ожидается: {test['expected']}")
        
        try:
            result = subprocess.run(
                test["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            print(f"📤 stdout: {result.stdout.strip()}")
            if result.stderr.strip():
                print(f"📤 stderr: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def create_agent_safe_commands():
    """Создает примеры безопасных команд для агента"""
    print_header("БЕЗОПАСНЫЕ КОМАНДЫ ДЛЯ АГЕНТА")
    
    safe_commands = {
        "python_simple": {
            "command": "py -c \"print('Hello from Python')\"",
            "description": "Простая Python команда с выводом"
        },
        "python_with_flush": {
            "command": "py -c \"import sys; print('Start'); sys.stdout.flush(); print('End'); sys.stdout.flush()\"",
            "description": "Python команда с принудительным flush"
        },
        "python_with_timeout": {
            "command": "timeout 10 py -c \"import time; time.sleep(5); print('Completed')\"",
            "description": "Python команда с таймаутом"
        },
        "file_operations": {
            "command": "py -c \"import os; print(f'Current dir: {os.getcwd()}'); print(f'Files: {len(os.listdir())}')\"",
            "description": "Операции с файлами"
        },
        "system_info": {
            "command": "py -c \"import platform; print(f'OS: {platform.system()}'); print(f'Python: {platform.python_version()}')\"",
            "description": "Информация о системе"
        }
    }
    
    print("✅ Рекомендуемые безопасные команды:")
    for name, cmd in safe_commands.items():
        print(f"\n🔧 {name}:")
        print(f"   Команда: {cmd['command']}")
        print(f"   Описание: {cmd['description']}")
    
    # Создаем файл с безопасными командами
    script_content = '''#!/bin/bash
# Безопасные команды для агента Cursor

echo "🤖 Безопасные команды для агента"

# 1. Простая Python команда
echo "📋 Тест 1: Простая команда"
py -c "print('Hello from Python')"

# 2. Команда с flush
echo "📋 Тест 2: Команда с flush"
py -c "import sys; print('Start'); sys.stdout.flush(); print('End'); sys.stdout.flush()"

# 3. Команда с таймаутом
echo "📋 Тест 3: Команда с таймаутом"
timeout 5 py -c "import time; time.sleep(2); print('Completed')"

# 4. Информация о системе
echo "📋 Тест 4: Информация о системе"
py -c "import platform; print(f'OS: {platform.system()}'); print(f'Python: {platform.python_version()}')"

echo "✅ Все тесты завершены"
'''
    
    script_path = Path.cwd() / "agent_safe_commands.sh"
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"\n✅ Создан скрипт с безопасными командами: {script_path}")
        print("💡 Запустите: ./agent_safe_commands.sh")
    except Exception as e:
        print(f"❌ Ошибка создания скрипта: {e}")

def provide_agent_solutions():
    """Предоставляет решения для проблем с агентом"""
    print_header("РЕШЕНИЯ ДЛЯ ПРОБЛЕМ С АГЕНТОМ")
    
    solutions = [
        {
            "problem": "Агент зависает после выполнения команд",
            "causes": [
                "Команда не завершается (бесконечный цикл)",
                "Команда ждет ввода от пользователя (input())",
                "Команда читает stdin до EOF",
                "Проблемы с буферизацией вывода",
                "Команда выполняется слишком долго"
            ],
            "solutions": [
                "1. Добавляйте timeout для команд: `timeout 10 your_command`",
                "2. Избегайте интерактивных команд (input(), raw_input())",
                "3. Используйте `sys.stdout.flush()` для принудительного вывода",
                "4. Проверяйте, что команда завершается корректно",
                "5. Используйте `subprocess.run()` с timeout в Python скриптах"
            ]
        },
        {
            "problem": "Агент не получает вывод команд",
            "causes": [
                "Буферизация вывода Python",
                "Вывод идет в stderr вместо stdout",
                "Команда не выводит ничего",
                "Проблемы с кодировкой"
            ],
            "solutions": [
                "1. Используйте `-u` флаг для Python: `py -u script.py`",
                "2. Добавляйте `sys.stdout.flush()` после print()",
                "3. Проверяйте и stderr, и stdout",
                "4. Устанавливайте правильную кодировку: `PYTHONIOENCODING=utf-8`"
            ]
        },
        {
            "problem": "Агент ждет завершения длительных команд",
            "causes": [
                "Команда выполняется очень долго",
                "Команда обрабатывает большие файлы",
                "Сетевые операции без таймаута",
                "Команда зависает на I/O операциях"
            ],
            "solutions": [
                "1. Всегда добавляйте разумный timeout",
                "2. Разбивайте длительные операции на части",
                "3. Используйте прогресс-бары для длительных операций",
                "4. Запускайте длительные команды в фоне с логированием"
            ]
        }
    ]
    
    for i, solution in enumerate(solutions, 1):
        print(f"\n🔧 Проблема {i}: {solution['problem']}")
        print("📋 Возможные причины:")
        for cause in solution['causes']:
            print(f"   • {cause}")
        print("✅ Решения:")
        for sol in solution['solutions']:
            print(f"   {sol}")

def create_agent_best_practices():
    """Создает руководство по лучшим практикам для агента"""
    print_header("ЛУЧШИЕ ПРАКТИКИ ДЛЯ АГЕНТА")
    
    practices = {
        "Безопасные команды": [
            "py -c \"print('Hello')\"",
            "py -c \"import sys; print('Start'); sys.stdout.flush(); print('End')\"",
            "timeout 10 py script.py",
            "py -u script.py  # -u для unbuffered output"
        ],
        "Опасные команды (избегать)": [
            "py -c \"input('Enter: ')\"  # Ждет ввода",
            "py -c \"while True: pass\"  # Бесконечный цикл",
            "py -c \"sys.stdin.read()\"  # Читает до EOF",
            "py script.py  # Без timeout для длительных скриптов"
        ],
        "Проверка завершения": [
            "Всегда проверяйте return code команды",
            "Используйте timeout для всех команд",
            "Проверяйте и stdout, и stderr",
            "Логируйте результаты выполнения"
        ],
        "Обработка ошибок": [
            "Обрабатывайте TimeoutExpired исключения",
            "Проверяйте кодировку вывода",
            "Используйте errors='replace' для subprocess",
            "Логируйте все ошибки выполнения"
        ]
    }
    
    for category, items in practices.items():
        print(f"\n📋 {category}:")
        for item in items:
            print(f"   • {item}")
    
    # Создаем файл с лучшими практиками
    practices_content = '''# Лучшие практики для агента Cursor

## ✅ Безопасные команды

### Простые команды с выводом
```bash
py -c "print('Hello from Python')"
py -c "import sys; print('Start'); sys.stdout.flush(); print('End')"
```

### Команды с таймаутом
```bash
timeout 10 py script.py
timeout 30 py -c "import time; time.sleep(5); print('Done')"
```

### Команды с unbuffered output
```bash
py -u script.py  # -u флаг для немедленного вывода
```

## ❌ Опасные команды (избегать)

### Интерактивные команды
```bash
py -c "input('Enter something: ')"  # Ждет ввода
py -c "raw_input('Enter: ')"        # Ждет ввода (Python 2)
```

### Бесконечные циклы
```bash
py -c "while True: pass"            # Никогда не завершится
py -c "while True: print('loop')"   # Бесконечный вывод
```

### Команды чтения stdin
```bash
py -c "sys.stdin.read()"            # Ждет закрытия stdin
py -c "input()"                     # Ждет ввода
```

## 🔧 Рекомендации

1. **Всегда используйте timeout** для команд
2. **Проверяйте return code** после выполнения
3. **Используйте sys.stdout.flush()** для принудительного вывода
4. **Обрабатывайте исключения** TimeoutExpired
5. **Логируйте результаты** выполнения команд
6. **Проверяйте и stdout, и stderr**

## 🐍 Пример безопасного выполнения

```python
import subprocess
import sys

def run_command_safe(command, timeout=10):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)
```
'''
    
    practices_path = Path.cwd() / "AGENT_BEST_PRACTICES.md"
    try:
        with open(practices_path, 'w', encoding='utf-8') as f:
            f.write(practices_content)
        print(f"\n✅ Создано руководство: {practices_path}")
    except Exception as e:
        print(f"❌ Ошибка создания руководства: {e}")

def main():
    """Основная функция диагностики"""
    print("🤖 ДИАГНОСТИКА ПРОБЛЕМ С АГЕНТОМ CURSOR")
    print("Проблема: Агент не продолжает работу после выполнения команд в терминале")
    print("Цель: Найти и исправить причины зависания агента")
    
    try:
        test_command_completion()
        test_interactive_commands()
        test_output_buffering()
        create_agent_safe_commands()
        provide_agent_solutions()
        create_agent_best_practices()
        
        print_header("ЗАКЛЮЧЕНИЕ")
        print("✅ Диагностика завершена!")
        print("📋 Основные причины зависания агента:")
        print("   • Команды не завершаются (бесконечные циклы)")
        print("   • Интерактивные команды (input(), stdin.read())")
        print("   • Проблемы с буферизацией вывода")
        print("   • Отсутствие timeout для команд")
        print("\n💡 Рекомендации:")
        print("   1. Всегда добавляйте timeout для команд")
        print("   2. Избегайте интерактивных команд")
        print("   3. Используйте sys.stdout.flush() для вывода")
        print("   4. Проверяйте завершение команд")
        print("   5. Обрабатывайте исключения TimeoutExpired")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Диагностика прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка диагностики: {e}")

if __name__ == "__main__":
    main()

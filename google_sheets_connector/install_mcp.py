"""
Установка MCP зависимостей для Google Sheets сервера
"""

import subprocess
import sys
import os

def install_mcp_dependencies():
    """Устанавливает MCP зависимости"""
    print("🔧 Установка MCP зависимостей для Google Sheets сервера")
    print("=" * 60)
    
    # MCP пакеты для установки
    mcp_packages = [
        "mcp>=1.0.0",
        "asyncio",
    ]
    
    # Проверяем наличие pip
    try:
        import pip
        print("✅ pip найден")
    except ImportError:
        print("❌ pip не найден")
        return False
    
    # Устанавливаем пакеты
    for package in mcp_packages:
        print(f"\n📦 Установка {package}...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {package} установлен успешно")
            else:
                print(f"❌ Ошибка установки {package}: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка установки {package}: {e}")
            return False
    
    return True

def verify_installation():
    """Проверяет корректность установки"""
    print("\n🔍 Проверка установки...")
    
    try:
        import mcp
        print("✅ MCP библиотека успешно импортирована")
        print(f"📋 Версия MCP: {getattr(mcp, '__version__', 'неизвестна')}")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта MCP: {e}")
        print("💡 Попробуйте установить MCP вручную:")
        print("   pip install mcp")
        return False

def test_mcp_server():
    """Тестирует MCP сервер"""
    print("\n🚀 Тестирование MCP сервера...")
    
    # Проверяем наличие всех необходимых файлов
    required_files = [
        "mcp_server.py",
        "connector.py", 
        "priorities_manager.py",
        "credentials/quickstart-1591698112539-676a9e339335.json"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Отсутствуют необходимые файлы:")
        for file in missing_files:
            print(f"   • {file}")
        return False
    
    print("✅ Все необходимые файлы найдены")
    
    # Проверяем импорт основных модулей
    try:
        from connector import GoogleSheetsConnector
        print("✅ GoogleSheetsConnector импортирован")
        
        from priorities_manager import PrioritiesManager
        print("✅ PrioritiesManager импортирован")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def create_startup_script():
    """Создает скрипт для запуска MCP сервера"""
    print("\n📝 Создание скрипта запуска...")
    
    startup_script = """#!/usr/bin/env python3
\"\"\"
Скрипт запуска Google Sheets MCP сервера
\"\"\"

import sys
import os
import asyncio

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mcp_server import main
    
    if __name__ == "__main__":
        print("🚀 Запуск Google Sheets MCP сервера...")
        print("📊 Доступные инструменты:")
        print("   • authenticate - аутентификация")
        print("   • get_spreadsheet_info - информация о таблице")
        print("   • read_range - чтение данных")
        print("   • write_range - запись данных")
        print("   • create_sheet - создание листа")
        print("   • analyze_priorities_table - анализ приоритетов")
        print("   • create_dashboard - создание дашборда")
        print("   • search_projects - поиск проектов")
        print()
        print("🔧 Для остановки используйте Ctrl+C")
        print("=" * 50)
        
        asyncio.run(main())
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("💡 Установите зависимости: python install_mcp.py")
    sys.exit(1)
except KeyboardInterrupt:
    print("\\n👋 MCP сервер остановлен")
    sys.exit(0)
except Exception as e:
    print(f"❌ Ошибка запуска: {e}")
    sys.exit(1)
"""

    with open("start_mcp_server.py", "w", encoding="utf-8") as f:
        f.write(startup_script)
    
    print("✅ Скрипт запуска создан: start_mcp_server.py")
    
    # Делаем скрипт исполняемым (на Unix системах)
    try:
        os.chmod("start_mcp_server.py", 0o755)
    except:
        pass  # На Windows это не работает

def create_usage_guide():
    """Создает руководство по использованию"""
    print("\n📚 Создание руководства по использованию...")
    
    guide = """# Google Sheets MCP Server - Руководство по использованию

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
python install_mcp.py
```

### 2. Настройка credentials
        Убедитесь, что файл `credentials/quickstart-1591698112539-676a9e339335.json` содержит корректные данные Service Account.

### 3. Запуск сервера
```bash
python start_mcp_server.py
```

## 📊 Доступные инструменты

### 🔐 authenticate
Аутентификация в Google Sheets API
```json
{
  "name": "authenticate",
  "arguments": {
            "credentials_file": "credentials/quickstart-1591698112539-676a9e339335.json"
  }
}
```

### 📊 get_spreadsheet_info
Получение информации о таблице
```json
{
  "name": "get_spreadsheet_info", 
  "arguments": {
    "spreadsheet_id": "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
  }
}
```

### 📖 read_range
Чтение данных из диапазона
```json
{
  "name": "read_range",
  "arguments": {
    "spreadsheet_id": "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE",
    "range": "Лист1!A1:C10"
  }
}
```

### ✍️ write_range
Запись данных в диапазон
```json
{
  "name": "write_range",
  "arguments": {
    "spreadsheet_id": "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE",
    "range": "NewData!A1",
    "values": [["Заголовок1", "Заголовок2"], ["Данные1", "Данные2"]]
  }
}
```

### 🎯 analyze_priorities_table
Анализ таблицы приоритетов
```json
{
  "name": "analyze_priorities_table",
  "arguments": {
    "analysis_type": "status_report"
  }
}
```

### 🔍 search_projects
Поиск проектов
```json
{
  "name": "search_projects",
  "arguments": {
    "query": "Иллан",
    "filter_by": "all"
  }
}
```

## 🔧 Конфигурация для Claude Desktop

Добавьте в файл конфигурации Claude Desktop:

```json
{
  "mcpServers": {
    "google-sheets": {
      "command": "python",
      "args": ["start_mcp_server.py"],
      "cwd": "/path/to/your/google_sheets_connector"
    }
  }
}
```

## 🛠️ Диагностика проблем

### Проблема с аутентификацией
1. Проверьте корректность `credentials/quickstart-1591698112539-676a9e339335.json`
2. Убедитесь, что Service Account имеет доступ к таблице
3. Проверьте включение Google Sheets API в проекте

### Проблема с подключением
1. Проверьте ID таблицы
2. Убедитесь в наличии интернет-соединения
3. Проверьте права доступа к таблице

### Проблема с данными
1. Проверьте корректность диапазонов
2. Убедитесь в существовании указанных листов
3. Проверьте формат передаваемых данных

## 📋 Логи и отладка

Сервер выводит подробные логи о всех операциях. При возникновении ошибок обратите внимание на:
- Сообщения об ошибках аутентификации
- Ошибки доступа к таблицам (403, 404)
- Проблемы с форматом данных
- Сетевые ошибки

## 🔗 Полезные ссылки

- [Google Sheets API документация](https://developers.google.com/sheets/api)
- [Google Cloud Console](https://console.cloud.google.com/)
- [MCP Protocol](https://modelcontextprotocol.io/)
"""

    with open("MCP_USAGE_GUIDE.md", "w", encoding="utf-8") as f:
        f.write(guide)
    
    print("✅ Руководство создано: MCP_USAGE_GUIDE.md")

def main():
    """Главная функция установки"""
    print("🚀 УСТАНОВКА GOOGLE SHEETS MCP СЕРВЕРА")
    print("=" * 60)
    
    # Устанавливаем зависимости
    if not install_mcp_dependencies():
        print("\n❌ Ошибка установки зависимостей")
        return False
    
    # Проверяем установку
    if not verify_installation():
        print("\n❌ Ошибка проверки установки")
        return False
    
    # Тестируем сервер
    if not test_mcp_server():
        print("\n❌ Ошибка тестирования сервера")
        return False
    
    # Создаем вспомогательные файлы
    create_startup_script()
    create_usage_guide()
    
    print("\n🎉 УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!")
    print("=" * 60)
    print("🚀 Для запуска сервера выполните:")
    print("   python start_mcp_server.py")
    print()
    print("📚 Руководство по использованию:")
    print("   MCP_USAGE_GUIDE.md")
    print()
    print("🔧 Конфигурация для Claude Desktop:")
    print("   mcp_config.json")
    
    return True

if __name__ == "__main__":
    main()

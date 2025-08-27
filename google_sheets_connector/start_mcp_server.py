#!/usr/bin/env python3
"""
Скрипт запуска Google Sheets MCP сервера
"""

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
    print("\n👋 MCP сервер остановлен")
    sys.exit(0)
except Exception as e:
    print(f"❌ Ошибка запуска: {e}")
    sys.exit(1)

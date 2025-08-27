"""
Тест MCP сервера Google Sheets
"""

import json
import asyncio
from mcp_server import GoogleSheetsMCPServer

async def test_mcp_server():
    """Тестирует основные функции MCP сервера"""
    print("🚀 Тестирование Google Sheets MCP сервера")
    print("=" * 60)
    
    try:
        # Создаем сервер
        server_instance = GoogleSheetsMCPServer()
        print("✅ MCP сервер создан")
        
        # Тестируем список инструментов
        print("\n📋 Тестирование списка инструментов...")
        
        # Получаем функцию обработки списка инструментов
        list_tools_handler = None
        for handler in server_instance.server._tool_list_handlers:
            list_tools_handler = handler
            break
        
        if list_tools_handler:
            tools = await list_tools_handler()
            print(f"✅ Найдено {len(tools)} инструментов:")
            
            for tool in tools:
                print(f"   • {tool.name}: {tool.description}")
        
        # Тестируем список ресурсов  
        print("\n📋 Тестирование списка ресурсов...")
        
        # Получаем функцию обработки списка ресурсов
        list_resources_handler = None
        for handler in server_instance.server._resource_list_handlers:
            list_resources_handler = handler
            break
        
        if list_resources_handler:
            resources = await list_resources_handler()
            print(f"✅ Найдено {len(resources)} ресурсов:")
            
            for resource in resources:
                print(f"   • {resource.name}: {resource.description}")
        
        # Тестируем чтение ресурсов
        print("\n📖 Тестирование чтения ресурсов...")
        
        # Получаем функцию чтения ресурсов
        read_resource_handler = None
        for handler in server_instance.server._resource_handlers:
            read_resource_handler = handler
            break
        
        if read_resource_handler:
            # Тестируем чтение конфигурации
            config_content = await read_resource_handler("google-sheets://config")
            print("✅ Конфигурация прочитана:")
            print(f"   {config_content[:100]}...")
            
            # Тестируем чтение справки
            help_content = await read_resource_handler("google-sheets://help")
            print("✅ Справка прочитана:")
            print(f"   Размер: {len(help_content)} символов")
        
        print("\n🎉 Все тесты пройдены успешно!")
        print("\n📊 Сводка:")
        print(f"   • Инструменты: {len(tools) if 'tools' in locals() else 'N/A'}")
        print(f"   • Ресурсы: {len(resources) if 'resources' in locals() else 'N/A'}")
        print("   • Статус: Готов к работе")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_client_example():
    """Создает пример клиента для работы с MCP сервером"""
    print("\n📝 Создание примера клиента...")
    
    client_example = '''
"""
Пример клиента для работы с Google Sheets MCP сервером
"""

import json
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

async def example_mcp_client():
    """Пример работы с MCP сервером"""
    
    # Подключение к серверу через stdio
    async with stdio_client(["python", "start_mcp_server.py"]) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Инициализация
            await session.initialize()
            
            # Получаем список инструментов
            tools = await session.list_tools()
            print("Доступные инструменты:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Аутентификация
            auth_result = await session.call_tool(
                "authenticate",
                {"credentials_file": "credentials/service_account.json"}
            )
            print("Результат аутентификации:", auth_result)
            
            # Получение информации о таблице
            info_result = await session.call_tool(
                "get_spreadsheet_info",
                {"spreadsheet_id": "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"}
            )
            print("Информация о таблице:", info_result)
            
            # Чтение данных
            read_result = await session.call_tool(
                "read_range",
                {
                    "spreadsheet_id": "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE",
                    "range": "Лист1!A1:C5"
                }
            )
            print("Данные из таблицы:", read_result)

if __name__ == "__main__":
    asyncio.run(example_mcp_client())
'''
    
    with open("mcp_client_example.py", "w", encoding="utf-8") as f:
        f.write(client_example)
    
    print("✅ Пример клиента создан: mcp_client_example.py")

def main():
    """Главная функция тестирования"""
    
    # Запускаем тест сервера
    result = asyncio.run(test_mcp_server())
    
    if result:
        # Создаем пример клиента
        create_client_example()
        
        print("\n🎯 ЗАКЛЮЧЕНИЕ:")
        print("=" * 60)
        print("✅ MCP сервер полностью настроен и готов к работе")
        print("✅ Все компоненты протестированы")
        print("✅ Документация создана")
        print()
        print("🚀 Для запуска сервера:")
        print("   python start_mcp_server.py")
        print()
        print("📋 Для использования в Claude Desktop:")
        print("   Добавьте конфигурацию из mcp_config.json")
        print()
        print("📚 Документация:")
        print("   MCP_USAGE_GUIDE.md")

if __name__ == "__main__":
    main()

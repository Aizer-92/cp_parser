"""
MCP Server для Google Sheets
Реализует Model Context Protocol для работы с Google Sheets
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
import traceback

# MCP зависимости
try:
    from mcp.server import Server
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel
    )
except ImportError:
    print("❌ MCP библиотеки не установлены")
    print("💡 Установите: pip install mcp")
    exit(1)

# Наш коннектор
from connector import GoogleSheetsConnector
from priorities_manager import PrioritiesManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-google-sheets")

class GoogleSheetsMCPServer:
    """MCP сервер для Google Sheets"""
    
    def __init__(self):
        self.server = Server("google-sheets-mcp")
        self.connector = GoogleSheetsConnector()
        self.priorities_manager = None
        self.authenticated = False
        
        # Регистрируем инструменты
        self._register_tools()
        
        # Регистрируем ресурсы
        self._register_resources()
    
    def _register_tools(self):
        """Регистрирует доступные инструменты"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Список доступных инструментов"""
            return [
                Tool(
                    name="authenticate",
                    description="Аутентификация в Google Sheets API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "credentials_file": {
                                "type": "string",
                                "description": "Путь к файлу Service Account JSON",
                                "default": "credentials/service_account.json"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_spreadsheet_info",
                    description="Получить информацию о таблице",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "ID Google Sheets таблицы"
                            }
                        },
                        "required": ["spreadsheet_id"]
                    }
                ),
                Tool(
                    name="read_range",
                    description="Прочитать данные из диапазона ячеек",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "ID Google Sheets таблицы"
                            },
                            "range": {
                                "type": "string",
                                "description": "Диапазон ячеек (например: Sheet1!A1:C10)"
                            },
                            "value_render_option": {
                                "type": "string",
                                "description": "Опция отображения значений",
                                "enum": ["FORMATTED_VALUE", "UNFORMATTED_VALUE", "FORMULA"],
                                "default": "FORMATTED_VALUE"
                            }
                        },
                        "required": ["spreadsheet_id", "range"]
                    }
                ),
                Tool(
                    name="write_range",
                    description="Записать данные в диапазон ячеек",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "ID Google Sheets таблицы"
                            },
                            "range": {
                                "type": "string",
                                "description": "Диапазон ячеек для записи"
                            },
                            "values": {
                                "type": "array",
                                "description": "Данные для записи (массив массивов)",
                                "items": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                }
                            },
                            "value_input_option": {
                                "type": "string",
                                "description": "Как интерпретировать данные",
                                "enum": ["RAW", "USER_ENTERED"],
                                "default": "USER_ENTERED"
                            }
                        },
                        "required": ["spreadsheet_id", "range", "values"]
                    }
                ),
                Tool(
                    name="create_sheet",
                    description="Создать новый лист в таблице",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "ID Google Sheets таблицы"
                            },
                            "sheet_title": {
                                "type": "string",
                                "description": "Название нового листа"
                            },
                            "rows": {
                                "type": "integer",
                                "description": "Количество строк",
                                "default": 1000
                            },
                            "columns": {
                                "type": "integer",
                                "description": "Количество колонок",
                                "default": 26
                            }
                        },
                        "required": ["spreadsheet_id", "sheet_title"]
                    }
                ),
                Tool(
                    name="analyze_priorities_table",
                    description="Анализ таблицы приоритетов проектов",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "ID таблицы приоритетов",
                                "default": "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE"
                            },
                            "analysis_type": {
                                "type": "string",
                                "description": "Тип анализа",
                                "enum": ["status_report", "workload", "financial", "dashboard"],
                                "default": "status_report"
                            }
                        }
                    }
                ),
                Tool(
                    name="create_dashboard",
                    description="Создать дашборд в таблице",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "spreadsheet_id": {
                                "type": "string",
                                "description": "ID Google Sheets таблицы"
                            },
                            "dashboard_type": {
                                "type": "string",
                                "description": "Тип дашборда",
                                "enum": ["priorities", "financial", "general"],
                                "default": "general"
                            }
                        },
                        "required": ["spreadsheet_id"]
                    }
                ),
                Tool(
                    name="search_projects",
                    description="Поиск проектов в таблице приоритетов",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Поисковый запрос"
                            },
                            "filter_by": {
                                "type": "string",
                                "description": "Фильтр по полю",
                                "enum": ["status", "executor", "client_grade", "all"],
                                "default": "all"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Обработка вызовов инструментов"""
            try:
                if name == "authenticate":
                    return await self._authenticate(arguments)
                elif name == "get_spreadsheet_info":
                    return await self._get_spreadsheet_info(arguments)
                elif name == "read_range":
                    return await self._read_range(arguments)
                elif name == "write_range":
                    return await self._write_range(arguments)
                elif name == "create_sheet":
                    return await self._create_sheet(arguments)
                elif name == "analyze_priorities_table":
                    return await self._analyze_priorities_table(arguments)
                elif name == "create_dashboard":
                    return await self._create_dashboard(arguments)
                elif name == "search_projects":
                    return await self._search_projects(arguments)
                else:
                    return [TextContent(type="text", text=f"❌ Неизвестный инструмент: {name}")]
                    
            except Exception as e:
                error_msg = f"❌ Ошибка выполнения {name}: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                return [TextContent(type="text", text=error_msg)]
    
    def _register_resources(self):
        """Регистрирует доступные ресурсы"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """Список доступных ресурсов"""
            return [
                Resource(
                    uri="google-sheets://config",
                    name="Google Sheets Configuration",
                    description="Конфигурация подключения к Google Sheets",
                    mimeType="application/json"
                ),
                Resource(
                    uri="google-sheets://priorities-table",
                    name="Priorities Table",
                    description="Таблица приоритетов проектов",
                    mimeType="application/json"
                ),
                Resource(
                    uri="google-sheets://help",
                    name="Google Sheets MCP Help",
                    description="Справка по использованию MCP сервера",
                    mimeType="text/markdown"
                )
            ]
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Чтение ресурсов"""
            if uri == "google-sheets://config":
                config = self.connector.config
                return json.dumps(config, indent=2, ensure_ascii=False)
            
            elif uri == "google-sheets://priorities-table":
                if not self.authenticated:
                    return json.dumps({"error": "Требуется аутентификация"})
                
                try:
                    if not self.priorities_manager:
                        self.priorities_manager = PrioritiesManager()
                        self.priorities_manager.connector = self.connector
                    
                    df = self.priorities_manager.get_all_projects()
                    if df.empty:
                        return json.dumps({"error": "Нет данных"})
                    
                    return df.head(10).to_json(orient="records", force_ascii=False, indent=2)
                except Exception as e:
                    return json.dumps({"error": str(e)})
            
            elif uri == "google-sheets://help":
                return self._get_help_content()
            
            else:
                return f"❌ Неизвестный ресурс: {uri}"
    
    async def _authenticate(self, args: Dict[str, Any]) -> List[TextContent]:
        """Аутентификация"""
        credentials_file = args.get("credentials_file", "credentials/service_account.json")
        
        try:
            success = self.connector.authenticate_service_account(credentials_file)
            if success:
                self.authenticated = True
                return [TextContent(type="text", text="✅ Аутентификация успешна")]
            else:
                return [TextContent(type="text", text="❌ Ошибка аутентификации")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка аутентификации: {e}")]
    
    async def _get_spreadsheet_info(self, args: Dict[str, Any]) -> List[TextContent]:
        """Получение информации о таблице"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        spreadsheet_id = args["spreadsheet_id"]
        
        try:
            info = self.connector.get_spreadsheet_info(spreadsheet_id)
            result = json.dumps(info, indent=2, ensure_ascii=False)
            return [TextContent(type="text", text=f"📊 Информация о таблице:\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка получения информации: {e}")]
    
    async def _read_range(self, args: Dict[str, Any]) -> List[TextContent]:
        """Чтение данных"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        spreadsheet_id = args["spreadsheet_id"]
        range_name = args["range"]
        value_render_option = args.get("value_render_option", "FORMATTED_VALUE")
        
        try:
            data = self.connector.read_range(spreadsheet_id, range_name, value_render_option)
            result = json.dumps(data, indent=2, ensure_ascii=False)
            return [TextContent(type="text", text=f"📖 Данные из {range_name}:\n{result}")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка чтения данных: {e}")]
    
    async def _write_range(self, args: Dict[str, Any]) -> List[TextContent]:
        """Запись данных"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        spreadsheet_id = args["spreadsheet_id"]
        range_name = args["range"]
        values = args["values"]
        value_input_option = args.get("value_input_option", "USER_ENTERED")
        
        try:
            success = self.connector.write_range(spreadsheet_id, range_name, values, value_input_option)
            if success:
                return [TextContent(type="text", text=f"✅ Данные записаны в {range_name}")]
            else:
                return [TextContent(type="text", text="❌ Ошибка записи данных")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка записи данных: {e}")]
    
    async def _create_sheet(self, args: Dict[str, Any]) -> List[TextContent]:
        """Создание листа"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        spreadsheet_id = args["spreadsheet_id"]
        sheet_title = args["sheet_title"]
        rows = args.get("rows", 1000)
        columns = args.get("columns", 26)
        
        try:
            sheet_id = self.connector.create_sheet(spreadsheet_id, sheet_title, rows, columns)
            if sheet_id:
                return [TextContent(type="text", text=f"✅ Лист '{sheet_title}' создан с ID {sheet_id}")]
            else:
                return [TextContent(type="text", text="❌ Ошибка создания листа")]
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка создания листа: {e}")]
    
    async def _analyze_priorities_table(self, args: Dict[str, Any]) -> List[TextContent]:
        """Анализ таблицы приоритетов"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        spreadsheet_id = args.get("spreadsheet_id", "1Xxx_cNb5eOi0CzRhr1X3mWwYWyltmZu_uI_02B9EfcE")
        analysis_type = args.get("analysis_type", "status_report")
        
        try:
            if not self.priorities_manager:
                self.priorities_manager = PrioritiesManager(spreadsheet_id)
                self.priorities_manager.connector = self.connector
            
            if analysis_type == "status_report":
                report = self.priorities_manager.generate_status_report()
                return [TextContent(type="text", text=report)]
            
            elif analysis_type == "workload":
                workload = self.priorities_manager.analyze_workload()
                result = json.dumps(workload, indent=2, ensure_ascii=False)
                return [TextContent(type="text", text=f"👥 Анализ нагрузки:\n{result}")]
            
            elif analysis_type == "financial":
                finance = self.priorities_manager.analyze_financial_metrics()
                result = json.dumps(finance, indent=2, ensure_ascii=False)
                return [TextContent(type="text", text=f"💰 Финансовые показатели:\n{result}")]
            
            elif analysis_type == "dashboard":
                success = self.priorities_manager.create_dashboard()
                if success:
                    return [TextContent(type="text", text="✅ Дашборд создан успешно")]
                else:
                    return [TextContent(type="text", text="❌ Ошибка создания дашборда")]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка анализа: {e}")]
    
    async def _create_dashboard(self, args: Dict[str, Any]) -> List[TextContent]:
        """Создание дашборда"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        spreadsheet_id = args["spreadsheet_id"]
        dashboard_type = args.get("dashboard_type", "general")
        
        try:
            # Здесь можно реализовать разные типы дашбордов
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            dashboard_data = [
                [f"📊 {dashboard_type.upper()} DASHBOARD", f"Создано: {current_time}"],
                ["", ""],
                ["Тип дашборда", dashboard_type],
                ["Статус", "Активен"]
            ]
            
            # Создаем лист дашборда
            sheet_title = f"Dashboard_{dashboard_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            sheet_id = self.connector.create_sheet(spreadsheet_id, sheet_title)
            
            if sheet_id:
                # Записываем данные дашборда
                success = self.connector.write_range(spreadsheet_id, f"{sheet_title}!A1", dashboard_data)
                if success:
                    return [TextContent(type="text", text=f"✅ Дашборд '{sheet_title}' создан успешно")]
                else:
                    return [TextContent(type="text", text="❌ Ошибка записи данных дашборда")]
            else:
                return [TextContent(type="text", text="❌ Ошибка создания листа дашборда")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка создания дашборда: {e}")]
    
    async def _search_projects(self, args: Dict[str, Any]) -> List[TextContent]:
        """Поиск проектов"""
        if not self.authenticated:
            return [TextContent(type="text", text="❌ Требуется аутентификация")]
        
        query = args["query"]
        filter_by = args.get("filter_by", "all")
        
        try:
            if not self.priorities_manager:
                self.priorities_manager = PrioritiesManager()
                self.priorities_manager.connector = self.connector
            
            df = self.priorities_manager.get_all_projects()
            if df.empty:
                return [TextContent(type="text", text="❌ Нет данных для поиска")]
            
            # Выполняем поиск
            if filter_by == "status":
                results = df[df['Статус'].str.contains(query, case=False, na=False)]
            elif filter_by == "executor":
                results = df[df['Исполнители'].str.contains(query, case=False, na=False)]
            elif filter_by == "client_grade":
                results = df[df['Грейд клиента'].astype(str).str.contains(query, case=False, na=False)]
            else:  # all
                mask = df.astype(str).apply(lambda x: x.str.contains(query, case=False, na=False)).any(axis=1)
                results = df[mask]
            
            if results.empty:
                return [TextContent(type="text", text=f"🔍 Проекты по запросу '{query}' не найдены")]
            
            # Форматируем результаты
            result_text = f"🔍 Найдено {len(results)} проектов по запросу '{query}':\n\n"
            
            for idx, (_, row) in enumerate(results.head(10).iterrows(), 1):
                result_text += f"{idx}. {row['Название'][:60]}...\n"
                result_text += f"   Статус: {row['Статус']}\n"
                result_text += f"   Исполнители: {str(row['Исполнители'])[:50]}...\n\n"
            
            if len(results) > 10:
                result_text += f"... и еще {len(results) - 10} проектов"
            
            return [TextContent(type="text", text=result_text)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"❌ Ошибка поиска: {e}")]
    
    def _get_help_content(self) -> str:
        """Содержимое справки"""
        return """# Google Sheets MCP Server

## Доступные инструменты:

### 🔐 authenticate
Аутентификация в Google Sheets API
- `credentials_file` - путь к Service Account JSON файлу

### 📊 get_spreadsheet_info
Получить информацию о таблице
- `spreadsheet_id` - ID Google Sheets таблицы

### 📖 read_range
Прочитать данные из диапазона ячеек
- `spreadsheet_id` - ID таблицы
- `range` - диапазон (например: Sheet1!A1:C10)
- `value_render_option` - опция отображения

### ✍️ write_range
Записать данные в диапазон ячеек
- `spreadsheet_id` - ID таблицы
- `range` - диапазон для записи
- `values` - данные (массив массивов)

### 📋 create_sheet
Создать новый лист в таблице
- `spreadsheet_id` - ID таблицы
- `sheet_title` - название листа
- `rows` - количество строк
- `columns` - количество колонок

### 🎯 analyze_priorities_table
Анализ таблицы приоритетов проектов
- `spreadsheet_id` - ID таблицы приоритетов
- `analysis_type` - тип анализа (status_report, workload, financial, dashboard)

### 📊 create_dashboard
Создать дашборд в таблице
- `spreadsheet_id` - ID таблицы
- `dashboard_type` - тип дашборда

### 🔍 search_projects
Поиск проектов в таблице приоритетов
- `query` - поисковый запрос
- `filter_by` - фильтр по полю

## Доступные ресурсы:

- `google-sheets://config` - конфигурация
- `google-sheets://priorities-table` - данные таблицы приоритетов
- `google-sheets://help` - эта справка

## Пример использования:

1. Сначала выполните аутентификацию:
   ```
   authenticate(credentials_file="credentials/service_account.json")
   ```

2. Получите информацию о таблице:
   ```
   get_spreadsheet_info(spreadsheet_id="your_sheet_id")
   ```

3. Прочитайте данные:
   ```
   read_range(spreadsheet_id="your_sheet_id", range="Sheet1!A1:C10")
   ```
"""

async def main():
    """Главная функция сервера"""
    # Создаем MCP сервер
    google_sheets_server = GoogleSheetsMCPServer()
    
    # Запускаем сервер через stdio
    async with stdio_server() as (read_stream, write_stream):
        await google_sheets_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="google-sheets-mcp",
                server_version="1.0.0",
                capabilities=google_sheets_server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())

# Google Sheets MCP Server - Руководство по использованию

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
python install_mcp.py
```

### 2. Настройка credentials
Убедитесь, что файл `credentials/service_account.json` содержит корректные данные Service Account.

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
    "credentials_file": "credentials/service_account.json"
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
1. Проверьте корректность `credentials/service_account.json`
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

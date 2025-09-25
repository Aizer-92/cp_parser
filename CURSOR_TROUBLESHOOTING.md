# 🔧 Troubleshooting Cursor MCP

## Если команда "Покажи список всех сотрудников в Planfix" не работает:

### 1. ✅ Проверьте настройки MCP в Cursor:
- Cmd+, → MCP Servers
- Должен быть виден сервер "planfix" 
- Статус должен быть зеленый

### 2. ✅ Проверьте конфигурацию:
Убедитесь что в `.cursor/mcp.json` есть:
```json
{
  "mcpServers": {
    "planfix": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/Aizer-92/planfix-mcp-server@main",
        "planfix-server",
        "--account", "megamindru", 
        "--api-key", "ae717f1bb8e41ab5e586dc1b2781240a"
      ]
    }
  }
}
```

### 3. ✅ Альтернативные команды для тестирования:
```
"Найди задачи в Planfix"
"Покажи проекты в Planfix" 
"Получи контакты из Planfix"
"Создай задачу в Planfix с названием 'Тест MCP'"
```

### 4. ✅ Если MCP не видит инструменты:
1. Полностью закрыть Cursor (Cmd+Q)
2. Перезапустить Cursor
3. Подождать 10-15 секунд для инициализации
4. Попробовать еще раз

### 5. ✅ Проверить логи Cursor:
- Cmd+Shift+I → Console
- Искать ошибки MCP или planfix

## 🎯 Ожидаемый результат команды:

Должен появиться список сотрудников примерно так:
```
Список сотрудников в Planfix:

1. Иванов Иван (ID: 123, Email: ivan@company.com)
2. Петрова Мария (ID: 124, Email: maria@company.com)
3. Сидоров Петр (ID: 125, Email: petr@company.com)
...
```

## 🆘 Если ничего не работает:
Напишите "MCP не работает" и я дам дополнительные инструкции по диагностике.


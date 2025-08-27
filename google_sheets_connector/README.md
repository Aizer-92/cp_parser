# Google Sheets Connector

Универсальный коннектор для работы с Google Sheets через Python API.

## Возможности

- ✅ Аутентификация через Service Account
- ✅ Чтение данных из таблиц
- ✅ Запись данных в таблицы
- ✅ Обновление существующих данных
- ✅ Создание новых листов
- ✅ Форматирование ячеек
- ✅ Работа с формулами
- ✅ Экспорт данных в разные форматы

## Структура проекта

```
google_sheets_connector/
├── connector.py         # Основной класс коннектора
├── auth.py             # Модуль аутентификации
├── examples/           # Примеры использования
├── utils/              # Утилиты для интеграции
├── credentials/        # Ключи доступа (не в git)
├── requirements.txt    # Зависимости
└── README.md          # Документация
```

## Быстрый старт

1. Установите зависимости: `pip install -r requirements.txt`
2. Настройте Google API credentials
3. Используйте connector.py для работы с таблицами

## Примеры использования

### Чтение данных
```python
from connector import GoogleSheetsConnector

# Подключение
sheets = GoogleSheetsConnector()
sheets.authenticate('path/to/credentials.json')

# Чтение данных
data = sheets.read_range('spreadsheet_id', 'Sheet1!A1:C10')
```

### Запись данных
```python
# Запись данных
data = [['Имя', 'Возраст', 'Город'], ['Иван', 25, 'Москва']]
sheets.write_range('spreadsheet_id', 'Sheet1!A1', data)
```

### Интеграция с Health данными
```python
from utils.health_integration import HealthSheetsSync

# Синхронизация медицинских данных
health_sync = HealthSheetsSync()
health_sync.sync_analysis_reports()
```

## Конфигурация

Создайте файл `config.json` для настройки таблиц:
```json
{
  "health_tracking": "spreadsheet_id_1",
  "finance_tracking": "spreadsheet_id_2",
  "learning_progress": "spreadsheet_id_3"
}
```

## Безопасность

- Все credentials хранятся локально
- Поддержка Service Account для автоматизации
- Валидация данных перед отправкой
- Логирование всех операций

# Скрипты парсинга коммерческих предложений

Эта папка содержит все скрипты для парсинга и валидации коммерческих предложений.

## Основные скрипты

### Парсинг
- `smart_batch_parser.py` - Умный парсер для обработки файлов батчами
- `parse_valid_batches.py` - Парсинг только валидных файлов
- `parse_from_valid_ids.py` - Парсинг по списку ID

### Валидация
- `create_fixed_validation_report.py` - Создание полного отчета валидации
- `create_full_validation_report.py` - Создание детального отчета
- `debug_validation.py` - Отладка валидации
- `simple_validation.py` - Простая валидация

### Утилиты
- `find_and_save_valid_ids.py` - Поиск и сохранение валидных ID

## Использование

1. **Валидация всех файлов:**
```bash
python create_fixed_validation_report.py
```

2. **Парсинг отличных файлов (90%+ рейтинг):**
```bash
python smart_batch_parser.py
```

3. **Парсинг по списку ID:**
```bash
python parse_from_valid_ids.py
```

## Результаты

- JSON отчеты валидации сохраняются в корне проекта
- Спарсенные данные сохраняются в базу данных
- Изображения сохраняются в папку `storage/images/`

## Требования

- Python 3.8+
- Все зависимости из `requirements.txt` в корне проекта
- База данных SQLite в папке `database/`

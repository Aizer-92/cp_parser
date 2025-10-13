# CP Parser Core

Ядро парсинга коммерческих предложений из Google Sheets в PostgreSQL БД.

## 📁 Структура проекта

```
cp_parser_core/
├── parsers/          # Основные парсеры для разных шаблонов
├── utils/            # Вспомогательные утилиты
├── scripts/          # Служебные скрипты
├── config/           # Конфигурационные файлы
├── docs/             # Документация
├── requirements.txt  # Зависимости
└── README.md         # Этот файл
```

## 🚀 Основные парсеры

- `parse_template_4.py` - Парсер для шаблона 4 (тиражи с образцами)
- `parse_template_5.py` - Парсер для шаблона 5
- `parse_template_6.py` - Парсер для шаблона 6
- `parse_master_table.py` - Парсинг мастер-таблицы проектов

## 🛠️ Утилиты

- `google_sheets.py` - Работа с Google Sheets API
- `database.py` - Работа с PostgreSQL
- `ftp_manager.py` - Загрузка изображений на FTP
- `image_processor.py` - Обработка изображений

## 📊 Процесс парсинга

1. Подключение к Google Sheets
2. Определение типа шаблона
3. Извлечение данных товаров
4. Парсинг ценовых предложений
5. Сохранение изображений
6. Загрузка в PostgreSQL

## ⚙️ Настройка

1. Скопируйте `config/config.example.py` в `config/config.py`
2. Настройте подключение к БД
3. Добавьте Google API credentials
4. Настройте FTP для загрузки изображений

## 🔧 Использование

```bash
# Парсинг одного проекта
python parsers/parse_template_4.py --sheet-id "YOUR_SHEET_ID"

# Парсинг всех проектов
python scripts/parse_all_projects.py

# Загрузка изображений на FTP
python scripts/upload_images_to_ftp.py
```

## 📝 Логи

Все логи сохраняются в `logs/` директорию.

## 🔗 Связанные проекты

- **cp_parser** (веб-интерфейс) - просмотр спарсенных данных
- **price_calculator** - калькулятор цен для товаров

---

**Версия:** 1.0  
**Дата:** 13 октября 2025

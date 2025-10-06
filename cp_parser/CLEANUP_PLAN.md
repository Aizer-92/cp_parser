# План очистки проекта CP Parser

## 🗑️ Файлы для удаления

### Временные и отладочные скрипты
- `debug_*.py` - все отладочные скрипты
- `test_*.py` - все тестовые скрипты (кроме основных)
- `analyze_*.py` - скрипты анализа
- `check_*.py` - скрипты проверки
- `clean_*.py` - скрипты очистки
- `improve_*.py` - скрипты улучшения
- `apply_*.py` - скрипты применения патчей

### Устаревшие парсеры
- `batch_parser.py`
- `production_parser.py`
- `run_*.py` - скрипты запуска
- `fill_database_from_production.py`

### Временные отчеты
- `*_report_*.txt` - текстовые отчеты
- `*_batch_*.json` - временные JSON файлы
- `*_results_*.json` - временные результаты
- `*_ids_*.json` - временные списки ID
- `confirmed_*.json` - подтвержденные файлы
- `excellent_*.json` - отличные файлы
- `low_requirement_*.json` - файлы с низкими требованиями
- `manual_*.json` - ручные списки

### Загрузчики изображений (оставить только один рабочий)
- `upload_images_*.py` - все скрипты загрузки (кроме FTP)
- `setup_*.py` - скрипты настройки

### Документация (оставить только основную)
- `ANALYSIS_*.md` - отчеты анализа
- `PARSING_IMPROVEMENT_PLAN.md`
- `PRODUCTION_GUIDE.md`
- `README_DEPLOY.md`
- `VALIDATION_ANALYSIS_REPORT.md`
- `QUICK_SUMMARY_*.md`

### Временные файлы
- `analysis_files_list.txt`
- `parsing_report_*.txt`
- `smart_parsing_report_*.txt`
- `valid_parsing_report_*.txt`

## ✅ Файлы для сохранения

### Основная структура
- `src/` - исходный код парсера
- `database/` - база данных и модели
- `web_interface/` - веб-интерфейс
- `scripts/` - основные скрипты (очистить)
- `storage/` - хранилище данных
- `templates/` - шаблоны веб-интерфейса

### Ключевые файлы
- `uploaded_images_report.json` - отчет о загруженных изображениях
- `uploaded_images_index.json` - индекс загруженных изображений
- `complete_validation_results_*.json` - результаты валидации всех таблиц
- `README.md` - основная документация

### Основные скрипты
- `validate_all_tables.py` - валидация всех таблиц
- `create_uploaded_images_report.py` - создание отчета об изображениях
- `upload_images_ftp.py` - загрузка изображений (рабочий)
- `test_ftp_connection.py` - тест FTP соединения

### Веб-интерфейс
- `web_interface/` - полная папка веб-интерфейса
- `web_viewer_new.py` - новый веб-просмотрщик

## 📁 Структура после очистки

```
projects/cp_parser/
├── src/                          # Исходный код парсера
├── database/                     # База данных
├── web_interface/               # Веб-интерфейс
├── scripts/                     # Основные скрипты
│   ├── cloud_image_manager.py   # Менеджер облачных изображений
│   └── README.md               # Документация скриптов
├── storage/                     # Хранилище данных
├── templates/                   # Шаблоны веб-интерфейса
├── uploaded_images_report.json  # Отчет о загруженных изображениях
├── uploaded_images_index.json   # Индекс загруженных изображений
├── complete_validation_results_*.json  # Результаты валидации
├── validate_all_tables.py       # Валидация всех таблиц
├── create_uploaded_images_report.py  # Создание отчета об изображениях
├── upload_images_ftp.py         # Загрузка изображений
├── test_ftp_connection.py       # Тест FTP соединения
├── web_viewer_new.py           # Веб-просмотрщик
└── README.md                   # Основная документация
```

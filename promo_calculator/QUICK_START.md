# 🚀 Быстрый запуск Промо-Калькулятора

## PostgreSQL версия (основная)
```bash
cd projects/promo_calculator
py main.py
# Открыть: http://localhost:8003
```

## SQLite версия (альтернативная)
```bash
cd projects/promo_calculator
py main_sqlite.py
# Открыть: http://localhost:8003
```

## 📊 Что работает
- ✅ Список товаров с поиском и фильтрацией
- ✅ Детальные карточки товаров
- ✅ Отображение цен в разных валютах
- ✅ Правильное отображение MOQ (целые числа)
- ✅ Изображения товаров
- ✅ Технические характеристики
- ✅ Разделение на обычные варианты и образцы

## 🔧 Требования
- Python 3.12+
- PostgreSQL (для main.py)
- SQLite (для main_sqlite.py)

## 📁 Структура
- `main.py` - PostgreSQL версия
- `main_sqlite.py` - SQLite версия
- `templates/` - HTML шаблоны
- `static/` - CSS/JS файлы
- `database/` - SQLite база данных

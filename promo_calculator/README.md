# Промо-Калькулятор

Веб-интерфейс для работы с базой данных товаров с поддержкой PostgreSQL и SQLite.

## 🚀 Быстрый старт

### PostgreSQL версия (основная)
```bash
# Запуск PostgreSQL интерфейса
py main.py
# Открыть: http://localhost:8003
```

### SQLite версия (альтернативная)
```bash
# Запуск SQLite интерфейса
py main_sqlite.py
# Открыть: http://localhost:8003
```

## 📊 Структура базы данных

Обе версии используют идентичную структуру данных:

### Таблица `products`
- `id` - Уникальный идентификатор
- `offer_id` - ID предложения
- `title` - Название товара
- `original_title` - Оригинальное название
- `description` - Описание
- `price_cny_min/max` - Цена в CNY (мин/макс)
- `price_rub_min/max` - Цена в RUB (мин/макс)
- `price_usd_min/max` - Цена в USD (мин/макс)
- `currency` - Валюта (по умолчанию CNY)
- `moq_min/max` - Минимальный заказ (мин/макс)
- `lead_time` - Время поставки
- `source_url` - URL источника
- `main_image` - Главное изображение
- `vendor` - Поставщик
- `brand` - Бренд
- `total_variants` - Общее количество вариантов
- `source_databases` - Источники данных
- `has_images` - Есть ли изображения
- `has_specifications` - Есть ли характеристики

### Таблица `images`
- `id` - Уникальный идентификатор
- `product_id` - ID товара
- `image_url` - URL изображения
- `local_path` - Локальный путь
- `image_type` - Тип изображения
- `is_primary` - Главное изображение
- `source_database` - Источник данных

### Таблица `specifications`
- `id` - Уникальный идентификатор
- `product_id` - ID товара
- `spec_type` - Тип характеристики
- `spec_name` - Название характеристики
- `spec_value` - Значение характеристики
- `source_database` - Источник данных

### Таблица `product_variants`
- `id` - Уникальный идентификатор
- `product_id` - ID товара
- `variant_name` - Название варианта
- `price_cny/rub/usd` - Цены в разных валютах
- `currency` - Валюта
- `moq` - Минимальный заказ
- `lead_time` - Время поставки
- `transport_tariff` - Транспортный тариф
- `quantity_in_box` - Количество в коробке
- `box_width/height/length` - Размеры коробки
- `box_weight` - Вес коробки
- `item_weight` - Вес единицы
- `cargo_density` - Плотность груза
- `cost_price` - Себестоимость
- `markup_percent` - Наценка в процентах

## 🔧 Настройка

### PostgreSQL
Убедитесь, что PostgreSQL запущен и создана база данных `promo_calculator`.

Переменные окружения:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=promo_calculator
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### SQLite
Файл базы данных: `database/advanced_merged_products_clean.db`

## 📋 Функциональность

### Главная страница
- Список товаров с пагинацией
- Поиск по названию и описанию
- Фильтрация по поставщику
- Фильтрация по наличию изображений/характеристик
- Отображение 3 вариантов цен (исключая образцы)

### Детальная страница товара
- Полная информация о товаре
- Все варианты цен с детальными характеристиками
- Изображения товара
- Технические характеристики
- Разделение на обычные варианты и образцы

### API
- `GET /api/products` - Список товаров
- `GET /api/product/{id}` - Детальная информация о товаре
- `GET /api/statistics` - Статистика базы данных

## 🎨 Особенности интерфейса

- Адаптивный дизайн
- Современный UI с Bootstrap
- Отображение цен в разных валютах
- Правильное округление MOQ (целые числа)
- Сортировка изображений (главное первым)
- Цветовая индикация для образцов и обычных вариантов

## 📁 Структура проекта

```
promo_calculator/
├── main.py                 # PostgreSQL версия
├── main_sqlite.py          # SQLite версия
├── requirements.txt        # Зависимости
├── templates/              # HTML шаблоны
│   ├── final_index.html    # Главная страница
│   ├── final_product_detail.html # Детальная страница
│   └── error.html          # Страница ошибок
├── static/                 # Статические файлы
├── database/               # SQLite база данных
└── README.md              # Документация
```

## 🔄 Миграция данных

Для пересоздания PostgreSQL базы по структуре SQLite:
```bash
py recreate_postgresql_db.py
```

## 🚀 Запуск веб-интерфейсов

**ВАЖНО**: Всегда запускать из правильной директории проекта!

### Алгоритм запуска:
1. `cd projects/promo_calculator`
2. Проверить: `pwd` и `ls *.py`
3. Запуск: `py имя_скрипта.py` (НЕ `python`!)

### PostgreSQL:
```bash
cd projects/promo_calculator
py main.py
# http://localhost:8003
```

### SQLite:
```bash
cd projects/promo_calculator
py main_sqlite.py
# http://localhost:8003
```

## 📊 Статистика

- **Товаров**: 17,973
- **Изображений**: 71,043
- **Характеристик**: 635,359
- **Вариантов**: 45,176

## 🛠️ Технологии

- **Backend**: FastAPI, Python 3.12
- **Базы данных**: PostgreSQL, SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Шаблоны**: Jinja2
- **Векторный поиск**: SentenceTransformers

## 📝 Примечания

- В Windows всегда используйте команду `py` вместо `python`
- MOQ отображается как целые числа (округление)
- Образцы (MOQ=1) исключаются из основного списка
- Главные изображения отображаются первыми
- Поддерживается полнотекстовый поиск в PostgreSQL
# 🗄️ Структура БД и Правила Валидации

**Дата создания**: 08.10.2025  
**Версия**: 1.0  
**База данных**: PostgreSQL

---

## 📋 Оглавление

1. [Структура таблиц](#структура-таблиц)
2. [Правила валидации](#правила-валидации)
3. [Парсинг структуры](#парсинг-структуры)
4. [Требования к данным](#требования-к-данным)
5. [Известные шаблоны](#известные-шаблоны)

---

## 🗄️ Структура таблиц

### 1. Таблица `projects`

Хранит информацию о Google Sheets проектах (коммерческих предложениях).

```sql
CREATE TABLE projects (
    id                    INTEGER PRIMARY KEY,
    table_id              TEXT,            -- ID Google Sheets таблицы
    project_name          TEXT,            -- Название проекта
    file_name             TEXT,            -- Имя файла (при скачивании)
    file_path             TEXT,            -- Путь к локальному файлу
    file_size_mb          TEXT,            -- Размер файла
    google_sheets_url     TEXT,            -- URL Google Sheets
    client_name           TEXT,            -- Имя клиента
    manager_name          TEXT,            -- Менеджер проекта
    region                TEXT,            -- Регион
    min_budget_usd        TEXT,
    max_budget_usd        TEXT,
    min_budget_rub        TEXT,
    max_budget_rub        TEXT,
    min_quantity          INTEGER,
    max_quantity          INTEGER,
    parsing_status        TEXT,            -- 'pending' | 'completed' | 'error'
    structure_type        TEXT,            -- Тип структуры таблицы
    parsing_complexity    TEXT,            -- Сложность парсинга
    total_products_found  INTEGER,
    total_images_found    INTEGER,
    parsing_errors        TEXT,            -- Описание ошибок
    created_at            TEXT,
    updated_at            TEXT,
    parsed_at             TEXT
);
```

**Статусы парсинга:**
- `pending` - ожидает парсинга
- `completed` - успешно распарсен
- `error` - ошибка при парсинге

---

### 2. Таблица `products`

Хранит информацию о товарах.

```sql
CREATE TABLE products (
    id                  INTEGER PRIMARY KEY,
    project_id          INTEGER NOT NULL,       -- FK → projects.id
    table_id            TEXT,                   -- ID таблицы (дубль для удобства)
    name                TEXT NOT NULL,          -- Название товара
    description         TEXT,                   -- Описание
    article_number      TEXT,                   -- Артикул
    custom_field        TEXT,                   -- Доп. поле (дизайн, характеристики)
    sheet_name          TEXT,                   -- Имя листа в Excel
    row_number          INTEGER,                -- Номер строки в таблице
    row_number_end      INTEGER,                -- Конечная строка (для multi-row)
    sample_price        TEXT,                   -- Цена образца
    sample_delivery_time INTEGER,               -- Срок доставки образца
    specifications      TEXT,                   -- Технические характеристики
    custom_fields       TEXT,                   -- JSON с доп. полями
    data_quality        TEXT,                   -- Оценка качества данных
    parsing_notes       TEXT,                   -- Заметки парсера
    created_at          TEXT,
    updated_at          TEXT,
    
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**Обязательные поля для валидации:**
- ✅ `name` - НЕ NULL, длина >= 3 символов
- ✅ `project_id` - должен существовать в `projects`

---

### 3. Таблица `price_offers`

Хранит ценовые предложения для разных тиражей и маршрутов.

```sql
CREATE TABLE price_offers (
    id                    INTEGER PRIMARY KEY,
    product_id            INTEGER NOT NULL,     -- FK → products.id
    table_id              TEXT,                 -- ID таблицы
    quantity              BIGINT,               -- Тираж (может быть > 2млн)
    quantity_unit         TEXT,                 -- Единица измерения (шт, уп, кор)
    price_usd             TEXT,                 -- Цена в долларах
    price_rub             TEXT,                 -- Цена в рублях
    route                 TEXT,                 -- 'ЖД' | 'АВИА' | 'Образец'
    delivery_time_days    INTEGER,              -- Срок доставки (дни)
    delivery_conditions   TEXT,                 -- Условия доставки
    discount_percent      TEXT,                 -- Процент скидки
    special_conditions    TEXT,                 -- Специальные условия
    row_position          TEXT,                 -- Позиция в таблице
    is_recommended        TEXT,                 -- Рекомендуемое предложение
    data_source           TEXT,                 -- Источник данных
    created_at            TEXT,
    updated_at            TEXT,
    
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Правила:**
- Минимум **1 предложение** на товар
- В среднем: **2.84 предложения** на товар (оптимально)
- `quantity` может быть BIGINT (до 500,000+)

---

### 4. Таблица `product_images`

Хранит метаданные изображений товаров.

```sql
CREATE TABLE product_images (
    id                    INTEGER PRIMARY KEY,
    product_id            INTEGER NOT NULL,     -- FK → products.id
    table_id              TEXT,                 -- ID таблицы
    image_url             TEXT,                 -- URL на FTP облаке (ОБЯЗАТЕЛЬНО!)
    local_path            TEXT,                 -- Локальный путь (deprecated)
    image_filename        TEXT,                 -- Имя файла
    sheet_name            TEXT,                 -- Имя листа
    cell_position         TEXT,                 -- Позиция ячейки (A4, B5)
    row_number            INTEGER,              -- Номер строки
    column_number         INTEGER,              -- Номер колонки
    width_px              INTEGER,              -- Ширина (пиксели)
    height_px             INTEGER,              -- Высота (пиксели)
    file_size_kb          TEXT,                 -- Размер файла
    format                TEXT,                 -- Формат (PNG, JPG)
    is_main_image         TEXT,                 -- Главное изображение
    display_order         INTEGER,              -- Порядок отображения
    extraction_method     TEXT,                 -- Метод извлечения
    quality_score         TEXT,                 -- Оценка качества
    processing_status     TEXT,                 -- Статус обработки
    created_at            TEXT,
    updated_at            TEXT,
    
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**КРИТИЧЕСКИ ВАЖНО:**
- ✅ `image_url` должен быть заполнен ПЕРЕД миграцией на Railway
- ✅ Формат URL: `https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}.png`
- ✅ В среднем: **7.27 изображений** на товар

---

## ✅ Правила валидации

### Валидация структуры таблицы

Класс: `CommercialProposalParser` → метод `validate_table_structure()`

#### 1. Обязательные колонки

```python
REQUIRED_COLUMNS = {
    'A': 'Photo',         # Фото товара
    'B': 'Name',          # Название товара
}
```

**Минимум:**
- Колонка **A** (Фото)
- Колонка **B** (Название)
- Хотя бы **1 полный маршрут** (тип + тираж + цена + сроки)

#### 2. Структура маршрута

Полный маршрут включает:
- **Тип маршрута** (ЖД/АВИА) - строка 2 или 3
- **Тираж** - колонка с количеством
- **Цена USD** - следующая колонка
- **Цена RUB** - следующая колонка  
- **Сроки доставки** - следующая колонка

**Примеры валидных структур:**

```
Маршрут 1 (ЖД):     F | G | H    (тираж | USD | RUB | сроки)
Маршрут 2 (АВИА):   I | J | K    (тираж | USD | RUB | сроки)
```

#### 3. Начало данных

```python
DATA_START_ROW = 4  # Данные начинаются с 4-й строки
```

**Структура заголовков:**
- Строка 1: Логотип компании (игнорируется)
- Строка 2: Названия маршрутов ("ЖД", "АВИА", "Образец")
- Строка 3: Подзаголовки ("Тираж", "USD", "RUB", "Сроки")
- Строка 4+: Данные товаров

---

### Валидация данных

#### 1. Название товара

```python
def validate_product_name(name):
    if not name or len(name.strip()) < 3:
        return False
    
    # Исключаем служебные строки
    EXCLUDED_KEYWORDS = [
        'фото', 'наименование', 'название', 
        'характеристики', 'тираж', 'цена'
    ]
    
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in name.lower():
            return False
    
    return True
```

#### 2. Количество (тираж)

```python
def validate_quantity(qty_str):
    # Парсинг с дефисом: "300-500" → 300
    if '-' in qty_str:
        qty_str = qty_str.split('-')[0].strip()
    
    qty = int(''.join(filter(str.isdigit, qty_str)))
    
    # Фильтр аномалий
    if qty <= 0 or qty > 1_000_000:
        return None
    
    return qty
```

#### 3. Цены

```python
def validate_price_usd(price_str):
    price = float(price_str.replace(',', '.').strip())
    
    # Фильтр аномалий
    if price > 10_000:
        return None
    
    return price

def validate_price_rub(price_str):
    price = float(price_str.replace(',', '.').replace(' ', '').strip())
    
    # Фильтр аномалий
    if price > 1_000_000:
        return None
    
    return price
```

#### 4. Сроки доставки

```python
def validate_delivery_time(time_str):
    # Парсинг с дефисом: "17-19" → 19 (берем МАКСИМУМ)
    if '-' in time_str:
        time_str = time_str.split('-')[-1].strip()
    
    days = int(''.join(filter(str.isdigit, time_str)))
    
    # Фильтр аномалий
    if days > 365:
        return 60  # Default для ЖД
    
    return days
```

**Правило**: При диапазоне берем **большее** значение (хуже для клиента, но безопаснее).

---

## 🔍 Парсинг структуры

### 1. Динамическое определение data_start_row

```python
def find_data_start_row(worksheet):
    # Ищем "Наименование" во 2-й строке
    for row in range(1, 5):
        for col in range(1, 10):
            cell_value = str(worksheet.cell(row, col).value or '').lower()
            if 'наименование' in cell_value:
                return row + 2  # Данные через 2 строки
    
    return 4  # По умолчанию
```

### 2. Парсинг маршрутов

```python
# Строка 2: названия маршрутов
route_jd_name = worksheet.cell(2, 6).value or ''     # F2
route_avia_name = worksheet.cell(2, 9).value or ''   # I2

# Проверка на "Образец"
is_sample_route = 'образец' in route_avia_name.lower()

if is_sample_route:
    # Парсим ТОЛЬКО ЖД маршрут
    routes = ['ЖД']
else:
    # Парсим ОБА маршрута
    routes = ['ЖД', 'АВИА']
```

### 3. Multi-row товары

```python
def parse_multi_row_product(worksheet, start_row):
    """
    Парсинг товара, который занимает несколько строк
    (дополнительные тиражи в следующих строках)
    """
    offers = []
    current_row = start_row
    
    while True:
        # Парсим предложения из текущей строки
        row_offers = parse_offers_from_row(worksheet, current_row)
        offers.extend(row_offers)
        
        # Проверяем следующую строку
        next_row = current_row + 1
        next_name = worksheet.cell(next_row, 2).value
        next_qty = worksheet.cell(next_row, 5).value
        
        # Если название пустое, но есть тираж → доп. строка
        if (not next_name or len(str(next_name).strip()) < 3) and next_qty:
            current_row = next_row
            continue
        else:
            break
    
    return offers
```

---

## 📏 Требования к данным

### Минимальные требования для успешного парсинга

| Поле | Требование |
|------|-----------|
| **Фото** | Колонка A должна существовать |
| **Название** | Колонка B, длина >= 3, не служебное слово |
| **Маршрут** | Минимум 1 полный маршрут (тип + тираж + цена + сроки) |
| **Тираж** | Число > 0 и <= 1,000,000 |
| **Цена USD** | Число > 0 и <= 10,000 |
| **Цена RUB** | Число > 0 и <= 1,000,000 |
| **Сроки** | Число > 0 и <= 365 дней |

### Рекомендуемые значения

| Метрика | Рекомендация |
|---------|-------------|
| Предложений на товар | >= 2 (оптимально 2-4) |
| Изображений на товар | >= 1 (оптимально 5-10) |
| Заполненность описания | > 50% |
| Маршруты | ЖД + АВИА (2 варианта) |

---

## 🎯 Известные шаблоны таблиц

### Шаблон 1: Стандартный (272 проекта)

```
| A    | B          | C          | D      | E     | F      | G      | H      | I      | J      | K      |
|------|------------|------------|--------|-------|--------|--------|--------|--------|--------|--------|
| Фото | Название   | Описание   | Дизайн | ЖД    |        |        | АВИА   |        |        |        |
|      |            |            |        | Тираж | USD    | RUB    | Тираж  | USD    | RUB    |        |
|      |            |            |        |       |        | Сроки  |        |        | Сроки  |        |
| IMG  | Товар 1    | Описание 1 | Сток   | 1000  | 5.50   | 500    | 1000   | 6.00   | 550    | 40     |
```

**Характеристики:**
- ✅ Стандартная структура
- ✅ 2 маршрута (ЖД + АВИА)
- ✅ Данные с 4-й строки

### Шаблон 2: С колонкой "Итого, руб"

```
| A    | B          | C          | D      | E     | F      | G      | H       | I      | J      | K      | L       |
|------|------------|------------|--------|-------|--------|--------|---------|--------|--------|--------|---------|
| Фото | Название   | Описание   | Дизайн | ЖД    |        |        | Итого   | АВИА   |        |        | Итого   |
|      |            |            |        | Тираж | USD    | RUB    | RUB     | Тираж  | USD    | RUB    | RUB     |
```

**Характеристики:**
- ✅ Есть колонка "Итого, руб" (ИГНОРИРУЕТСЯ при парсинге)
- ✅ Структура сдвинута на 1 колонку

### Шаблон 3: С "Образцом"

```
| A    | B          | C          | D      | E     | F      | G      | H       | I        |
|------|------------|------------|--------|-------|--------|--------|---------|----------|
| Фото | Название   | Описание   | Дизайн | ЖД    |        |        | Образец |          |
|      |            |            |        | Тираж | USD    | RUB    | Цена    | Сроки    |
```

**Характеристики:**
- ✅ Вместо АВИА - "Образец"
- ✅ Парсится ТОЛЬКО ЖД маршрут
- ⚠️ "Образец" игнорируется (не добавляется как route)

---

## 🔧 Настройка парсера

### Файл: `src/structure_parser.py`

```python
class CommercialProposalParser:
    # Обязательные колонки
    REQUIRED_MAIN_COLUMNS = ['A', 'B']
    
    # Начало данных (может быть динамическим)
    DEFAULT_DATA_START_ROW = 4
    
    # Фильтры аномалий
    MAX_QUANTITY = 1_000_000
    MAX_PRICE_USD = 10_000
    MAX_PRICE_RUB = 1_000_000
    MAX_DELIVERY_DAYS = 365
```

### Файл: `parse_validated_272_files.py`

```python
# Колонки маршрутов
JD_ROUTE_COLUMNS = {
    'qty': 5,      # E
    'usd': 6,      # F
    'rub': 7,      # G
    'delivery': 8  # H
}

AVIA_ROUTE_COLUMNS = {
    'qty': 5,      # E (дублируется с ЖД)
    'usd': 9,      # I
    'rub': 10,     # J
    'delivery': 11 # K
}
```

---

## 📊 Статистика качества (текущая)

```
Проектов валидных:     272 / 3,261 (8.3%)
Товаров:               8,717
Предложений на товар:  2.84 (среднее)
Изображений на товар:  7.27 (среднее)
Успешность парсинга:   98.9% (269/272)
```

**Критерии качества:**
- ✅ >= 2 предложения на товар
- ✅ >= 1 изображение на товар
- ✅ Заполнены обязательные поля
- ✅ Цены в реалистичных диапазонах

---

## 🚀 Дальнейшее развитие

### Планируется поддержка новых структур:

1. **Шаблон 4**: Таблицы с доп. колонками (артикул, бренд)
2. **Шаблон 5**: Матричные цены (цена зависит от 2 параметров)
3. **Шаблон 6**: Таблицы с вариантами товара (цвета, размеры)

### Для добавления нового шаблона:

1. Проанализировать структуру в `check_new_template.py`
2. Обновить `CommercialProposalParser.validate_table_structure()`
3. Добавить логику парсинга в `parse_validated_272_files.py`
4. Протестировать на 10 файлах
5. Обновить эту документацию

---

**Дата последнего обновления**: 08.10.2025  
**Версия**: 1.0  
**Автор**: Reshad







**Дата создания**: 08.10.2025  
**Версия**: 1.0  
**База данных**: PostgreSQL

---

## 📋 Оглавление

1. [Структура таблиц](#структура-таблиц)
2. [Правила валидации](#правила-валидации)
3. [Парсинг структуры](#парсинг-структуры)
4. [Требования к данным](#требования-к-данным)
5. [Известные шаблоны](#известные-шаблоны)

---

## 🗄️ Структура таблиц

### 1. Таблица `projects`

Хранит информацию о Google Sheets проектах (коммерческих предложениях).

```sql
CREATE TABLE projects (
    id                    INTEGER PRIMARY KEY,
    table_id              TEXT,            -- ID Google Sheets таблицы
    project_name          TEXT,            -- Название проекта
    file_name             TEXT,            -- Имя файла (при скачивании)
    file_path             TEXT,            -- Путь к локальному файлу
    file_size_mb          TEXT,            -- Размер файла
    google_sheets_url     TEXT,            -- URL Google Sheets
    client_name           TEXT,            -- Имя клиента
    manager_name          TEXT,            -- Менеджер проекта
    region                TEXT,            -- Регион
    min_budget_usd        TEXT,
    max_budget_usd        TEXT,
    min_budget_rub        TEXT,
    max_budget_rub        TEXT,
    min_quantity          INTEGER,
    max_quantity          INTEGER,
    parsing_status        TEXT,            -- 'pending' | 'completed' | 'error'
    structure_type        TEXT,            -- Тип структуры таблицы
    parsing_complexity    TEXT,            -- Сложность парсинга
    total_products_found  INTEGER,
    total_images_found    INTEGER,
    parsing_errors        TEXT,            -- Описание ошибок
    created_at            TEXT,
    updated_at            TEXT,
    parsed_at             TEXT
);
```

**Статусы парсинга:**
- `pending` - ожидает парсинга
- `completed` - успешно распарсен
- `error` - ошибка при парсинге

---

### 2. Таблица `products`

Хранит информацию о товарах.

```sql
CREATE TABLE products (
    id                  INTEGER PRIMARY KEY,
    project_id          INTEGER NOT NULL,       -- FK → projects.id
    table_id            TEXT,                   -- ID таблицы (дубль для удобства)
    name                TEXT NOT NULL,          -- Название товара
    description         TEXT,                   -- Описание
    article_number      TEXT,                   -- Артикул
    custom_field        TEXT,                   -- Доп. поле (дизайн, характеристики)
    sheet_name          TEXT,                   -- Имя листа в Excel
    row_number          INTEGER,                -- Номер строки в таблице
    row_number_end      INTEGER,                -- Конечная строка (для multi-row)
    sample_price        TEXT,                   -- Цена образца
    sample_delivery_time INTEGER,               -- Срок доставки образца
    specifications      TEXT,                   -- Технические характеристики
    custom_fields       TEXT,                   -- JSON с доп. полями
    data_quality        TEXT,                   -- Оценка качества данных
    parsing_notes       TEXT,                   -- Заметки парсера
    created_at          TEXT,
    updated_at          TEXT,
    
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**Обязательные поля для валидации:**
- ✅ `name` - НЕ NULL, длина >= 3 символов
- ✅ `project_id` - должен существовать в `projects`

---

### 3. Таблица `price_offers`

Хранит ценовые предложения для разных тиражей и маршрутов.

```sql
CREATE TABLE price_offers (
    id                    INTEGER PRIMARY KEY,
    product_id            INTEGER NOT NULL,     -- FK → products.id
    table_id              TEXT,                 -- ID таблицы
    quantity              BIGINT,               -- Тираж (может быть > 2млн)
    quantity_unit         TEXT,                 -- Единица измерения (шт, уп, кор)
    price_usd             TEXT,                 -- Цена в долларах
    price_rub             TEXT,                 -- Цена в рублях
    route                 TEXT,                 -- 'ЖД' | 'АВИА' | 'Образец'
    delivery_time_days    INTEGER,              -- Срок доставки (дни)
    delivery_conditions   TEXT,                 -- Условия доставки
    discount_percent      TEXT,                 -- Процент скидки
    special_conditions    TEXT,                 -- Специальные условия
    row_position          TEXT,                 -- Позиция в таблице
    is_recommended        TEXT,                 -- Рекомендуемое предложение
    data_source           TEXT,                 -- Источник данных
    created_at            TEXT,
    updated_at            TEXT,
    
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**Правила:**
- Минимум **1 предложение** на товар
- В среднем: **2.84 предложения** на товар (оптимально)
- `quantity` может быть BIGINT (до 500,000+)

---

### 4. Таблица `product_images`

Хранит метаданные изображений товаров.

```sql
CREATE TABLE product_images (
    id                    INTEGER PRIMARY KEY,
    product_id            INTEGER NOT NULL,     -- FK → products.id
    table_id              TEXT,                 -- ID таблицы
    image_url             TEXT,                 -- URL на FTP облаке (ОБЯЗАТЕЛЬНО!)
    local_path            TEXT,                 -- Локальный путь (deprecated)
    image_filename        TEXT,                 -- Имя файла
    sheet_name            TEXT,                 -- Имя листа
    cell_position         TEXT,                 -- Позиция ячейки (A4, B5)
    row_number            INTEGER,              -- Номер строки
    column_number         INTEGER,              -- Номер колонки
    width_px              INTEGER,              -- Ширина (пиксели)
    height_px             INTEGER,              -- Высота (пиксели)
    file_size_kb          TEXT,                 -- Размер файла
    format                TEXT,                 -- Формат (PNG, JPG)
    is_main_image         TEXT,                 -- Главное изображение
    display_order         INTEGER,              -- Порядок отображения
    extraction_method     TEXT,                 -- Метод извлечения
    quality_score         TEXT,                 -- Оценка качества
    processing_status     TEXT,                 -- Статус обработки
    created_at            TEXT,
    updated_at            TEXT,
    
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

**КРИТИЧЕСКИ ВАЖНО:**
- ✅ `image_url` должен быть заполнен ПЕРЕД миграцией на Railway
- ✅ Формат URL: `https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}.png`
- ✅ В среднем: **7.27 изображений** на товар

---

## ✅ Правила валидации

### Валидация структуры таблицы

Класс: `CommercialProposalParser` → метод `validate_table_structure()`

#### 1. Обязательные колонки

```python
REQUIRED_COLUMNS = {
    'A': 'Photo',         # Фото товара
    'B': 'Name',          # Название товара
}
```

**Минимум:**
- Колонка **A** (Фото)
- Колонка **B** (Название)
- Хотя бы **1 полный маршрут** (тип + тираж + цена + сроки)

#### 2. Структура маршрута

Полный маршрут включает:
- **Тип маршрута** (ЖД/АВИА) - строка 2 или 3
- **Тираж** - колонка с количеством
- **Цена USD** - следующая колонка
- **Цена RUB** - следующая колонка  
- **Сроки доставки** - следующая колонка

**Примеры валидных структур:**

```
Маршрут 1 (ЖД):     F | G | H    (тираж | USD | RUB | сроки)
Маршрут 2 (АВИА):   I | J | K    (тираж | USD | RUB | сроки)
```

#### 3. Начало данных

```python
DATA_START_ROW = 4  # Данные начинаются с 4-й строки
```

**Структура заголовков:**
- Строка 1: Логотип компании (игнорируется)
- Строка 2: Названия маршрутов ("ЖД", "АВИА", "Образец")
- Строка 3: Подзаголовки ("Тираж", "USD", "RUB", "Сроки")
- Строка 4+: Данные товаров

---

### Валидация данных

#### 1. Название товара

```python
def validate_product_name(name):
    if not name or len(name.strip()) < 3:
        return False
    
    # Исключаем служебные строки
    EXCLUDED_KEYWORDS = [
        'фото', 'наименование', 'название', 
        'характеристики', 'тираж', 'цена'
    ]
    
    for keyword in EXCLUDED_KEYWORDS:
        if keyword in name.lower():
            return False
    
    return True
```

#### 2. Количество (тираж)

```python
def validate_quantity(qty_str):
    # Парсинг с дефисом: "300-500" → 300
    if '-' in qty_str:
        qty_str = qty_str.split('-')[0].strip()
    
    qty = int(''.join(filter(str.isdigit, qty_str)))
    
    # Фильтр аномалий
    if qty <= 0 or qty > 1_000_000:
        return None
    
    return qty
```

#### 3. Цены

```python
def validate_price_usd(price_str):
    price = float(price_str.replace(',', '.').strip())
    
    # Фильтр аномалий
    if price > 10_000:
        return None
    
    return price

def validate_price_rub(price_str):
    price = float(price_str.replace(',', '.').replace(' ', '').strip())
    
    # Фильтр аномалий
    if price > 1_000_000:
        return None
    
    return price
```

#### 4. Сроки доставки

```python
def validate_delivery_time(time_str):
    # Парсинг с дефисом: "17-19" → 19 (берем МАКСИМУМ)
    if '-' in time_str:
        time_str = time_str.split('-')[-1].strip()
    
    days = int(''.join(filter(str.isdigit, time_str)))
    
    # Фильтр аномалий
    if days > 365:
        return 60  # Default для ЖД
    
    return days
```

**Правило**: При диапазоне берем **большее** значение (хуже для клиента, но безопаснее).

---

## 🔍 Парсинг структуры

### 1. Динамическое определение data_start_row

```python
def find_data_start_row(worksheet):
    # Ищем "Наименование" во 2-й строке
    for row in range(1, 5):
        for col in range(1, 10):
            cell_value = str(worksheet.cell(row, col).value or '').lower()
            if 'наименование' in cell_value:
                return row + 2  # Данные через 2 строки
    
    return 4  # По умолчанию
```

### 2. Парсинг маршрутов

```python
# Строка 2: названия маршрутов
route_jd_name = worksheet.cell(2, 6).value or ''     # F2
route_avia_name = worksheet.cell(2, 9).value or ''   # I2

# Проверка на "Образец"
is_sample_route = 'образец' in route_avia_name.lower()

if is_sample_route:
    # Парсим ТОЛЬКО ЖД маршрут
    routes = ['ЖД']
else:
    # Парсим ОБА маршрута
    routes = ['ЖД', 'АВИА']
```

### 3. Multi-row товары

```python
def parse_multi_row_product(worksheet, start_row):
    """
    Парсинг товара, который занимает несколько строк
    (дополнительные тиражи в следующих строках)
    """
    offers = []
    current_row = start_row
    
    while True:
        # Парсим предложения из текущей строки
        row_offers = parse_offers_from_row(worksheet, current_row)
        offers.extend(row_offers)
        
        # Проверяем следующую строку
        next_row = current_row + 1
        next_name = worksheet.cell(next_row, 2).value
        next_qty = worksheet.cell(next_row, 5).value
        
        # Если название пустое, но есть тираж → доп. строка
        if (not next_name or len(str(next_name).strip()) < 3) and next_qty:
            current_row = next_row
            continue
        else:
            break
    
    return offers
```

---

## 📏 Требования к данным

### Минимальные требования для успешного парсинга

| Поле | Требование |
|------|-----------|
| **Фото** | Колонка A должна существовать |
| **Название** | Колонка B, длина >= 3, не служебное слово |
| **Маршрут** | Минимум 1 полный маршрут (тип + тираж + цена + сроки) |
| **Тираж** | Число > 0 и <= 1,000,000 |
| **Цена USD** | Число > 0 и <= 10,000 |
| **Цена RUB** | Число > 0 и <= 1,000,000 |
| **Сроки** | Число > 0 и <= 365 дней |

### Рекомендуемые значения

| Метрика | Рекомендация |
|---------|-------------|
| Предложений на товар | >= 2 (оптимально 2-4) |
| Изображений на товар | >= 1 (оптимально 5-10) |
| Заполненность описания | > 50% |
| Маршруты | ЖД + АВИА (2 варианта) |

---

## 🎯 Известные шаблоны таблиц

### Шаблон 1: Стандартный (272 проекта)

```
| A    | B          | C          | D      | E     | F      | G      | H      | I      | J      | K      |
|------|------------|------------|--------|-------|--------|--------|--------|--------|--------|--------|
| Фото | Название   | Описание   | Дизайн | ЖД    |        |        | АВИА   |        |        |        |
|      |            |            |        | Тираж | USD    | RUB    | Тираж  | USD    | RUB    |        |
|      |            |            |        |       |        | Сроки  |        |        | Сроки  |        |
| IMG  | Товар 1    | Описание 1 | Сток   | 1000  | 5.50   | 500    | 1000   | 6.00   | 550    | 40     |
```

**Характеристики:**
- ✅ Стандартная структура
- ✅ 2 маршрута (ЖД + АВИА)
- ✅ Данные с 4-й строки

### Шаблон 2: С колонкой "Итого, руб"

```
| A    | B          | C          | D      | E     | F      | G      | H       | I      | J      | K      | L       |
|------|------------|------------|--------|-------|--------|--------|---------|--------|--------|--------|---------|
| Фото | Название   | Описание   | Дизайн | ЖД    |        |        | Итого   | АВИА   |        |        | Итого   |
|      |            |            |        | Тираж | USD    | RUB    | RUB     | Тираж  | USD    | RUB    | RUB     |
```

**Характеристики:**
- ✅ Есть колонка "Итого, руб" (ИГНОРИРУЕТСЯ при парсинге)
- ✅ Структура сдвинута на 1 колонку

### Шаблон 3: С "Образцом"

```
| A    | B          | C          | D      | E     | F      | G      | H       | I        |
|------|------------|------------|--------|-------|--------|--------|---------|----------|
| Фото | Название   | Описание   | Дизайн | ЖД    |        |        | Образец |          |
|      |            |            |        | Тираж | USD    | RUB    | Цена    | Сроки    |
```

**Характеристики:**
- ✅ Вместо АВИА - "Образец"
- ✅ Парсится ТОЛЬКО ЖД маршрут
- ⚠️ "Образец" игнорируется (не добавляется как route)

---

## 🔧 Настройка парсера

### Файл: `src/structure_parser.py`

```python
class CommercialProposalParser:
    # Обязательные колонки
    REQUIRED_MAIN_COLUMNS = ['A', 'B']
    
    # Начало данных (может быть динамическим)
    DEFAULT_DATA_START_ROW = 4
    
    # Фильтры аномалий
    MAX_QUANTITY = 1_000_000
    MAX_PRICE_USD = 10_000
    MAX_PRICE_RUB = 1_000_000
    MAX_DELIVERY_DAYS = 365
```

### Файл: `parse_validated_272_files.py`

```python
# Колонки маршрутов
JD_ROUTE_COLUMNS = {
    'qty': 5,      # E
    'usd': 6,      # F
    'rub': 7,      # G
    'delivery': 8  # H
}

AVIA_ROUTE_COLUMNS = {
    'qty': 5,      # E (дублируется с ЖД)
    'usd': 9,      # I
    'rub': 10,     # J
    'delivery': 11 # K
}
```

---

## 📊 Статистика качества (текущая)

```
Проектов валидных:     272 / 3,261 (8.3%)
Товаров:               8,717
Предложений на товар:  2.84 (среднее)
Изображений на товар:  7.27 (среднее)
Успешность парсинга:   98.9% (269/272)
```

**Критерии качества:**
- ✅ >= 2 предложения на товар
- ✅ >= 1 изображение на товар
- ✅ Заполнены обязательные поля
- ✅ Цены в реалистичных диапазонах

---

## 🚀 Дальнейшее развитие

### Планируется поддержка новых структур:

1. **Шаблон 4**: Таблицы с доп. колонками (артикул, бренд)
2. **Шаблон 5**: Матричные цены (цена зависит от 2 параметров)
3. **Шаблон 6**: Таблицы с вариантами товара (цвета, размеры)

### Для добавления нового шаблона:

1. Проанализировать структуру в `check_new_template.py`
2. Обновить `CommercialProposalParser.validate_table_structure()`
3. Добавить логику парсинга в `parse_validated_272_files.py`
4. Протестировать на 10 файлах
5. Обновить эту документацию

---

**Дата последнего обновления**: 08.10.2025  
**Версия**: 1.0  
**Автор**: Reshad














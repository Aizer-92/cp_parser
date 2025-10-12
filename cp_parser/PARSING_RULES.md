# 📋 ПРАВИЛА ПАРСИНГА КОММЕРЧЕСКИХ ПРЕДЛОЖЕНИЙ

## 🎯 СТРУКТУРА EXCEL ФАЙЛОВ

### Базовая структура таблицы:

```
| A      | B           | C                | D         | E      | F        | G         | H       | I        | J         | K       |
|--------|-------------|------------------|-----------|--------|----------|-----------|---------|----------|-----------|---------|
| [Фото] | Наименование| Характеристики   | Кастом    | Тираж  | USD ЖД   | RUB ЖД    | Срок ЖД | USD АВИА | RUB АВИА  | Срок    |
| [IMG]  | Товар 1     | Описание...      | Дизайн... | 1000   | 5.50     | 500       | 60      | 6.00     | 550       | 30      |
|        |             |                  |           | 3000   | 5.00     | 450       | 60      | 5.50     | 500       | 30      |
| [IMG]  | Товар 2     | Другое описание  | ...       | 500    | 10.00    | 900       | 55      | 11.00    | 1000      | 25      |
```

---

## 🔧 ПРАВИЛА ПАРСИНГА

### 1. **Начало данных**
- Данные начинаются с **строки 5** (пропускаем заголовки)
- Парсинг до строки **500** максимум

### 2. **Идентификация товара**
- **Столбец B (2)** = Название товара
- Минимальная длина названия: **3 символа**
- Пропускаем строки с заголовками: `фото`, `наименование`, `название`, `характеристики`, `тираж`, `цена`

### 3. **Многострочные товары (КРИТИЧЕСКИ ВАЖНО!)**
- Один товар может занимать **несколько строк** с разными тиражами
- **Алгоритм:**
  1. Читаем название товара из столбца B
  2. Парсим предложения из текущей строки
  3. **Проверяем следующие строки:**
     - Если название ПУСТОЕ, но есть тираж (столбец E) → это дополнительное предложение для ТОГО ЖЕ товара
     - Добавляем все предложения к одному товару
  4. Прекращаем, когда встречаем новое название или пустую строку без тиража

**Пример:**
```
| B           | E      | F        | ... |
|-------------|--------|----------|-----|
| Кружка      | 1000   | 5.50     | ... | ← Товар 1, предложение 1
|             | 3000   | 5.00     | ... | ← Товар 1, предложение 2 (название пустое!)
|             | 5000   | 4.80     | ... | ← Товар 1, предложение 3 (название пустое!)
| Блокнот     | 500    | 2.00     | ... | ← Товар 2, предложение 1
```

### 4. **Поля товара**

| Поле          | Столбец | Тип    | Обязательное | Обработка                     |
|---------------|---------|--------|--------------|-------------------------------|
| name          | B (2)   | String | ✅           | `str(value).strip()`          |
| description   | C (3)   | String | ❌           | `str(value)` если есть        |
| custom_field  | D (4)   | String | ❌           | `str(value)` если есть        |

### 5. **Ценовые предложения (Price Offers)**

#### 📦 **Маршрут ЖД (Железная дорога)**
| Поле                | Столбец | Тип   | Обработка                                  |
|---------------------|---------|-------|-------------------------------------------|
| quantity            | E (5)   | Int   | Если есть `-` → берем первое число        |
| price_usd           | F (6)   | Float | `replace(',', '.')`                       |
| price_rub           | G (7)   | Float | `replace(',', '.').replace(' ', '')`      |
| delivery_time_days  | H (8)   | Int   | Извлекаем цифры                           |
| route               | -       | String| **"ЖД"**                                  |

#### ✈️ **Маршрут АВИА**
| Поле                | Столбец | Тип   | Обработка                                  |
|---------------------|---------|-------|-------------------------------------------|
| quantity            | E (5)   | Int   | **ТОТ ЖЕ** тираж, что и для ЖД           |
| price_usd           | I (9)   | Float | `replace(',', '.')`                       |
| price_rub           | J (10)  | Float | `replace(',', '.').replace(' ', '')`      |
| delivery_time_days  | K (11)  | Int   | Извлекаем цифры                           |
| route               | -       | String| **"АВИА"**                                |

#### ⚠️ **ВАЖНО:**
- Если в строке есть тираж (E) → создаем **ДВА** предложения: ЖД + АВИА (если цены есть)
- Предложение создается только если есть `price_usd` ИЛИ `price_rub`
- Если нет цен ЖД/АВИА → пропускаем это предложение

### 6. **Обработка тиража (Quantity)**

**Варианты формата:**
- `1000` → `1000`
- `300-500` → `300` (берем первое число)
- `5 000` → `5000` (убираем пробелы)
- `10000шт` → `10000` (извлекаем только цифры)

**Код:**
```python
qty_str = str(cell_value).strip()
if '-' in qty_str:
    qty_str = qty_str.split('-')[0].strip()
qty = int(''.join(filter(str.isdigit, qty_str)))
```

### 7. **Изображения (Product Images)**

#### 📷 **Извлечение из Excel**
- Изображения хранятся как **blob данные** внутри `.xlsx` файлов
- Используем `openpyxl` с `data_only=False` для извлечения
- Доступ через `worksheet._images`

#### 📁 **Формат имени файла:**
```
{table_id}_{cell_position}_{hash}.png
```

**Пример:**
```
11Zs0Urnzve7URBBwgWsonjjgOWc414YP_Onkxo0AMRo_N7_474edece.png
```

Где:
- `11Zs0Urnzve7URBBwgWsonjjgOWc414YP_Onkxo0AMRo` = Google Sheets Table ID
- `N7` = Позиция ячейки (столбец N, строка 7)
- `474edece` = MD5 hash изображения (первые 8 символов)

#### 🔗 **Привязка к товарам:**
- Изображения привязываются по **диапазону строк**: ±2 от строки товара
- Если товар в строке 10, ищем изображения в строках 8-12
- **Несколько изображений** на товар → сохраняем все

#### 💾 **Поля в БД:**
| Поле          | Тип    | Описание                              |
|---------------|--------|---------------------------------------|
| product_id    | Int    | FK к таблице `products`               |
| table_id      | String | ID Google Sheets таблицы              |
| image_filename| String | Имя файла (см. формат выше)           |
| cell_position | String | Позиция в таблице (A1, B5, N7...)     |
| row_number    | Int    | Номер строки                          |
| column_number | Int    | Номер столбца                         |

---

## 📊 ВАЛИДАЦИЯ СТРУКТУРЫ

### Минимальные требования:

1. ✅ **Обязательные столбцы** (для валидации):
   - Фото (A)
   - Наименование (B)
   - Тираж (E)
   - Цены (F, G, I, J - хотя бы одна)
   - Срок доставки (H, K)

2. ✅ **Проверка заголовков:**
   - Ищем ключевые слова: `фото`, `наименование`, `тираж`, `цена`, `доставка`
   - Проверяем наличие маршрутов: `жд`, `авиа`, `ж/д`, `авто`

3. ✅ **Валидация данных:**
   - `quantity > 0`
   - `price_usd > 0` ИЛИ `price_rub > 0`
   - `delivery_time_days >= 0`

---

## 🗄️ СХЕМА БАЗЫ ДАННЫХ

### **Таблица: `projects`**
```sql
id                  SERIAL PRIMARY KEY
project_name        VARCHAR(500)
table_id            VARCHAR(200)  -- Google Sheets ID
google_sheets_url   TEXT
parsing_status      VARCHAR(50)   -- 'pending', 'completed', 'error'
parsing_errors      TEXT
parsed_at           TIMESTAMP
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### **Таблица: `products`**
```sql
id                  SERIAL PRIMARY KEY
project_id          INTEGER FK → projects.id
table_id            VARCHAR(200)
name                VARCHAR(500)  -- Столбец B
description         TEXT          -- Столбец C
custom_field        TEXT          -- Столбец D (дизайн)
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### **Таблица: `price_offers`**
```sql
id                  SERIAL PRIMARY KEY
product_id          INTEGER FK → products.id
quantity            INTEGER       -- Столбец E
price_usd           DECIMAL(10,2) -- Столбцы F/I
price_rub           DECIMAL(10,2) -- Столбцы G/J
route               VARCHAR(50)   -- "ЖД" или "АВИА"
delivery_time_days  INTEGER       -- Столбцы H/K
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### **Таблица: `product_images`**
```sql
id                  SERIAL PRIMARY KEY
product_id          INTEGER FK → products.id
table_id            VARCHAR(200)
image_filename      VARCHAR(500)
cell_position       VARCHAR(10)   -- "A1", "N7"
row_number          INTEGER
column_number       INTEGER
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

---

## 🚀 ПРОЦЕСС ПАРСИНГА

### Шаг 1: Загрузка файла
```python
# Для изображений (БЕЗ data_only)
workbook_images = load_workbook(file_path, data_only=False)

# Для данных (С data_only для вычисленных значений)
workbook_data = load_workbook(file_path, data_only=True)
```

### Шаг 2: Извлечение изображений
```python
images_by_row = {}  # {row_idx: [{'filename': ..., 'cell_position': ..., ...}]}

if hasattr(worksheet_images, '_images'):
    for img in worksheet_images._images:
        row = img.anchor._from.row + 1
        col = img.anchor._from.col + 1
        img_data = save_image_from_excel(img, table_id, row, col)
        images_by_row[row].append(img_data)
```

### Шаг 3: Парсинг товаров
```python
skip_rows = set()  # Уже обработанные строки

for row_idx in range(5, 500):
    if row_idx in skip_rows:
        continue
    
    name = worksheet_data.cell(row_idx, 2).value  # Столбец B
    
    if not name or len(name) < 3:
        continue
    
    # Парсим предложения из текущей строки
    offers = parse_offers_from_row(row_idx)
    
    # Проверяем следующие строки на дополнительные предложения
    check_row = row_idx + 1
    while check_row < 500:
        next_name = worksheet_data.cell(check_row, 2).value
        next_qty = worksheet_data.cell(check_row, 5).value
        
        if next_name and len(str(next_name)) >= 3:
            break  # Новый товар
        
        if next_qty:
            # Дополнительное предложение для ТОГО ЖЕ товара
            additional_offers = parse_offers_from_row(check_row)
            offers.extend(additional_offers)
            skip_rows.add(check_row)
            check_row += 1
        else:
            break
    
    # Ищем изображения (±2 строки)
    product_images = []
    for check_row in range(max(1, row_idx - 2), row_idx + 3):
        if check_row in images_by_row:
            product_images.extend(images_by_row[check_row])
    
    # Сохраняем товар
    save_product(name, description, custom_field, offers, product_images)
```

### Шаг 4: Парсинг предложений
```python
def parse_offers_from_row(row_idx):
    offers = []
    
    # Тираж
    qty_cell = worksheet_data.cell(row_idx, 5)
    if not qty_cell.value:
        return offers
    
    qty_str = str(qty_cell.value).strip()
    if '-' in qty_str:
        qty_str = qty_str.split('-')[0].strip()
    qty = int(''.join(filter(str.isdigit, qty_str)))
    
    # ЖД маршрут
    price_usd_jd = parse_float(worksheet_data.cell(row_idx, 6).value)
    price_rub_jd = parse_float(worksheet_data.cell(row_idx, 7).value)
    delivery_jd = parse_int(worksheet_data.cell(row_idx, 8).value)
    
    if price_usd_jd or price_rub_jd:
        offers.append({
            'quantity': qty,
            'price_usd': price_usd_jd,
            'price_rub': price_rub_jd,
            'route': 'ЖД',
            'delivery_time_days': delivery_jd or 60
        })
    
    # АВИА маршрут
    price_usd_avia = parse_float(worksheet_data.cell(row_idx, 9).value)
    price_rub_avia = parse_float(worksheet_data.cell(row_idx, 10).value)
    delivery_avia = parse_int(worksheet_data.cell(row_idx, 11).value)
    
    if price_usd_avia or price_rub_avia:
        offers.append({
            'quantity': qty,
            'price_usd': price_usd_avia,
            'price_rub': price_rub_avia,
            'route': 'АВИА',
            'delivery_time_days': delivery_avia or 30
        })
    
    return offers
```

---

## ✅ КОНТРОЛЬ КАЧЕСТВА

### Метрики после парсинга:

1. **Успешность:** ≥ 70%
2. **Товары с изображениями:** ≥ 85%
3. **Предложений на товар:** ≥ 2.0 (учитывая многострочность и маршруты)
4. **Изображений на товар:** ≥ 3.0

### Текущие результаты (8,573 товара):
- ✅ Товары с изображениями: **93.0%**
- ✅ Предложений на товар: **2.80**
- ✅ Изображений на товар: **3.40**

---

## 🐛 ОСОБЫЕ СЛУЧАИ

### 1. **Столбец "Итого, руб"**
- Если в таблице есть столбец "Итого" → **пропускаем его**
- Не используем для парсинга, но учитываем при валидации структуры

### 2. **Образцы**
- Иногда тираж = "Образец" (вместо числа)
- Парсим как `quantity = 1` с route = "Образец"

### 3. **Пустые цены**
- Если `price_usd = 0` и `price_rub = 0` → **не создаем предложение**
- Логируем для отчета

### 4. **Дубликаты**
- Перед сохранением проверяем: существует ли товар с таким именем для этого проекта
- Если да → **пропускаем** (не перезаписываем)

---

## 📝 ЛОГИРОВАНИЕ

### Уровни логов:

```python
logger.info(f"📋 {i}/{total}: Парсинг {filename}")
logger.info(f"   ✅ Товары: {products} | Предложения: {offers} | Изображения: {images}")
logger.warning(f"   ⚠️  No products found")
logger.error(f"   ❌ Ошибка: {error_message}")
```

### Статистика в конце:
```
✅ Успешно: 198/272 (72.8%)
❌ Ошибки: 74
📦 Товары: 759
💰 Предложения: 2,466
🖼️  Изображения: 5,868
```

---

## 🔄 ОБНОВЛЕНИЕ ДАННЫХ

### Правила:
1. **НЕ ПЕРЕЗАПИСЫВАЕМ** уже спарсенные проекты (проверяем `parsing_status = 'completed'`)
2. **НЕ ДУБЛИРУЕМ** товары (проверяем по `project_id` + `name`)
3. **ЛОГИРУЕМ** все пропуски и ошибки

---

## 📦 ФАЙЛЫ ПРОЕКТА

```
cp_parser/
├── parse_validated_272_files.py       # Основной парсер
├── src/
│   └── structure_parser.py            # Валидация структуры
├── database/
│   ├── models.py                      # SQLAlchemy модели
│   └── postgresql_manager.py          # Подключение к PostgreSQL
├── storage/
│   ├── excel_files/                   # Исходные .xlsx файлы
│   └── images/                        # Извлеченные изображения
└── PARSING_RULES.md                   # ЭТО ФАЙЛ
```

---

## 🎯 ИТОГ

**Главное правило:**
> Один товар = одна запись в `products`, но может иметь **НЕСКОЛЬКО** строк в исходной таблице (многострочность), **НЕСКОЛЬКО** price_offers (ЖД/АВИА + разные тиражи) и **НЕСКОЛЬКО** изображений.

**Парсим:**
- ✅ Многострочные товары (пустое название, но есть тираж)
- ✅ Несколько маршрутов (ЖД и АВИА) из одной строки
- ✅ Изображения из blob данных Excel
- ✅ Все варианты тиражей (`1000`, `300-500`, `5 000 шт`)

---

*Последнее обновление: 08.10.2025*








## 🎯 СТРУКТУРА EXCEL ФАЙЛОВ

### Базовая структура таблицы:

```
| A      | B           | C                | D         | E      | F        | G         | H       | I        | J         | K       |
|--------|-------------|------------------|-----------|--------|----------|-----------|---------|----------|-----------|---------|
| [Фото] | Наименование| Характеристики   | Кастом    | Тираж  | USD ЖД   | RUB ЖД    | Срок ЖД | USD АВИА | RUB АВИА  | Срок    |
| [IMG]  | Товар 1     | Описание...      | Дизайн... | 1000   | 5.50     | 500       | 60      | 6.00     | 550       | 30      |
|        |             |                  |           | 3000   | 5.00     | 450       | 60      | 5.50     | 500       | 30      |
| [IMG]  | Товар 2     | Другое описание  | ...       | 500    | 10.00    | 900       | 55      | 11.00    | 1000      | 25      |
```

---

## 🔧 ПРАВИЛА ПАРСИНГА

### 1. **Начало данных**
- Данные начинаются с **строки 5** (пропускаем заголовки)
- Парсинг до строки **500** максимум

### 2. **Идентификация товара**
- **Столбец B (2)** = Название товара
- Минимальная длина названия: **3 символа**
- Пропускаем строки с заголовками: `фото`, `наименование`, `название`, `характеристики`, `тираж`, `цена`

### 3. **Многострочные товары (КРИТИЧЕСКИ ВАЖНО!)**
- Один товар может занимать **несколько строк** с разными тиражами
- **Алгоритм:**
  1. Читаем название товара из столбца B
  2. Парсим предложения из текущей строки
  3. **Проверяем следующие строки:**
     - Если название ПУСТОЕ, но есть тираж (столбец E) → это дополнительное предложение для ТОГО ЖЕ товара
     - Добавляем все предложения к одному товару
  4. Прекращаем, когда встречаем новое название или пустую строку без тиража

**Пример:**
```
| B           | E      | F        | ... |
|-------------|--------|----------|-----|
| Кружка      | 1000   | 5.50     | ... | ← Товар 1, предложение 1
|             | 3000   | 5.00     | ... | ← Товар 1, предложение 2 (название пустое!)
|             | 5000   | 4.80     | ... | ← Товар 1, предложение 3 (название пустое!)
| Блокнот     | 500    | 2.00     | ... | ← Товар 2, предложение 1
```

### 4. **Поля товара**

| Поле          | Столбец | Тип    | Обязательное | Обработка                     |
|---------------|---------|--------|--------------|-------------------------------|
| name          | B (2)   | String | ✅           | `str(value).strip()`          |
| description   | C (3)   | String | ❌           | `str(value)` если есть        |
| custom_field  | D (4)   | String | ❌           | `str(value)` если есть        |

### 5. **Ценовые предложения (Price Offers)**

#### 📦 **Маршрут ЖД (Железная дорога)**
| Поле                | Столбец | Тип   | Обработка                                  |
|---------------------|---------|-------|-------------------------------------------|
| quantity            | E (5)   | Int   | Если есть `-` → берем первое число        |
| price_usd           | F (6)   | Float | `replace(',', '.')`                       |
| price_rub           | G (7)   | Float | `replace(',', '.').replace(' ', '')`      |
| delivery_time_days  | H (8)   | Int   | Извлекаем цифры                           |
| route               | -       | String| **"ЖД"**                                  |

#### ✈️ **Маршрут АВИА**
| Поле                | Столбец | Тип   | Обработка                                  |
|---------------------|---------|-------|-------------------------------------------|
| quantity            | E (5)   | Int   | **ТОТ ЖЕ** тираж, что и для ЖД           |
| price_usd           | I (9)   | Float | `replace(',', '.')`                       |
| price_rub           | J (10)  | Float | `replace(',', '.').replace(' ', '')`      |
| delivery_time_days  | K (11)  | Int   | Извлекаем цифры                           |
| route               | -       | String| **"АВИА"**                                |

#### ⚠️ **ВАЖНО:**
- Если в строке есть тираж (E) → создаем **ДВА** предложения: ЖД + АВИА (если цены есть)
- Предложение создается только если есть `price_usd` ИЛИ `price_rub`
- Если нет цен ЖД/АВИА → пропускаем это предложение

### 6. **Обработка тиража (Quantity)**

**Варианты формата:**
- `1000` → `1000`
- `300-500` → `300` (берем первое число)
- `5 000` → `5000` (убираем пробелы)
- `10000шт` → `10000` (извлекаем только цифры)

**Код:**
```python
qty_str = str(cell_value).strip()
if '-' in qty_str:
    qty_str = qty_str.split('-')[0].strip()
qty = int(''.join(filter(str.isdigit, qty_str)))
```

### 7. **Изображения (Product Images)**

#### 📷 **Извлечение из Excel**
- Изображения хранятся как **blob данные** внутри `.xlsx` файлов
- Используем `openpyxl` с `data_only=False` для извлечения
- Доступ через `worksheet._images`

#### 📁 **Формат имени файла:**
```
{table_id}_{cell_position}_{hash}.png
```

**Пример:**
```
11Zs0Urnzve7URBBwgWsonjjgOWc414YP_Onkxo0AMRo_N7_474edece.png
```

Где:
- `11Zs0Urnzve7URBBwgWsonjjgOWc414YP_Onkxo0AMRo` = Google Sheets Table ID
- `N7` = Позиция ячейки (столбец N, строка 7)
- `474edece` = MD5 hash изображения (первые 8 символов)

#### 🔗 **Привязка к товарам:**
- Изображения привязываются по **диапазону строк**: ±2 от строки товара
- Если товар в строке 10, ищем изображения в строках 8-12
- **Несколько изображений** на товар → сохраняем все

#### 💾 **Поля в БД:**
| Поле          | Тип    | Описание                              |
|---------------|--------|---------------------------------------|
| product_id    | Int    | FK к таблице `products`               |
| table_id      | String | ID Google Sheets таблицы              |
| image_filename| String | Имя файла (см. формат выше)           |
| cell_position | String | Позиция в таблице (A1, B5, N7...)     |
| row_number    | Int    | Номер строки                          |
| column_number | Int    | Номер столбца                         |

---

## 📊 ВАЛИДАЦИЯ СТРУКТУРЫ

### Минимальные требования:

1. ✅ **Обязательные столбцы** (для валидации):
   - Фото (A)
   - Наименование (B)
   - Тираж (E)
   - Цены (F, G, I, J - хотя бы одна)
   - Срок доставки (H, K)

2. ✅ **Проверка заголовков:**
   - Ищем ключевые слова: `фото`, `наименование`, `тираж`, `цена`, `доставка`
   - Проверяем наличие маршрутов: `жд`, `авиа`, `ж/д`, `авто`

3. ✅ **Валидация данных:**
   - `quantity > 0`
   - `price_usd > 0` ИЛИ `price_rub > 0`
   - `delivery_time_days >= 0`

---

## 🗄️ СХЕМА БАЗЫ ДАННЫХ

### **Таблица: `projects`**
```sql
id                  SERIAL PRIMARY KEY
project_name        VARCHAR(500)
table_id            VARCHAR(200)  -- Google Sheets ID
google_sheets_url   TEXT
parsing_status      VARCHAR(50)   -- 'pending', 'completed', 'error'
parsing_errors      TEXT
parsed_at           TIMESTAMP
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### **Таблица: `products`**
```sql
id                  SERIAL PRIMARY KEY
project_id          INTEGER FK → projects.id
table_id            VARCHAR(200)
name                VARCHAR(500)  -- Столбец B
description         TEXT          -- Столбец C
custom_field        TEXT          -- Столбец D (дизайн)
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### **Таблица: `price_offers`**
```sql
id                  SERIAL PRIMARY KEY
product_id          INTEGER FK → products.id
quantity            INTEGER       -- Столбец E
price_usd           DECIMAL(10,2) -- Столбцы F/I
price_rub           DECIMAL(10,2) -- Столбцы G/J
route               VARCHAR(50)   -- "ЖД" или "АВИА"
delivery_time_days  INTEGER       -- Столбцы H/K
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

### **Таблица: `product_images`**
```sql
id                  SERIAL PRIMARY KEY
product_id          INTEGER FK → products.id
table_id            VARCHAR(200)
image_filename      VARCHAR(500)
cell_position       VARCHAR(10)   -- "A1", "N7"
row_number          INTEGER
column_number       INTEGER
created_at          TIMESTAMP
updated_at          TIMESTAMP
```

---

## 🚀 ПРОЦЕСС ПАРСИНГА

### Шаг 1: Загрузка файла
```python
# Для изображений (БЕЗ data_only)
workbook_images = load_workbook(file_path, data_only=False)

# Для данных (С data_only для вычисленных значений)
workbook_data = load_workbook(file_path, data_only=True)
```

### Шаг 2: Извлечение изображений
```python
images_by_row = {}  # {row_idx: [{'filename': ..., 'cell_position': ..., ...}]}

if hasattr(worksheet_images, '_images'):
    for img in worksheet_images._images:
        row = img.anchor._from.row + 1
        col = img.anchor._from.col + 1
        img_data = save_image_from_excel(img, table_id, row, col)
        images_by_row[row].append(img_data)
```

### Шаг 3: Парсинг товаров
```python
skip_rows = set()  # Уже обработанные строки

for row_idx in range(5, 500):
    if row_idx in skip_rows:
        continue
    
    name = worksheet_data.cell(row_idx, 2).value  # Столбец B
    
    if not name or len(name) < 3:
        continue
    
    # Парсим предложения из текущей строки
    offers = parse_offers_from_row(row_idx)
    
    # Проверяем следующие строки на дополнительные предложения
    check_row = row_idx + 1
    while check_row < 500:
        next_name = worksheet_data.cell(check_row, 2).value
        next_qty = worksheet_data.cell(check_row, 5).value
        
        if next_name and len(str(next_name)) >= 3:
            break  # Новый товар
        
        if next_qty:
            # Дополнительное предложение для ТОГО ЖЕ товара
            additional_offers = parse_offers_from_row(check_row)
            offers.extend(additional_offers)
            skip_rows.add(check_row)
            check_row += 1
        else:
            break
    
    # Ищем изображения (±2 строки)
    product_images = []
    for check_row in range(max(1, row_idx - 2), row_idx + 3):
        if check_row in images_by_row:
            product_images.extend(images_by_row[check_row])
    
    # Сохраняем товар
    save_product(name, description, custom_field, offers, product_images)
```

### Шаг 4: Парсинг предложений
```python
def parse_offers_from_row(row_idx):
    offers = []
    
    # Тираж
    qty_cell = worksheet_data.cell(row_idx, 5)
    if not qty_cell.value:
        return offers
    
    qty_str = str(qty_cell.value).strip()
    if '-' in qty_str:
        qty_str = qty_str.split('-')[0].strip()
    qty = int(''.join(filter(str.isdigit, qty_str)))
    
    # ЖД маршрут
    price_usd_jd = parse_float(worksheet_data.cell(row_idx, 6).value)
    price_rub_jd = parse_float(worksheet_data.cell(row_idx, 7).value)
    delivery_jd = parse_int(worksheet_data.cell(row_idx, 8).value)
    
    if price_usd_jd or price_rub_jd:
        offers.append({
            'quantity': qty,
            'price_usd': price_usd_jd,
            'price_rub': price_rub_jd,
            'route': 'ЖД',
            'delivery_time_days': delivery_jd or 60
        })
    
    # АВИА маршрут
    price_usd_avia = parse_float(worksheet_data.cell(row_idx, 9).value)
    price_rub_avia = parse_float(worksheet_data.cell(row_idx, 10).value)
    delivery_avia = parse_int(worksheet_data.cell(row_idx, 11).value)
    
    if price_usd_avia or price_rub_avia:
        offers.append({
            'quantity': qty,
            'price_usd': price_usd_avia,
            'price_rub': price_rub_avia,
            'route': 'АВИА',
            'delivery_time_days': delivery_avia or 30
        })
    
    return offers
```

---

## ✅ КОНТРОЛЬ КАЧЕСТВА

### Метрики после парсинга:

1. **Успешность:** ≥ 70%
2. **Товары с изображениями:** ≥ 85%
3. **Предложений на товар:** ≥ 2.0 (учитывая многострочность и маршруты)
4. **Изображений на товар:** ≥ 3.0

### Текущие результаты (8,573 товара):
- ✅ Товары с изображениями: **93.0%**
- ✅ Предложений на товар: **2.80**
- ✅ Изображений на товар: **3.40**

---

## 🐛 ОСОБЫЕ СЛУЧАИ

### 1. **Столбец "Итого, руб"**
- Если в таблице есть столбец "Итого" → **пропускаем его**
- Не используем для парсинга, но учитываем при валидации структуры

### 2. **Образцы**
- Иногда тираж = "Образец" (вместо числа)
- Парсим как `quantity = 1` с route = "Образец"

### 3. **Пустые цены**
- Если `price_usd = 0` и `price_rub = 0` → **не создаем предложение**
- Логируем для отчета

### 4. **Дубликаты**
- Перед сохранением проверяем: существует ли товар с таким именем для этого проекта
- Если да → **пропускаем** (не перезаписываем)

---

## 📝 ЛОГИРОВАНИЕ

### Уровни логов:

```python
logger.info(f"📋 {i}/{total}: Парсинг {filename}")
logger.info(f"   ✅ Товары: {products} | Предложения: {offers} | Изображения: {images}")
logger.warning(f"   ⚠️  No products found")
logger.error(f"   ❌ Ошибка: {error_message}")
```

### Статистика в конце:
```
✅ Успешно: 198/272 (72.8%)
❌ Ошибки: 74
📦 Товары: 759
💰 Предложения: 2,466
🖼️  Изображения: 5,868
```

---

## 🔄 ОБНОВЛЕНИЕ ДАННЫХ

### Правила:
1. **НЕ ПЕРЕЗАПИСЫВАЕМ** уже спарсенные проекты (проверяем `parsing_status = 'completed'`)
2. **НЕ ДУБЛИРУЕМ** товары (проверяем по `project_id` + `name`)
3. **ЛОГИРУЕМ** все пропуски и ошибки

---

## 📦 ФАЙЛЫ ПРОЕКТА

```
cp_parser/
├── parse_validated_272_files.py       # Основной парсер
├── src/
│   └── structure_parser.py            # Валидация структуры
├── database/
│   ├── models.py                      # SQLAlchemy модели
│   └── postgresql_manager.py          # Подключение к PostgreSQL
├── storage/
│   ├── excel_files/                   # Исходные .xlsx файлы
│   └── images/                        # Извлеченные изображения
└── PARSING_RULES.md                   # ЭТО ФАЙЛ
```

---

## 🎯 ИТОГ

**Главное правило:**
> Один товар = одна запись в `products`, но может иметь **НЕСКОЛЬКО** строк в исходной таблице (многострочность), **НЕСКОЛЬКО** price_offers (ЖД/АВИА + разные тиражи) и **НЕСКОЛЬКО** изображений.

**Парсим:**
- ✅ Многострочные товары (пустое название, но есть тираж)
- ✅ Несколько маршрутов (ЖД и АВИА) из одной строки
- ✅ Изображения из blob данных Excel
- ✅ Все варианты тиражей (`1000`, `300-500`, `5 000 шт`)

---

*Последнее обновление: 08.10.2025*











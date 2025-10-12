# 📋 ПЛАН ПАРСИНГА ШАБЛОНА 5

**Дата:** 09.10.2025  
**Проектов:** 230

---

## 🎯 КЛЮЧЕВЫЕ ОТЛИЧИЯ ОТ ШАБЛОНА 4

### 1️⃣ Маршруты доставки

**Шаблон 4:**
```
Тираж: 1000 шт
├── Highway ЖД:  5.50$ / 500₽ / 45 дней
└── Highway Avia: 6.20$ / 580₽ / 15 дней

→ Результат: 2 price_offers
```

**Шаблон 5:**
```
Тираж: 2000 шт
└── Единая цена: 0.49$ / 47₽ / 15-20 дней

→ Результат: 1 price_offer (без delivery_route)
```

### 2️⃣ Структура колонок

| Поле | Шаблон 4 | Шаблон 5 | Куда парсим |
|------|----------|----------|-------------|
| Фото | A | A | `product_images` (is_main=true) |
| Наименование | B | B | `products.name` |
| Описание | C | C | `products.custom_field` |
| Кастом/Дизайн | D | - | (в Шаблоне 5 в описании) |
| Тираж | E | D | `price_offers.quantity` |
| Цена USD | F,I | E | `price_offers.price_usd` |
| Цена RUB | G,J | F | `price_offers.price_rub` |
| Срок | H,K | G | `price_offers.delivery_time` |
| Образец цена | N | H | `products.sample_price` |
| Образец срок | P | I | `products.sample_delivery_time` |
| Доп. фото | Q | J | `product_images` (is_main=false) |

### 3️⃣ Позиция заголовков

```
Шаблон 4:
Строка 1: (служебная)
Строка 2: (служебная)
Строка 3: (служебная)
Строка 4: [ЗАГОЛОВКИ]
Строка 5: [ДАННЫЕ]

Шаблон 5:
Строка 1: Менеджер, примечания
Строка 2: [ЗАГОЛОВКИ]
Строка 3: [ДАННЫЕ]
```

---

## 📝 ПРИМЕРЫ РЕЗУЛЬТАТА ПАРСИНГА

### Пример 1: Простой товар

**Excel (Шаблон 5):**
```
A: [фото]
B: Светоотражающиеся шнурки
C: Размер: 9х120мм, Материал: Полиэстер
D: 2000
   4000
E: 0,49
   0,75
   
   0,46
   0,71
F: 47,16 ₽
   73,37 ₽
   
   43,97 ₽
   70,17 ₽
G: 15-20 кд
   
   14-16 кд
H: -
I: -
```

**Результат в БД:**

**products:**
```json
{
  "id": 15001,
  "project_id": 1912,
  "name": "Светоотражающиеся шнурки",
  "custom_field": "Размер: 9х120мм, Материал: Полиэстер",
  "sample_price": null,
  "sample_delivery_time": null
}
```

**price_offers:** (4 записи)
```json
[
  {
    "product_id": 15001,
    "quantity": 2000,
    "price_usd": 0.49,
    "price_rub": 47.16,
    "delivery_time": "20 дней",
    "delivery_route": null
  },
  {
    "product_id": 15001,
    "quantity": 4000,
    "price_usd": 0.75,
    "price_rub": 73.37,
    "delivery_time": "20 дней",
    "delivery_route": null
  },
  {
    "product_id": 15001,
    "quantity": 2000,
    "price_usd": 0.46,
    "price_rub": 43.97,
    "delivery_time": "16 дней",
    "delivery_route": null
  },
  {
    "product_id": 15001,
    "quantity": 4000,
    "price_usd": 0.71,
    "price_rub": 70.17,
    "delivery_time": "16 дней",
    "delivery_route": null
  }
]
```

**product_images:**
```json
{
  "product_id": 15001,
  "cell_position": "A3",
  "is_main_image": true,
  "image_url": "https://ru1.storage.beget.cloud/.../image.png"
}
```

---

### Пример 2: Товар с образцом

**Excel (Шаблон 5):**
```
A: [фото]
B: Песочные часы
C: Материал: пластик, стекло, акрил. Размер: 10x5 см
D: 150
E: 4,03
   
   4,57
F: 386,98
   
   440,78
G: 40-45 календ.дней
H: 7900 руб
   
   8100 руб
I: 20-22 календ.дня
```

**Результат в БД:**

**products:**
```json
{
  "id": 15002,
  "project_id": 1944,
  "name": "Песочные часы",
  "custom_field": "Материал: пластик, стекло, акрил. Размер: 10x5 см",
  "sample_price": "7900 руб / 8100 руб",
  "sample_delivery_time": 22
}
```

**price_offers:** (2 записи)
```json
[
  {
    "product_id": 15002,
    "quantity": 150,
    "price_usd": 4.03,
    "price_rub": 386.98,
    "delivery_time": "45 дней",
    "delivery_route": null
  },
  {
    "product_id": 15002,
    "quantity": 150,
    "price_usd": 4.57,
    "price_rub": 440.78,
    "delivery_time": "45 дней",
    "delivery_route": null
  }
]
```

---

### Пример 3: Multi-row товар (с доп. опциями)

**Excel (Шаблон 5):**
```
Строка 3:
A: [фото]
B: Полотенце
C: 70*140см, вес 210г-215г, 100% микрофибра
D: 164
E: 8.37
F: 771.75
G: 45-50кд
H: 7 539 ₽ - без печати на сумке
I: 20-22кд

Строка 4: (дополнительная опция)
A: (пусто)
B: (пусто)
C: +Нанесение: печать на сумке шелкография
D: (пусто)
E: 8.67
F: 799.3
G: (пусто)
H: 12 748 ₽ - с печатью до 2-х цветов
I: (пусто)
```

**Результат в БД:**

**products:**
```json
{
  "id": 15003,
  "project_id": 2115,
  "name": "Полотенце",
  "custom_field": "70*140см, вес 210г-215г, 100% микрофибра\n+Нанесение: печать на сумке шелкография",
  "sample_price": "7539₽ / 12748₽",
  "sample_delivery_time": 22
}
```

**price_offers:** (2 записи - базовая + с печатью)
```json
[
  {
    "product_id": 15003,
    "quantity": 164,
    "price_usd": 8.37,
    "price_rub": 771.75,
    "delivery_time": "50 дней",
    "delivery_route": null
  },
  {
    "product_id": 15003,
    "quantity": 164,
    "price_usd": 8.67,
    "price_rub": 799.30,
    "delivery_time": "50 дней",
    "delivery_route": null
  }
]
```

---

## 🔄 АЛГОРИТМ ПАРСИНГА

### Шаг 1: Инициализация
```python
DATA_START_ROW = 3  # Строка 2 = заголовки, строка 3 = данные
COLUMNS = {
    'photo': 'A',
    'name': 'B',
    'description': 'C',
    'quantity': 'D',
    'price_usd': 'E',
    'price_rub': 'F',
    'delivery_time': 'G',
    'sample_price': 'H',
    'sample_delivery': 'I',
    'extra_photo': 'J'
}
```

### Шаг 2: Определение multi-row товаров
```python
def is_new_product(row):
    """
    Новый товар если есть наименование в колонке B
    """
    return bool(row['name'])

def is_additional_row(row):
    """
    Дополнительная строка если:
    - НЕТ наименования
    - ЕСТЬ цены или описание
    """
    return not row['name'] and (row['price_usd'] or row['description'])
```

### Шаг 3: Парсинг количества и цен
```python
def parse_quantity_and_prices(quantity_cell, usd_cell, rub_cell, delivery_cell):
    """
    Парсим множественные значения из ячеек
    
    Пример:
    quantity_cell = "2000\n4000"
    usd_cell = "0.49\n0.75\n\n0.46\n0.71"
    
    Результат:
    [
      (2000, 0.49, 47.16, "20 дней"),
      (4000, 0.75, 73.37, "20 дней"),
      (2000, 0.46, 43.97, "16 дней"),
      (4000, 0.71, 70.17, "16 дней")
    ]
    """
    quantities = parse_multiline(quantity_cell)
    usd_prices = parse_multiline(usd_cell)
    rub_prices = parse_multiline(rub_cell)
    deliveries = parse_multiline(delivery_cell)
    
    # Группируем по парам
    offers = []
    # ... логика группировки
    
    return offers
```

### Шаг 4: Парсинг образца
```python
def parse_sample(sample_price_cell, sample_delivery_cell):
    """
    sample_price_cell = "7900 руб\n8100 руб"
    sample_delivery_cell = "20-22 календ.дня"
    
    Результат:
    {
      'price': "7900 руб / 8100 руб",
      'delivery_time': 22  # максимальное значение
    }
    """
    # Объединяем цены через " / "
    prices = [p.strip() for p in sample_price_cell.split('\n') if p.strip()]
    price_str = " / ".join(prices) if prices else None
    
    # Парсим срок: "20-22 дня" → 22
    delivery_time = parse_max_days(sample_delivery_cell)
    
    return {'price': price_str, 'delivery_time': delivery_time}
```

### Шаг 5: Извлечение изображений
```python
def extract_images(ws, row_num):
    """
    Извлекаем:
    - Главное фото из A{row_num}
    - Доп. фото из J{row_num} (может быть несколько)
    """
    images = []
    
    # Главное фото
    main_image = extract_image_from_cell(ws, row_num, 'A')
    if main_image:
        images.append({
            'data': main_image,
            'filename': f'{table_id}_A{row_num}_{hash}.png',
            'is_main': True
        })
    
    # Доп. фото (может быть несколько в одной ячейке)
    extra_images = extract_all_images_from_cell(ws, row_num, 'J')
    for idx, img_data in enumerate(extra_images, 1):
        images.append({
            'data': img_data,
            'filename': f'{table_id}_J{row_num}_{idx}_{hash}.png',
            'is_main': False
        })
    
    return images
```

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### На 230 проектов Шаблона 5:

```
Проектов:      230
├── Товаров:   ~1,000-1,500
├── Офферов:   ~3,000-5,000  (меньше чем Шаблон 4, т.к. нет разделения ЖД/Авиа)
└── Изображений: ~2,000-3,000
```

### Сравнение с Шаблоном 4:

| Метрика | Шаблон 4 (277 проектов) | Шаблон 5 (230 проектов) |
|---------|--------------------------|--------------------------|
| Товаров | 1,156 (4.2 на проект) | ~1,150 (5.0 на проект) |
| Офферов | 3,298 (2.9 на товар) | ~2,500 (2.2 на товар) |
| Изображений | 2,560 (2.2 на товар) | ~2,300 (2.0 на товар) |

**Почему меньше офферов:**
- Шаблон 4: каждый тираж = 2 оффера (ЖД + Авиа)
- Шаблон 5: каждый тираж = 1 оффер (единая цена)

---

## 🚀 ПЛАН РАЗРАБОТКИ

### Этап 1: Подготовка (30 мин)
- ✅ Документация создана (TEMPLATE_5_STRUCTURE.md)
- ⏳ Создать парсер `parse_template_5.py`
- ⏳ Скопировать базу из `parse_template_4.py`
- ⏳ Адаптировать под Шаблон 5

### Этап 2: Тестирование (1-2 часа)
- Тест на 5 проектах
- Проверка корректности данных
- Исправление ошибок

### Этап 3: Полный парсинг (2-3 часа)
- Парсинг всех 230 проектов
- Мониторинг ошибок
- Загрузка изображений на S3

### Этап 4: Верификация (30 мин)
- Проверка данных в Railway БД
- Сравнение с ожидаемыми показателями
- Создание отчета

---

## ⚠️ ОТЛИЧИЯ В КОДЕ

### parse_template_4.py → parse_template_5.py

**1. Константы:**
```python
# Было (Шаблон 4):
DATA_START_ROW = 5
COLUMNS = {..., 'custom_field': 'D', 'quantity': 'E', ...}

# Стало (Шаблон 5):
DATA_START_ROW = 3
COLUMNS = {..., 'quantity': 'D', ...}  # нет custom_field
```

**2. Парсинг офферов:**
```python
# Было (Шаблон 4): 2 оффера на тираж
offers.append({
    'quantity': qty,
    'price_usd': jd_usd,
    'price_rub': jd_rub,
    'delivery_route': 'highway_jd'
})
offers.append({
    'quantity': qty,
    'price_usd': avia_usd,
    'price_rub': avia_rub,
    'delivery_route': 'highway_avia'
})

# Стало (Шаблон 5): 1 оффер на тираж
offers.append({
    'quantity': qty,
    'price_usd': usd,
    'price_rub': rub,
    'delivery_route': None  # нет маршрута
})
```

**3. custom_field:**
```python
# Было (Шаблон 4):
custom_field = self._get_cell_value(ws_data, row, 'custom_field')

# Стало (Шаблон 5):
custom_field = self._get_cell_value(ws_data, row, 'description')
# дизайн уже внутри описания
```

---

**Готово к реализации!** 🚀

Хочешь начать создавать парсер для Шаблона 5?






**Дата:** 09.10.2025  
**Проектов:** 230

---

## 🎯 КЛЮЧЕВЫЕ ОТЛИЧИЯ ОТ ШАБЛОНА 4

### 1️⃣ Маршруты доставки

**Шаблон 4:**
```
Тираж: 1000 шт
├── Highway ЖД:  5.50$ / 500₽ / 45 дней
└── Highway Avia: 6.20$ / 580₽ / 15 дней

→ Результат: 2 price_offers
```

**Шаблон 5:**
```
Тираж: 2000 шт
└── Единая цена: 0.49$ / 47₽ / 15-20 дней

→ Результат: 1 price_offer (без delivery_route)
```

### 2️⃣ Структура колонок

| Поле | Шаблон 4 | Шаблон 5 | Куда парсим |
|------|----------|----------|-------------|
| Фото | A | A | `product_images` (is_main=true) |
| Наименование | B | B | `products.name` |
| Описание | C | C | `products.custom_field` |
| Кастом/Дизайн | D | - | (в Шаблоне 5 в описании) |
| Тираж | E | D | `price_offers.quantity` |
| Цена USD | F,I | E | `price_offers.price_usd` |
| Цена RUB | G,J | F | `price_offers.price_rub` |
| Срок | H,K | G | `price_offers.delivery_time` |
| Образец цена | N | H | `products.sample_price` |
| Образец срок | P | I | `products.sample_delivery_time` |
| Доп. фото | Q | J | `product_images` (is_main=false) |

### 3️⃣ Позиция заголовков

```
Шаблон 4:
Строка 1: (служебная)
Строка 2: (служебная)
Строка 3: (служебная)
Строка 4: [ЗАГОЛОВКИ]
Строка 5: [ДАННЫЕ]

Шаблон 5:
Строка 1: Менеджер, примечания
Строка 2: [ЗАГОЛОВКИ]
Строка 3: [ДАННЫЕ]
```

---

## 📝 ПРИМЕРЫ РЕЗУЛЬТАТА ПАРСИНГА

### Пример 1: Простой товар

**Excel (Шаблон 5):**
```
A: [фото]
B: Светоотражающиеся шнурки
C: Размер: 9х120мм, Материал: Полиэстер
D: 2000
   4000
E: 0,49
   0,75
   
   0,46
   0,71
F: 47,16 ₽
   73,37 ₽
   
   43,97 ₽
   70,17 ₽
G: 15-20 кд
   
   14-16 кд
H: -
I: -
```

**Результат в БД:**

**products:**
```json
{
  "id": 15001,
  "project_id": 1912,
  "name": "Светоотражающиеся шнурки",
  "custom_field": "Размер: 9х120мм, Материал: Полиэстер",
  "sample_price": null,
  "sample_delivery_time": null
}
```

**price_offers:** (4 записи)
```json
[
  {
    "product_id": 15001,
    "quantity": 2000,
    "price_usd": 0.49,
    "price_rub": 47.16,
    "delivery_time": "20 дней",
    "delivery_route": null
  },
  {
    "product_id": 15001,
    "quantity": 4000,
    "price_usd": 0.75,
    "price_rub": 73.37,
    "delivery_time": "20 дней",
    "delivery_route": null
  },
  {
    "product_id": 15001,
    "quantity": 2000,
    "price_usd": 0.46,
    "price_rub": 43.97,
    "delivery_time": "16 дней",
    "delivery_route": null
  },
  {
    "product_id": 15001,
    "quantity": 4000,
    "price_usd": 0.71,
    "price_rub": 70.17,
    "delivery_time": "16 дней",
    "delivery_route": null
  }
]
```

**product_images:**
```json
{
  "product_id": 15001,
  "cell_position": "A3",
  "is_main_image": true,
  "image_url": "https://ru1.storage.beget.cloud/.../image.png"
}
```

---

### Пример 2: Товар с образцом

**Excel (Шаблон 5):**
```
A: [фото]
B: Песочные часы
C: Материал: пластик, стекло, акрил. Размер: 10x5 см
D: 150
E: 4,03
   
   4,57
F: 386,98
   
   440,78
G: 40-45 календ.дней
H: 7900 руб
   
   8100 руб
I: 20-22 календ.дня
```

**Результат в БД:**

**products:**
```json
{
  "id": 15002,
  "project_id": 1944,
  "name": "Песочные часы",
  "custom_field": "Материал: пластик, стекло, акрил. Размер: 10x5 см",
  "sample_price": "7900 руб / 8100 руб",
  "sample_delivery_time": 22
}
```

**price_offers:** (2 записи)
```json
[
  {
    "product_id": 15002,
    "quantity": 150,
    "price_usd": 4.03,
    "price_rub": 386.98,
    "delivery_time": "45 дней",
    "delivery_route": null
  },
  {
    "product_id": 15002,
    "quantity": 150,
    "price_usd": 4.57,
    "price_rub": 440.78,
    "delivery_time": "45 дней",
    "delivery_route": null
  }
]
```

---

### Пример 3: Multi-row товар (с доп. опциями)

**Excel (Шаблон 5):**
```
Строка 3:
A: [фото]
B: Полотенце
C: 70*140см, вес 210г-215г, 100% микрофибра
D: 164
E: 8.37
F: 771.75
G: 45-50кд
H: 7 539 ₽ - без печати на сумке
I: 20-22кд

Строка 4: (дополнительная опция)
A: (пусто)
B: (пусто)
C: +Нанесение: печать на сумке шелкография
D: (пусто)
E: 8.67
F: 799.3
G: (пусто)
H: 12 748 ₽ - с печатью до 2-х цветов
I: (пусто)
```

**Результат в БД:**

**products:**
```json
{
  "id": 15003,
  "project_id": 2115,
  "name": "Полотенце",
  "custom_field": "70*140см, вес 210г-215г, 100% микрофибра\n+Нанесение: печать на сумке шелкография",
  "sample_price": "7539₽ / 12748₽",
  "sample_delivery_time": 22
}
```

**price_offers:** (2 записи - базовая + с печатью)
```json
[
  {
    "product_id": 15003,
    "quantity": 164,
    "price_usd": 8.37,
    "price_rub": 771.75,
    "delivery_time": "50 дней",
    "delivery_route": null
  },
  {
    "product_id": 15003,
    "quantity": 164,
    "price_usd": 8.67,
    "price_rub": 799.30,
    "delivery_time": "50 дней",
    "delivery_route": null
  }
]
```

---

## 🔄 АЛГОРИТМ ПАРСИНГА

### Шаг 1: Инициализация
```python
DATA_START_ROW = 3  # Строка 2 = заголовки, строка 3 = данные
COLUMNS = {
    'photo': 'A',
    'name': 'B',
    'description': 'C',
    'quantity': 'D',
    'price_usd': 'E',
    'price_rub': 'F',
    'delivery_time': 'G',
    'sample_price': 'H',
    'sample_delivery': 'I',
    'extra_photo': 'J'
}
```

### Шаг 2: Определение multi-row товаров
```python
def is_new_product(row):
    """
    Новый товар если есть наименование в колонке B
    """
    return bool(row['name'])

def is_additional_row(row):
    """
    Дополнительная строка если:
    - НЕТ наименования
    - ЕСТЬ цены или описание
    """
    return not row['name'] and (row['price_usd'] or row['description'])
```

### Шаг 3: Парсинг количества и цен
```python
def parse_quantity_and_prices(quantity_cell, usd_cell, rub_cell, delivery_cell):
    """
    Парсим множественные значения из ячеек
    
    Пример:
    quantity_cell = "2000\n4000"
    usd_cell = "0.49\n0.75\n\n0.46\n0.71"
    
    Результат:
    [
      (2000, 0.49, 47.16, "20 дней"),
      (4000, 0.75, 73.37, "20 дней"),
      (2000, 0.46, 43.97, "16 дней"),
      (4000, 0.71, 70.17, "16 дней")
    ]
    """
    quantities = parse_multiline(quantity_cell)
    usd_prices = parse_multiline(usd_cell)
    rub_prices = parse_multiline(rub_cell)
    deliveries = parse_multiline(delivery_cell)
    
    # Группируем по парам
    offers = []
    # ... логика группировки
    
    return offers
```

### Шаг 4: Парсинг образца
```python
def parse_sample(sample_price_cell, sample_delivery_cell):
    """
    sample_price_cell = "7900 руб\n8100 руб"
    sample_delivery_cell = "20-22 календ.дня"
    
    Результат:
    {
      'price': "7900 руб / 8100 руб",
      'delivery_time': 22  # максимальное значение
    }
    """
    # Объединяем цены через " / "
    prices = [p.strip() for p in sample_price_cell.split('\n') if p.strip()]
    price_str = " / ".join(prices) if prices else None
    
    # Парсим срок: "20-22 дня" → 22
    delivery_time = parse_max_days(sample_delivery_cell)
    
    return {'price': price_str, 'delivery_time': delivery_time}
```

### Шаг 5: Извлечение изображений
```python
def extract_images(ws, row_num):
    """
    Извлекаем:
    - Главное фото из A{row_num}
    - Доп. фото из J{row_num} (может быть несколько)
    """
    images = []
    
    # Главное фото
    main_image = extract_image_from_cell(ws, row_num, 'A')
    if main_image:
        images.append({
            'data': main_image,
            'filename': f'{table_id}_A{row_num}_{hash}.png',
            'is_main': True
        })
    
    # Доп. фото (может быть несколько в одной ячейке)
    extra_images = extract_all_images_from_cell(ws, row_num, 'J')
    for idx, img_data in enumerate(extra_images, 1):
        images.append({
            'data': img_data,
            'filename': f'{table_id}_J{row_num}_{idx}_{hash}.png',
            'is_main': False
        })
    
    return images
```

---

## 📊 ОЖИДАЕМЫЙ РЕЗУЛЬТАТ

### На 230 проектов Шаблона 5:

```
Проектов:      230
├── Товаров:   ~1,000-1,500
├── Офферов:   ~3,000-5,000  (меньше чем Шаблон 4, т.к. нет разделения ЖД/Авиа)
└── Изображений: ~2,000-3,000
```

### Сравнение с Шаблоном 4:

| Метрика | Шаблон 4 (277 проектов) | Шаблон 5 (230 проектов) |
|---------|--------------------------|--------------------------|
| Товаров | 1,156 (4.2 на проект) | ~1,150 (5.0 на проект) |
| Офферов | 3,298 (2.9 на товар) | ~2,500 (2.2 на товар) |
| Изображений | 2,560 (2.2 на товар) | ~2,300 (2.0 на товар) |

**Почему меньше офферов:**
- Шаблон 4: каждый тираж = 2 оффера (ЖД + Авиа)
- Шаблон 5: каждый тираж = 1 оффер (единая цена)

---

## 🚀 ПЛАН РАЗРАБОТКИ

### Этап 1: Подготовка (30 мин)
- ✅ Документация создана (TEMPLATE_5_STRUCTURE.md)
- ⏳ Создать парсер `parse_template_5.py`
- ⏳ Скопировать базу из `parse_template_4.py`
- ⏳ Адаптировать под Шаблон 5

### Этап 2: Тестирование (1-2 часа)
- Тест на 5 проектах
- Проверка корректности данных
- Исправление ошибок

### Этап 3: Полный парсинг (2-3 часа)
- Парсинг всех 230 проектов
- Мониторинг ошибок
- Загрузка изображений на S3

### Этап 4: Верификация (30 мин)
- Проверка данных в Railway БД
- Сравнение с ожидаемыми показателями
- Создание отчета

---

## ⚠️ ОТЛИЧИЯ В КОДЕ

### parse_template_4.py → parse_template_5.py

**1. Константы:**
```python
# Было (Шаблон 4):
DATA_START_ROW = 5
COLUMNS = {..., 'custom_field': 'D', 'quantity': 'E', ...}

# Стало (Шаблон 5):
DATA_START_ROW = 3
COLUMNS = {..., 'quantity': 'D', ...}  # нет custom_field
```

**2. Парсинг офферов:**
```python
# Было (Шаблон 4): 2 оффера на тираж
offers.append({
    'quantity': qty,
    'price_usd': jd_usd,
    'price_rub': jd_rub,
    'delivery_route': 'highway_jd'
})
offers.append({
    'quantity': qty,
    'price_usd': avia_usd,
    'price_rub': avia_rub,
    'delivery_route': 'highway_avia'
})

# Стало (Шаблон 5): 1 оффер на тираж
offers.append({
    'quantity': qty,
    'price_usd': usd,
    'price_rub': rub,
    'delivery_route': None  # нет маршрута
})
```

**3. custom_field:**
```python
# Было (Шаблон 4):
custom_field = self._get_cell_value(ws_data, row, 'custom_field')

# Стало (Шаблон 5):
custom_field = self._get_cell_value(ws_data, row, 'description')
# дизайн уже внутри описания
```

---

**Готово к реализации!** 🚀

Хочешь начать создавать парсер для Шаблона 5?













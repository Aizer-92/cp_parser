# Управление категориями товаров

## 📋 Архитектура категорий

### Источники данных

#### 1. **categories.yaml** (config/)
- **Роль:** Первичный источник для инициализации БД
- **Использование:** При первом запуске приложения / развёртывании
- **Формат:** YAML с структурированными данными о категориях

#### 2. **PostgreSQL БД (таблица `categories`)**
- **Роль:** Единственный источник истины в runtime
- **Использование:** Все операции расчета работают с БД
- **Преимущества:** Динамичность, API для управления, кэширование

### Поток данных

```
categories.yaml  →  (первичная загрузка)  →  PostgreSQL DB  →  PriceCalculator
                                                    ↓
                                            (runtime updates)
                                                    ↓
                                            Все расчёты
```

---

## 🎯 Специальная категория: "Новая категория"

### Назначение
Категория для товаров, которые не были распознаны автоматически.

### Характеристики
```yaml
- category: "Новая категория"
  material: ""
  rail_base: 0  # Требует ручного ввода
  air_base: 0   # Требует ручного ввода
  contract_base: 0
  duty: "Индивидуально"
  vat: 20
  requires_manual_input: true
```

### Workflow
1. Пользователь вводит товар
2. Система не находит подходящую категорию
3. Автоматически выбирается "Новая категория"
4. Открывается редактор параметров маршрута
5. Пользователь вводит кастомные ставки и пошлины

---

## 🛠️ Синхронизация категорий

### Утилита `sync_categories.py`

#### Режимы работы

**1. Проверка расхождений (без изменений):**
```bash
py sync_categories.py --check
```

**Показывает:**
- Категории только в YAML
- Категории только в БД
- Категории с различающимися параметрами

**2. Синхронизация (обновление расхождений):**
```bash
py sync_categories.py
```

**Действия:**
- Добавляет новые категории из YAML
- Обновляет категории с изменившимися параметрами
- НЕ удаляет категории, которые есть только в БД

**3. Полная перезапись (осторожно!):**
```bash
py sync_categories.py --force
```

**Действия:**
- Перезаписывает все категории из YAML
- Может удалить кастомные категории (например, "Новая категория")

**⚠️ Внимание:** Перед `--force` обязательно сделайте бэкап БД!

---

## 📝 Добавление новой категории

### Вариант 1: Через YAML (для постоянных категорий)

**1. Добавьте в `config/categories.yaml`:**
```yaml
- category: "Название категории"
  material: "материал"  # Опционально
  rail_base: 5.0        # Базовая ставка ЖД ($/кг)
  air_base: 7.1         # Базовая ставка Авиа ($/кг)
  contract_base: 4.5    # Базовая ставка Контракт ($/кг)
  duty: 10              # Пошлина (%)
  vat: 20               # НДС (%)
  keywords:             # Ключевые слова для распознавания
    - "ключевое слово 1"
    - "ключевое слово 2"
```

**2. Синхронизируйте с БД:**
```bash
py sync_categories.py
```

**3. Перезапустите приложение** (для обновления кэша)

### Вариант 2: Через API (для динамических категорий)

**Endpoint:** `POST /api/categories` (требуется реализация)

```python
import requests

category_data = {
    "category": "Название категории",
    "material": "материал",
    "rail_base": 5.0,
    "air_base": 7.1,
    # ...
}

response = requests.post(
    "http://localhost:8000/api/categories",
    json=category_data
)
```

---

## 🔧 Структура таблицы `categories`

### PostgreSQL Schema

```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    material VARCHAR(255) DEFAULT '',
    data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(category, material)
);

CREATE INDEX idx_categories_lookup ON categories(category, material);
CREATE INDEX idx_categories_data ON categories USING GIN(data);
```

### Поле `data` (JSONB)

Содержит полные данные категории:
```json
{
  "category": "Название",
  "material": "материал",
  "rail_base": 5.0,
  "air_base": 7.1,
  "contract_base": 4.5,
  "duty": 10,
  "vat": 20,
  "keywords": ["keyword1", "keyword2"],
  "requires_manual_input": false
}
```

---

## 🧪 Тестирование категорий

### 1. Проверка загрузки из БД

```python
from database import load_categories_from_db

categories = load_categories_from_db()
print(f"Загружено {len(categories)} категорий")

# Найти "Новая категория"
new_cat = next(
    (c for c in categories if c['category'] == 'Новая категория'),
    None
)
print(f"Новая категория найдена: {new_cat is not None}")
```

### 2. Проверка распознавания

```python
from price_calculator import PriceCalculator

calc = PriceCalculator()

# Тест 1: Распознанный товар
result1 = calc.find_category_by_name("футболка хлопок")
print(f"Футболка → {result1['category']}")

# Тест 2: Нераспознанный товар
result2 = calc.find_category_by_name("xyzабракадабра123")
print(f"Неизвестный товар → {result2['category']}")
# Ожидается: "Новая категория"
```

### 3. Проверка синхронизации

```bash
# Посмотреть расхождения
py sync_categories.py --check

# Если есть расхождения - синхронизировать
py sync_categories.py
```

---

## 📊 Статистика категорий

### Количество категорий

```sql
-- В PostgreSQL
SELECT COUNT(*) as total_categories FROM categories;

-- По типам duty
SELECT 
    data->>'duty' as duty_type,
    COUNT(*) as count
FROM categories
GROUP BY data->>'duty'
ORDER BY count DESC;
```

### Топ категорий по использованию

```sql
SELECT 
    category,
    COUNT(c.id) as usage_count
FROM calculations c
GROUP BY category
ORDER BY usage_count DESC
LIMIT 10;
```

---

## 🚀 Best Practices

### DO ✅

1. **Используйте `sync_categories.py --check`** перед деплоем
2. **Бэкап БД** перед массовыми изменениями
3. **Тестируйте** новые категории на staging
4. **Документируйте** изменения в категориях
5. **Используйте осмысленные keywords** для автоматического распознавания

### DON'T ❌

1. ❌ Не редактируйте категории напрямую в БД (используйте YAML + sync)
2. ❌ Не удаляйте "Новая категория" из БД
3. ❌ Не используйте `--force` без бэкапа
4. ❌ Не дублируйте keywords между категориями
5. ❌ Не оставляйте пустые `rail_base`/`air_base` для обычных категорий

---

## 🔍 Troubleshooting

### Проблема: "Новая категория" не найдена

**Решение:**
```bash
# 1. Проверить наличие в YAML
grep -A 5 "Новая категория" config/categories.yaml

# 2. Синхронизировать с БД
py sync_categories.py

# 3. Проверить в БД
py -c "from database import load_categories_from_db; \
       cats = load_categories_from_db(); \
       print([c['category'] for c in cats])"
```

### Проблема: Категория не распознаётся

**Решение:**
1. Проверить keywords в `categories.yaml`
2. Добавить больше вариантов ключевых слов
3. Синхронизировать: `py sync_categories.py`

### Проблема: Устаревшие данные в runtime

**Решение:**
```bash
# Перезапустить приложение для обновления кэша
# Railway автоматически перезапустится после деплоя
```

---

## 📚 Ссылки

- [categories.yaml](config/categories.yaml) - Исходные данные
- [database.py](database.py) - Функции работы с БД
- [price_calculator.py](price_calculator.py) - Логика распознавания
- [sync_categories.py](sync_categories.py) - Утилита синхронизации

---

**Версия:** 1.0  
**Дата:** 10.10.2025  
**Автор:** Refactoring Stage 3







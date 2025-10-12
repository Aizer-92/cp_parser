# 🔍 Проверка колонки name_embedding_text на Railway

## 📍 Где хранится колонка?

Колонка `name_embedding_text` хранится в таблице **`products`** в PostgreSQL базе данных Railway.

**Структура:**
```
products
├── id (INTEGER)
├── name (TEXT)
├── category (TEXT)
├── ... другие колонки ...
└── name_embedding_text (TEXT) ← векторные embeddings в формате JSON
```

---

## ✅ Способ 1: Через Railway Dashboard (самый простой)

### 1. Открой Railway Dashboard
https://railway.app → выбери свой проект

### 2. Найди PostgreSQL сервис
Кликни на сервис **PostgreSQL** в проекте

### 3. Открой Query Editor
В PostgreSQL сервисе найди **"Query"** или **"Data"** вкладку

### 4. Выполни SQL запрос:

```sql
-- Проверить существование колонки
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'products'
  AND column_name = 'name_embedding_text';
```

**Ожидаемый результат:**
```
column_name           | data_type | is_nullable
----------------------+-----------+------------
name_embedding_text   | text      | YES
```

Если результат **пустой** → колонка НЕ существует, нужно добавить (см. ниже)

### 5. Проверить данные (если колонка существует):

```sql
-- Статистика embeddings
SELECT 
    COUNT(*) as total_products,
    COUNT(name_embedding_text) as with_embeddings,
    COUNT(*) - COUNT(name_embedding_text) as without_embeddings,
    ROUND(COUNT(name_embedding_text)::numeric / COUNT(*)::numeric * 100, 1) as coverage_percent
FROM products;
```

---

## ✅ Способ 2: Через psql (командная строка)

### 1. Получи Connection URL из Railway

Railway Dashboard → PostgreSQL сервис → **Connect** → **Postgres Connection URL**

Скопируй строку вида:
```
postgresql://postgres:PASSWORD@containers-us-west-XXX.railway.app:5432/railway
```

### 2. Подключись через psql

```bash
psql "postgresql://postgres:PASSWORD@containers-us-west-XXX.railway.app:5432/railway"
```

### 3. Выполни команды:

```sql
-- Проверить колонку
\d products

-- Должно быть в списке:
-- name_embedding_text | text |

-- Статистика
SELECT 
    COUNT(*) as total,
    COUNT(name_embedding_text) as with_embeddings
FROM products;
```

### 4. Выход
```sql
\q
```

---

## ✅ Способ 3: Через Python скрипт

### 1. Экспортируй Railway DATABASE_URL

```bash
export DATABASE_URL="postgresql://postgres:PASSWORD@...railway.app:5432/railway"
```

### 2. Запусти скрипт проверки

```bash
python3 check_embeddings_column.py
```

**Ожидаемый вывод:**
```
================================================================================
Проверка колонки name_embedding_text - 🚂 Railway БД
================================================================================

✅ Подключение успешно
   PostgreSQL: PostgreSQL 15.X...

📊 Колонки таблицы products:
--------------------------------------------------------------------------------
🟢 name_embedding_text         TEXT                 NULL
--------------------------------------------------------------------------------

✅ Колонка name_embedding_text СУЩЕСТВУЕТ!

📈 Статистика embeddings:
   Всего товаров:       14,403
   С embeddings:        14,403 (100.0%)
   Без embeddings:      0

🎉 ВСЕ товары имеют embeddings! Векторный поиск готов!
```

---

## ❌ Если колонка НЕ существует

### Добавить колонку через psql:

```bash
# Подключись к Railway БД
psql "postgresql://postgres:...railway.app:5432/railway"

# Добавь колонку
ALTER TABLE products ADD COLUMN IF NOT EXISTS name_embedding_text TEXT;

# Проверь
\d products

# Выход
\q
```

### Или через Python скрипт:

```bash
# Экспортируй URL Railway БД
export DATABASE_URL="postgresql://postgres:...railway.app:5432/railway"

# Запусти setup
python3 setup_embeddings_simple.py
```

---

## ⚠️ Важные замечания

### 1. **Колонка на Railway НЕ создается автоматически**

Просто деплой кода НЕ добавит колонку. Нужно выполнить миграцию:
- Через psql (Способ выше)
- Через Python скрипт `setup_embeddings_simple.py`

### 2. **Embeddings тоже не появятся автоматически**

После добавления колонки нужно заполнить её данными:

**Вариант A: Скопировать из локальной БД** (быстро, 2 минуты)
```bash
python3 copy_embeddings_to_railway.py
```

**Вариант B: Сгенерировать заново** (медленно, 50 минут, $0.03)
```bash
export DATABASE_URL="postgresql://postgres:...railway.app:5432/railway"
python3 generate_embeddings_simple.py
```

### 3. **Векторный поиск работает БЕЗ embeddings**

Благодаря graceful fallback, даже если embeddings нет:
- Поиск работает (через обычный ILIKE)
- Приложение не ломается
- Пользователи не видят ошибок

Просто не будет умного семантического поиска по синонимам.

---

## 📊 Ожидаемая структура данных

### Как выглядит `name_embedding_text`:

```json
[0.023, -0.041, 0.018, ..., 0.029]
```

- Массив из 1536 чисел (float)
- Хранится как JSON строка в TEXT колонке
- Создается через OpenAI API (модель: text-embedding-3-small)

### Пример записи:

```sql
SELECT id, name, LEFT(name_embedding_text, 100) as embedding_preview
FROM products
WHERE name_embedding_text IS NOT NULL
LIMIT 1;
```

Результат:
```
id  | name              | embedding_preview
----+-------------------+--------------------------------------------------
123 | Кружка керамическая | [0.0234, -0.0412, 0.0187, 0.0523, -0.0198, ...
```

---

## 🎯 Чеклист проверки

- [ ] Колонка `name_embedding_text` существует в таблице `products`
- [ ] Тип колонки: `TEXT`
- [ ] Колонка может быть `NULL`
- [ ] В колонке есть данные (COUNT > 0)
- [ ] Покрытие близко к 100% (14,403 товаров)
- [ ] Данные в формате JSON массива чисел

---

## 📞 Быстрая диагностика

**Симптом:** Поиск не находит синонимы  
**Диагностика:** Проверь наличие embeddings в БД  
**Решение:** Скопируй или сгенерируй embeddings

**Симптом:** Ошибка "column name_embedding_text does not exist"  
**Диагностика:** Колонка не добавлена  
**Решение:** Запусти `setup_embeddings_simple.py` или SQL ALTER TABLE

**Симптом:** Векторный поиск отключен (в логах)  
**Диагностика:** Нет OpenAI API ключа или embeddings  
**Решение:** Добавь `OPENAI_API_KEY` в Railway Variables и заполни embeddings

---

## 🚀 Итоговый порядок действий для Railway

1. ✅ Задеплой код (git push)
2. ✅ Добавь `OPENAI_API_KEY` в Railway Variables
3. ✅ Добавь колонку `name_embedding_text` (psql или Python)
4. ✅ Скопируй embeddings из локальной БД (2 мин)
5. ✅ Проверь что поиск работает

**Время:** ~15-20 минут  
**Стоимость:** $0 (копирование) или $0.03 (генерация заново)

---

📖 **Полная инструкция:** RAILWAY_DEPLOY_QUICKSTART.md




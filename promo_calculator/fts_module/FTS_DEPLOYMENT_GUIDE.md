# Руководство по деплою полнотекстового поиска

## 📋 Обзор

Полнотекстовый поиск реализован как отдельный модуль `fts_search.py` для легкого деплоя и обновления. Модуль включает:

- ✅ Весовые коэффициенты (заголовки > описания)
- ✅ Автоматическое обновление при изменении данных
- ✅ Ранжирование по релевантности
- ✅ Русская морфология

## 🚀 Быстрый деплой

### 1. Генерация пакета деплоя

```bash
cd projects/promo_calculator
py export_fts_changes.py
```

Это создаст папку `fts_deployment_YYYYMMDD_HHMMSS/` с:
- `fts_export_*.sql` - основной скрипт установки
- `fts_rollback_*.sql` - скрипт отката
- `README.md` - инструкции

### 2. Установка на продакшн

```bash
psql -h <host> -U <user> -d <database> -f fts_export_*.sql
```

### 3. Проверка установки

```bash
# Проверка структуры
psql -h <host> -U <user> -d <database> -c "
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' AND column_name = 'search_vector';
"

# Проверка индекса
psql -h <host> -U <user> -d <database> -c "
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'products' AND indexname = 'idx_products_search_vector';
"

# Тест поиска
psql -h <host> -U <user> -d <database> -c "
SELECT COUNT(*) FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'телефон');
"
```

## 📊 Что экспортируется

### 1. Структура базы данных

```sql
-- Колонка для полнотекстового поиска
ALTER TABLE products ADD COLUMN search_vector tsvector;

-- GIN индекс для быстрого поиска
CREATE INDEX idx_products_search_vector ON products USING gin(search_vector);
```

### 2. Функции и триггеры

```sql
-- Функция обновления с весами
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('russian', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('russian', COALESCE(NEW.original_title, '')), 'A') ||
        setweight(to_tsvector('russian', COALESCE(NEW.brand, '')), 'B') ||
        setweight(to_tsvector('russian', COALESCE(NEW.vendor, '')), 'B') ||
        setweight(to_tsvector('russian', COALESCE(NEW.description, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для автоматического обновления
CREATE TRIGGER update_products_search_vector
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();
```

### 3. Заполнение данных

```sql
-- Обновление всех существующих записей
UPDATE products SET search_vector = 
    setweight(to_tsvector('russian', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('russian', COALESCE(original_title, '')), 'A') ||
    setweight(to_tsvector('russian', COALESCE(brand, '')), 'B') ||
    setweight(to_tsvector('russian', COALESCE(vendor, '')), 'B') ||
    setweight(to_tsvector('russian', COALESCE(description, '')), 'C');
```

## ⚖️ Весовые коэффициенты

| Вес | Поля | Описание |
|-----|------|----------|
| **A** | `title`, `original_title` | Высокий вес - заголовки товаров |
| **B** | `brand`, `vendor` | Средний вес - бренды и поставщики |
| **C** | `description` | Низкий вес - описания |

## 🔍 Использование в коде

### Базовый поиск

```sql
SELECT * FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'телефон');
```

### Поиск с ранжированием

```sql
SELECT *, ts_rank_cd(search_vector, plainto_tsquery('russian', 'телефон'), 32) as rank
FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'телефон')
ORDER BY rank DESC;
```

### Поиск с весами

```sql
SELECT *, 
       ts_rank_cd(search_vector, plainto_tsquery('russian', 'телефон'), 32) as rank,
       ts_rank_cd(search_vector, plainto_tsquery('russian', 'телефон'), 1) as rank_title,
       ts_rank_cd(search_vector, plainto_tsquery('russian', 'телефон'), 2) as rank_description
FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'телефон')
ORDER BY rank DESC;
```

## 🐍 Использование в Python

### Инициализация модуля

```python
from fts_search import FullTextSearch

pg_config = {
    'host': 'localhost',
    'port': '5432',
    'database': 'promo_calculator',
    'user': 'postgres',
    'password': 'postgres'
}

fts = FullTextSearch(pg_config)
```

### Поиск товаров

```python
# Поиск с ранжированием
products, total_count = fts.search_products("телефон", limit=25, offset=0)

# Получение предложений
suggestions = fts.get_search_suggestions("тел", limit=10)

# Статистика
stats = fts.get_search_statistics()
```

## 🔄 Обновление модуля

### 1. Обновление кода

```bash
# Обновить fts_search.py
# Обновить main.py (если нужно)
```

### 2. Перезапуск приложения

```bash
# Остановить приложение
# Запустить заново
py main.py
```

### 3. Обновление базы данных (если нужно)

```bash
# Если изменились веса или структура
py fts_search.py  # Пересоздаст структуру
```

## 🛠️ Отладка

### Проверка работы FTS

```python
from fts_search import FullTextSearch

fts = FullTextSearch(pg_config)

# Тестирование
results = fts.test_search(["телефон", "платье", "обувь"])
print(results)

# Статистика
stats = fts.get_search_statistics()
print(stats)
```

### Проверка в базе данных

```sql
-- Проверка заполнения
SELECT COUNT(*) as total, 
       COUNT(search_vector) as with_fts,
       ROUND(COUNT(search_vector)::numeric / COUNT(*) * 100, 2) as coverage
FROM products;

-- Проверка размера индекса
SELECT pg_size_pretty(pg_relation_size('idx_products_search_vector'));

-- Тест поиска
SELECT title, ts_rank_cd(search_vector, plainto_tsquery('russian', 'телефон'), 32) as rank
FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'телефон')
ORDER BY rank DESC
LIMIT 5;
```

## 🚨 Откат изменений

Если что-то пошло не так:

```bash
psql -h <host> -U <user> -d <database> -f fts_rollback_*.sql
```

Это удалит:
- Триггер `update_products_search_vector`
- Функцию `update_search_vector()`
- Индекс `idx_products_search_vector`
- Колонку `search_vector`

## 📈 Производительность

### Рекомендации

1. **Индекс**: GIN индекс автоматически создается для быстрого поиска
2. **Кэширование**: Результаты поиска можно кэшировать в приложении
3. **Пагинация**: Всегда используйте LIMIT для больших результатов
4. **Мониторинг**: Следите за размером индекса и производительностью

### Мониторинг

```sql
-- Размер индекса
SELECT pg_size_pretty(pg_relation_size('idx_products_search_vector'));

-- Статистика использования
SELECT * FROM pg_stat_user_indexes WHERE indexrelname = 'idx_products_search_vector';

-- Медленные запросы
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE query LIKE '%search_vector%'
ORDER BY mean_time DESC;
```

## ✅ Чек-лист деплоя

- [ ] Создан пакет деплоя (`py export_fts_changes.py`)
- [ ] Проверена совместимость с существующей базой
- [ ] Создан бэкап базы данных
- [ ] Установлен FTS на тестовой среде
- [ ] Протестирован поиск
- [ ] Установлен FTS на продакшн
- [ ] Проверена работа приложения
- [ ] Настроен мониторинг

## 📞 Поддержка

При проблемах проверьте:

1. **Логи приложения** - ошибки инициализации FTS
2. **Логи PostgreSQL** - ошибки создания индексов/функций
3. **Статистику поиска** - количество найденных товаров
4. **Размер индекса** - не должен быть слишком большим

---

**Версия**: 1.0  
**Дата**: 2025-01-27  
**Автор**: Personal Super Agent

# Модуль полнотекстового поиска (FTS)

## 📋 Обзор

Этот модуль содержит все компоненты для полнотекстового поиска с весовыми коэффициентами и правильной русской морфологией.

## 🚨 ВАЖНО: Исправлена морфология!

**Проблема**: "Таблетница" и "Таблетницы" находили разное количество результатов  
**Решение**: Используется правильная 'russian' конфигурация PostgreSQL

## 📁 Структура модуля

```
fts_module/
├── README.md                           # Эта документация
├── fts_search.py                       # Основной модуль FTS
├── export_fts_fixed.py                 # Генератор пакетов деплоя
├── test_final_morphology.py            # Тестирование морфологии
├── FTS_DEPLOYMENT_GUIDE.md             # Подробное руководство по деплою
└── fts_deployment_latest/              # Готовый пакет деплоя
    ├── fts_export_latest.sql           # SQL скрипт установки
    └── README.md                       # Инструкции по деплою
```

## 🚀 Быстрый старт

### 1. Использование в коде

```python
from fts_module.fts_search import FullTextSearch

# Инициализация
pg_config = {
    'host': 'localhost',
    'port': '5432', 
    'database': 'promo_calculator',
    'user': 'postgres',
    'password': 'postgres'
}

fts = FullTextSearch(pg_config)

# Поиск с ранжированием
products, total_count = fts.search_products("таблетница", limit=25)
```

### 2. Деплой на продакшн

```bash
# Создать исправленный пакет деплоя
py export_fts_fixed.py

# Установить на продакшн
psql -h <host> -U <user> -d <database> -f fts_deployment_latest/fts_export_latest.sql
```

## ⚖️ Весовые коэффициенты

| Вес | Поля | Описание |
|-----|------|----------|
| **A** | `title`, `original_title` | Высокий вес - заголовки товаров |
| **B** | `brand`, `vendor` | Средний вес - бренды и поставщики |
| **C** | `description` | Низкий вес - описания |

## 🔍 Исправления морфологии

### Проблема
```sql
-- НЕПРАВИЛЬНО (simple конфигурация)
SELECT COUNT(*) FROM products 
WHERE search_vector @@ plainto_tsquery('simple', 'таблетница');  -- 0 результатов

SELECT COUNT(*) FROM products 
WHERE search_vector @@ plainto_tsquery('simple', 'таблетницы');  -- 0 результатов
```

### Решение
```sql
-- ПРАВИЛЬНО (russian конфигурация)
SELECT COUNT(*) FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'таблетница');  -- 121 результат

SELECT COUNT(*) FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'таблетницы');  -- 121 результат ✅
```

## 🧪 Тестирование

### Тест морфологии

```bash
py test_morphology.py
```

Должен показать одинаковые результаты для разных форм слова.

### Тест в коде

```python
from fts_module.fts_search import FullTextSearch

fts = FullTextSearch(pg_config)

# Тестирование
results = fts.test_search(["таблетница", "таблетницы", "телефон"])
print(results)
```

## 📊 Результаты тестирования

### До исправления
- "таблетница": 0 товаров (simple FTS)
- "таблетницы": 0 товаров (simple FTS)
- "телефон": 825 товаров (simple FTS)
- "телефона": 0 товаров (simple FTS) ❌

### После исправления
- "таблетница": 121 товар (russian FTS)
- "таблетницы": 121 товар (russian FTS) ✅
- "телефон": 825 товаров (russian FTS)
- "телефона": 825 товаров (russian FTS) ✅

## 🔄 Обновление

### 1. Обновление кода
```bash
# Обновить fts_search.py
# Обновить main.py (импорт из fts_module.fts_search)
```

### 2. Обновление базы данных
```bash
# Создать новый пакет деплоя
py export_fts_fixed.py

# Установить на продакшн
psql -h <host> -U <user> -d <database> -f fts_deployment_latest/fts_export_latest.sql
```

## 🛠️ Отладка

### Проверка конфигурации

```sql
-- Проверить используемую конфигурацию
SELECT to_tsvector('russian', 'таблетница');
SELECT to_tsvector('simple', 'таблетница');
```

### Проверка индекса

```sql
-- Размер индекса
SELECT pg_size_pretty(pg_relation_size('idx_products_search_vector'));

-- Статистика использования
SELECT * FROM pg_stat_user_indexes WHERE indexrelname = 'idx_products_search_vector';
```

## 📈 Производительность

- **GIN индекс**: Автоматически создается для быстрого поиска
- **Ранжирование**: Использует `ts_rank_cd` с весовыми коэффициентами
- **Кэширование**: Результаты можно кэшировать в приложении
- **Пагинация**: Всегда используйте LIMIT для больших результатов

## 🚨 Откат

Если что-то пошло не так:

```sql
-- Удалить все FTS структуры
DROP TRIGGER IF EXISTS update_products_search_vector ON products;
DROP FUNCTION IF EXISTS update_search_vector();
DROP INDEX IF EXISTS idx_products_search_vector;
ALTER TABLE products DROP COLUMN IF EXISTS search_vector;
```

## 📞 Поддержка

При проблемах проверьте:

1. **Логи приложения** - ошибки инициализации FTS
2. **Логи PostgreSQL** - ошибки создания индексов/функций
3. **Тест морфологии** - `py test_morphology.py`
4. **Статистику поиска** - количество найденных товаров

## ✅ Чек-лист

- [x] Исправлена морфология (russian конфигурация)
- [x] Весовые коэффициенты настроены
- [x] Автоматическое обновление при изменении данных
- [x] Ранжирование по релевантности
- [x] Тестирование морфологии
- [x] Пакеты деплоя готовы
- [x] Документация создана

---

**Версия**: 1.1 (ИСПРАВЛЕНА МОРФОЛОГИЯ)  
**Дата**: 2025-01-27  
**Автор**: Personal Super Agent

# Пакет деплоя ИСПРАВЛЕННОГО полнотекстового поиска

Дата создания: 2025-09-07 10:34:47
Версия: 1.1 (ИСПРАВЛЕНА МОРФОЛОГИЯ)

## 🚨 ВАЖНО: Исправления

Этот пакет исправляет проблему с морфологией поиска:
- ✅ "таблетница" и "таблетницы" теперь находят одинаковые результаты
- ✅ Используется правильная 'russian' конфигурация PostgreSQL
- ✅ Сохранены все весовые коэффициенты

## Содержимое пакета

- `fts_export_latest.sql` - Исправленный скрипт установки FTS
- `README.md` - Эта документация

## Инструкция по деплою

### 1. Установка исправленного FTS

```bash
psql -h <host> -U <user> -d <database> -f fts_export_latest.sql
```

### 2. Проверка исправлений

После установки проверьте морфологию:

```sql
-- Должно быть одинаковое количество результатов
SELECT COUNT(*) FROM products WHERE search_vector @@ plainto_tsquery('russian', 'таблетница');
SELECT COUNT(*) FROM products WHERE search_vector @@ plainto_tsquery('russian', 'таблетницы');
```

### 3. Откат (если необходимо)

```bash
# Удалить старые структуры
psql -h <host> -U <user> -d <database> -c "
DROP TRIGGER IF EXISTS update_products_search_vector ON products;
DROP FUNCTION IF EXISTS update_search_vector();
DROP INDEX IF EXISTS idx_products_search_vector;
ALTER TABLE products DROP COLUMN IF EXISTS search_vector;
"
```

## Что исправлено

1. **Морфология**: Используется 'russian' конфигурация вместо 'simple'
2. **Функция**: update_search_vector() использует правильную конфигурацию
3. **Заполнение**: Все существующие записи обновляются с правильной морфологией
4. **Тестирование**: Добавлены тесты морфологии

## Весовые коэффициенты (без изменений)

- **A (высокий)**: title, original_title - заголовки
- **B (средний)**: brand, vendor - бренды и поставщики
- **C (низкий)**: description - описания

## Использование в коде

```sql
-- Поиск с правильной морфологией
SELECT * FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'запрос')
ORDER BY ts_rank_cd(search_vector, plainto_tsquery('russian', 'запрос'), 32) DESC;
```

## Требования

- PostgreSQL 9.6+
- Расширение для русского языка (обычно включено)
- Права на создание функций, триггеров и индексов

## Тестирование

После установки протестируйте:

```sql
-- Тест 1: Морфология
SELECT 'таблетница' as word, COUNT(*) as count 
FROM products WHERE search_vector @@ plainto_tsquery('russian', 'таблетница')
UNION ALL
SELECT 'таблетницы' as word, COUNT(*) as count 
FROM products WHERE search_vector @@ plainto_tsquery('russian', 'таблетницы');

-- Тест 2: Ранжирование
SELECT title, ts_rank_cd(search_vector, plainto_tsquery('russian', 'телефон'), 32) as rank
FROM products 
WHERE search_vector @@ plainto_tsquery('russian', 'телефон')
ORDER BY rank DESC
LIMIT 5;
```

Результаты должны быть одинаковыми для разных форм слова!

# План внедрения векторного поиска

## 🎯 Цель
Улучшить поиск по товарам с учетом синонимов и семантического сходства.

**Проблема сейчас:**
- Поиск по `ILIKE` - только точное совпадение подстроки
- "рюкзак" не найдет "backpack"
- "ручка" не найдет "pen" 
- "блокнот" не найдет "тетрадь" или "записная книжка"
- Нужно перебирать вручную разные варианты названий

**Что даст векторный поиск:**
- Семантический поиск (понимает смысл)
- Находит синонимы автоматически
- Работает с разными языками (РУ/EN)
- Учитывает опечатки и вариации написания

---

## 🏗️ Архитектура решения

### Вариант 1: PostgreSQL + pgvector (РЕКОМЕНДУЕТСЯ)

**Преимущества:**
- ✅ Используем существующую БД (уже есть PostgreSQL на Railway)
- ✅ Не нужны дополнительные сервисы
- ✅ Простая интеграция с текущим кодом
- ✅ Бесплатно (Railway уже оплачивается)
- ✅ Низкая латентность (данные в той же БД)

**Недостатки:**
- ⚠️ Нужно установить расширение pgvector на Railway
- ⚠️ Нужно сгенерировать embeddings для всех товаров

**Технологии:**
- PostgreSQL расширение: `pgvector`
- Embeddings модель: OpenAI `text-embedding-3-small` или локальная `sentence-transformers`
- Индексация: HNSW (Hierarchical Navigable Small World)

---

### Вариант 2: Elasticsearch с kNN search

**Преимущества:**
- ✅ Мощная full-text search из коробки
- ✅ Масштабируемость
- ✅ Множество фич (фасеты, аггрегации)

**Недостатки:**
- ❌ Дополнительный сервис ($$$)
- ❌ Сложнее в настройке
- ❌ Дублирование данных (ES + PostgreSQL)
- ❌ Избыточно для текущей задачи

---

### Вариант 3: Pinecone / Weaviate (векторные БД)

**Преимущества:**
- ✅ Специализированные для векторного поиска
- ✅ Высокая производительность

**Недостатки:**
- ❌ Дополнительная подписка ($$$)
- ❌ Vendor lock-in
- ❌ Дублирование данных

---

## 📋 Детальный план реализации (Вариант 1)

### Фаза 1: Подготовка (1-2 дня)

#### 1.1. Установка pgvector на Railway
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**Проверка:**
```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

#### 1.2. Добавление колонки для embeddings
```sql
ALTER TABLE products 
ADD COLUMN name_embedding vector(1536);  -- Размер для OpenAI text-embedding-3-small

CREATE INDEX ON products 
USING hnsw (name_embedding vector_cosine_ops);
```

#### 1.3. Выбор модели для embeddings

**Вариант A: OpenAI API (рекомендуется для старта)**
- Модель: `text-embedding-3-small` (1536 размерность)
- Стоимость: ~$0.02 за 1M токенов
- Для 3,000 товаров × 50 токенов = ~$0.003
- Качество: отличное, multilingual (RU+EN)

**Вариант B: Локальная модель (для экономии)**
- Модель: `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`
- Стоимость: $0 (но нужно CPU/GPU)
- Размерность: 768
- Качество: хорошее для RU+EN

**Рекомендация:** Начать с OpenAI (проще, надежнее), потом можно перейти на локальную.

---

### Фаза 2: Генерация embeddings (1 день)

#### 2.1. Скрипт генерации embeddings
```python
# generate_embeddings.py

from openai import OpenAI
from database.postgresql_manager import db_manager
from sqlalchemy import text
import time

client = OpenAI(api_key="...")

def generate_embedding(text: str):
    """Генерирует embedding для текста"""
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def update_product_embeddings():
    with db_manager.get_session() as session:
        # Получаем все товары без embeddings
        products = session.execute(text("""
            SELECT id, name, description
            FROM products
            WHERE name_embedding IS NULL
            ORDER BY id
        """)).fetchall()
        
        print(f"Найдено {len(products)} товаров для обработки")
        
        for i, (product_id, name, description) in enumerate(products, 1):
            # Формируем текст для embedding
            text_for_embedding = name
            if description:
                text_for_embedding += f" {description[:200]}"  # Первые 200 символов
            
            # Генерируем embedding
            embedding = generate_embedding(text_for_embedding)
            
            # Сохраняем в БД
            session.execute(text("""
                UPDATE products 
                SET name_embedding = :embedding::vector
                WHERE id = :product_id
            """), {
                'embedding': str(embedding),
                'product_id': product_id
            })
            
            if i % 10 == 0:
                session.commit()
                print(f"✅ Обработано {i}/{len(products)}")
                time.sleep(0.1)  # Rate limiting
        
        session.commit()
        print(f"✅ Все embeddings сгенерированы!")

if __name__ == '__main__':
    update_product_embeddings()
```

#### 2.2. Тестовый запрос
```sql
-- Найти товары похожие на "рюкзак"
WITH query_embedding AS (
    SELECT '[...]'::vector as embedding  -- embedding для "рюкзак"
)
SELECT 
    p.id,
    p.name,
    1 - (p.name_embedding <=> q.embedding) as similarity
FROM products p, query_embedding q
WHERE p.name_embedding IS NOT NULL
ORDER BY p.name_embedding <=> q.embedding
LIMIT 10;
```

---

### Фаза 3: Интеграция в веб-интерфейс (1-2 дня)

#### 3.1. Обновление backend

**Гибридный поиск (рекомендуется):**
1. Сначала векторный поиск (top-50 по семантике)
2. Потом фильтрация по цене/тиражу/региону
3. Сортировка по релевантности

```python
# app.py

def products_list():
    search = request.args.get('search', '', type=str)
    
    if search.strip():
        # Генерируем embedding для поискового запроса
        search_embedding = generate_embedding(search.strip())
        
        # Векторный поиск + фильтры
        products_sql = text(f"""
            WITH ranked_products AS (
                SELECT 
                    p.id,
                    p.name,
                    p.description,
                    pr.region,
                    1 - (p.name_embedding <=> :search_embedding::vector) as similarity
                FROM products p
                LEFT JOIN projects pr ON p.project_id = pr.id
                WHERE p.name_embedding IS NOT NULL
                    AND {where_clause}
                ORDER BY p.name_embedding <=> :search_embedding::vector
                LIMIT 100
            )
            SELECT * FROM ranked_products
            WHERE similarity > 0.5  -- Порог релевантности
            ORDER BY similarity DESC
            LIMIT :limit OFFSET :offset
        """)
    else:
        # Обычный запрос без поиска
        ...
```

#### 3.2. Кэширование embeddings запросов
```python
# Кэш для частых запросов
import redis
cache = redis.Redis(...)

def get_cached_embedding(query: str):
    cached = cache.get(f"emb:{query}")
    if cached:
        return json.loads(cached)
    
    embedding = generate_embedding(query)
    cache.setex(f"emb:{query}", 3600, json.dumps(embedding))
    return embedding
```

#### 3.3. UI улучшения
- Показывать "релевантность" (similarity score)
- "Похожие товары" в карточке товара
- Автокомплит с семантическими подсказками

---

### Фаза 4: Оптимизация (1 день)

#### 4.1. Мониторинг производительности
```python
import time

start = time.time()
# Векторный поиск
end = time.time()
print(f"Поиск занял: {end - start:.3f}s")
```

#### 4.2. Индексы
```sql
-- HNSW индекс для быстрого поиска
CREATE INDEX products_name_embedding_idx 
ON products 
USING hnsw (name_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Обычный индекс для фильтров
CREATE INDEX products_project_region_idx ON products(project_id) 
WHERE region = 'ОАЭ';
```

#### 4.3. Автоматическое обновление embeddings
```python
# При создании нового товара
def create_product(name, description, ...):
    # Сохраняем товар
    product = Product(name=name, ...)
    session.add(product)
    session.flush()
    
    # Сразу генерируем embedding
    embedding = generate_embedding(f"{name} {description}")
    product.name_embedding = embedding
    
    session.commit()
```

---

## 💰 Стоимость

### OpenAI API
- Генерация embeddings для 3,000 товаров: **~$0.01** (одноразово)
- Поисковые запросы: **~$0.001 за 1,000 запросов**
- Месячная стоимость (10,000 запросов): **~$0.01**

### Railway (pgvector)
- $0 дополнительно (входит в текущий план)

**Итого: ~$0.02/месяц** 🎉

---

## 📊 Ожидаемые результаты

### Улучшение поиска:
- ✅ Находит синонимы ("рюкзак" → "backpack", "сумка на спину")
- ✅ Работает с опечатками ("ручьа" → "ручка")
- ✅ Понимает контекст ("деловой подарок" → блокноты, ручки)
- ✅ Multilingual (EN ↔ RU автоматически)

### Производительность:
- Векторный поиск: **~50-100ms**
- ILIKE поиск сейчас: **~20-30ms**
- Компромисс приемлемый для улучшения качества

---

## 🚀 Пилотный запуск (минимальный MVP)

### Что сделать для теста:

1. **Установить pgvector на Railway** (5 минут)
   ```sql
   CREATE EXTENSION vector;
   ```

2. **Добавить колонку** (1 минута)
   ```sql
   ALTER TABLE products ADD COLUMN name_embedding vector(1536);
   ```

3. **Сгенерировать embeddings для 100 товаров** (5 минут)
   - Взять топ-100 популярных товаров
   - Прогнать через OpenAI API

4. **Тестовый поиск** (10 минут)
   - Написать простой endpoint `/search_vector`
   - Сравнить с обычным поиском

**Время на MVP: 30 минут**
**Стоимость: $0.001**

---

## ❓ Вопросы для обсуждения

1. **Бюджет:** Готовы тратить ~$0.02/месяц на OpenAI или хотите локальную модель?
2. **Производительность:** Приемлемо ли увеличение времени поиска до 100ms?
3. **Объем:** Сколько новых товаров добавляется в месяц? (для авто-генерации embeddings)
4. **Языки:** Только RU+EN или нужны другие?
5. **Приоритет:** Это критично сейчас или можно сделать позже?

---

## 🎯 Рекомендация

**Предлагаю начать с MVP:**
1. Установить pgvector (5 мин)
2. Сгенерировать embeddings для 100 товаров (5 мин)
3. Сделать тестовый endpoint (20 мин)
4. Оценить результаты

**Если понравится → внедряем для всех товаров**
**Если нет → откатываем (ничего не сломается)**

**Риски: минимальные**
**Выгода: потенциально огромная** (намного удобнее искать!)

---

## 📚 Полезные ссылки

- [pgvector документация](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [sentence-transformers](https://www.sbert.net/)
- [HNSW индексы](https://github.com/nmslib/hnswlib)

---

**Создано:** 10.10.2025
**Статус:** План готов к обсуждению
**Следующий шаг:** Решение по MVP



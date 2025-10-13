# 🚀 Деплой векторного поиска на Railway

**Дата:** 10 октября 2025  
**Статус:** Готово к деплою

---

## ✅ Что уже готово

- ✅ Railway подключен к GitHub
- ✅ PostgreSQL база данных подключена к проекту
- ✅ Код с векторным поиском готов (graceful fallback)
- ✅ Зависимости обновлены (openai, python-dotenv в requirements.txt)
- ✅ `.env` добавлен в `.gitignore`
- ✅ Локально всё работает (14,403 товаров с embeddings)

---

## 📋 Пошаговый план деплоя

### Шаг 1: Добавить OpenAI API ключ в Railway

1. Открой проект в Railway: https://railway.app
2. Выбери свой сервис `cp_parser` (или как он называется)
3. Перейди в **Variables** (вкладка переменных окружения)
4. Добавь новую переменную:
   ```
   Key: OPENAI_API_KEY
   Value: sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
5. Сохрани (Railway автоматически перезапустит сервис)

---

### Шаг 2: Закоммитить и запушить изменения

```bash
# Убедись что ты в директории проекта
cd /Users/bakirovresad/Downloads/Reshad\ 1/projects/cp_parser

# Проверь статус Git
git status

# Добавь все изменения
git add web_interface/app.py
git add web_interface/requirements.txt
git add web_interface/templates/products_list.html
git add web_interface/templates/product_detail.html
git add web_interface/templates/project_detail.html
git add .gitignore
git add README.md

# Также добавь документацию (опционально, но рекомендуется)
git add VECTOR_SEARCH_*.md

# Закоммить
git commit -m "✨ Добавлен AI-powered векторный поиск с OpenAI embeddings

- Интегрирован OpenAI API для семантического поиска
- Добавлен graceful fallback на ILIKE при сбоях AI
- Обновлен UI: collapsible фильтры, табовая сортировка
- Добавлены метаданные: менеджер и дата создания КП
- Исправлены 311 аномальных quantity записей
- Документация: VECTOR_SEARCH_*.md"

# Запушить в GitHub
git push origin main  # или master, в зависимости от ветки
```

**Railway автоматически подхватит изменения и задеплоит!** 🚀

---

### Шаг 3: Добавить колонку в Railway БД

После деплоя нужно добавить колонку `name_embedding_text` в production базу.

**Вариант A: Через Railway CLI (рекомендуется)**

```bash
# Подключись к Railway БД через CLI
railway run python3 setup_embeddings_simple.py
```

**Вариант B: Через psql напрямую**

1. В Railway dashboard найди свою PostgreSQL базу
2. Скопируй `DATABASE_URL` или connection string
3. Подключись локально:
   ```bash
   psql <DATABASE_URL>
   ```
4. Выполни SQL:
   ```sql
   ALTER TABLE products ADD COLUMN IF NOT EXISTS name_embedding_text TEXT;
   ```
5. Проверь:
   ```sql
   SELECT COUNT(*) FROM products WHERE name_embedding_text IS NULL;
   ```

**Вариант C: Загрузи скрипт как одноразовую задачу**

Можно создать временный Python скрипт в Railway и запустить его один раз:

1. Создай файл `migrate_add_embeddings_column.py` (или загрузи `setup_embeddings_simple.py`)
2. Запусти через Railway CLI:
   ```bash
   railway run python3 setup_embeddings_simple.py
   ```

---

### Шаг 4: Сгенерировать embeddings для production БД

Теперь самое важное - сгенерировать embeddings для всех товаров в production.

**⚠️ ВАЖНО:** Это займет ~40-50 минут и стоит ~$0.03

**Способ A: Локально подключиться к Railway БД (рекомендуется)**

1. Получи `DATABASE_URL` из Railway:
   ```bash
   railway variables
   ```
   Или скопируй из Railway dashboard → PostgreSQL → Connect → Connection URL

2. Экспортируй переменную окружения:
   ```bash
   export DATABASE_URL="postgresql://user:password@host:port/railway"
   ```

3. Запусти генерацию:
   ```bash
   python3 generate_embeddings_simple.py
   ```
   
4. Подтверди генерацию (введи `y`)

**Способ B: Через Railway CLI**

```bash
railway run python3 generate_embeddings_simple.py
```

**Способ C: Постепенная генерация (если боишься таймаутов)**

Можно генерировать партиями, модифицировав скрипт для работы порциями:

```bash
# Например, по 1000 товаров за раз
# Запускай несколько раз, пока все не обработаются
```

---

### Шаг 5: Проверить что всё работает

1. Открой свой production сайт (Railway домен)
2. Попробуй поиск:
   - "кружка" → должна найти чашки, mugs, термокружки
   - "ручка" → должна найти pens, авторучки
   - "USB" → должна найти флешки, кабели, хабы

3. Проверь логи в Railway:
   ```
   Должен увидеть: "✅ Vector search enabled with OpenAI"
   ```

4. Если векторный поиск не работает → автоматически включится fallback на обычный ILIKE

---

## 🔧 Альтернативный подход: Миграция БД из локальной

Если не хочешь генерировать embeddings заново на production:

### Вариант: Скопировать данные из локальной БД

1. **Экспортируй только колонку `name_embedding_text`:**
   ```bash
   # Подключись к локальной БД
   psql <LOCAL_DATABASE_URL>
   
   # Экспорти данные
   \copy (SELECT id, name_embedding_text FROM products WHERE name_embedding_text IS NOT NULL) TO 'embeddings_export.csv' CSV HEADER;
   ```

2. **Добавь колонку в Railway БД** (Шаг 3 выше)

3. **Импортируй данные в Railway БД:**
   ```bash
   # Подключись к Railway БД
   psql <RAILWAY_DATABASE_URL>
   
   # Создай временную таблицу
   CREATE TEMP TABLE temp_embeddings (id INTEGER, name_embedding_text TEXT);
   
   # Импортируй данные
   \copy temp_embeddings FROM 'embeddings_export.csv' CSV HEADER;
   
   # Обнови основную таблицу
   UPDATE products p
   SET name_embedding_text = t.name_embedding_text
   FROM temp_embeddings t
   WHERE p.id = t.id;
   
   # Проверь
   SELECT COUNT(*) FROM products WHERE name_embedding_text IS NOT NULL;
   ```

**Плюсы:** Быстро, не нужно генерировать заново  
**Минусы:** Нужны права psql, может быть несовпадение товаров между local и production

---

## 📊 Проверка статуса после деплоя

### Проверить колонку в БД

```sql
-- Подключись к Railway БД
psql <RAILWAY_DATABASE_URL>

-- Проверь что колонка существует
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'products' AND column_name = 'name_embedding_text';

-- Посчитай сколько товаров с embeddings
SELECT 
    COUNT(*) as total_products,
    COUNT(name_embedding_text) as with_embeddings,
    COUNT(*) - COUNT(name_embedding_text) as without_embeddings
FROM products;
```

### Проверить логи Railway

В Railway dashboard → Logs → смотри на запуск:
```
✅ Vector search enabled with OpenAI
или
⚠️ Vector search disabled: No OpenAI API key
```

---

## ⚠️ Что может пойти не так

### Проблема 1: OpenAI API ключ не работает
**Симптом:** В логах `⚠️ Vector search disabled`  
**Решение:** Проверь что `OPENAI_API_KEY` добавлен в Railway Variables

### Проблема 2: Колонка не существует
**Симптом:** Ошибка `column "name_embedding_text" does not exist`  
**Решение:** Запусти Шаг 3 (добавление колонки)

### Проблема 3: Embeddings не сгенерированы
**Симптом:** Поиск работает, но как обычный (не находит синонимы)  
**Решение:** Запусти Шаг 4 (генерация embeddings)

### Проблема 4: Таймаут при генерации
**Симптом:** Railway отключает соединение через 10-15 минут  
**Решение:** Используй локальное подключение к Railway БД (Способ A в Шаге 4)

---

## 🎯 Рекомендуемый порядок действий

### Самый простой и безопасный путь:

1. ✅ **Добавь `OPENAI_API_KEY` в Railway** (Шаг 1)
2. ✅ **Запушь код в GitHub** (Шаг 2) → Railway автоматически задеплоит
3. ✅ **Добавь колонку через Railway CLI** (Шаг 3, Вариант A)
4. ✅ **Скопируй embeddings из локальной БД** (Альтернативный подход)
   - Это быстрее чем генерировать заново (2 минуты vs 50 минут)
   - Не тратишь лишние API вызовы OpenAI
5. ✅ **Проверь что всё работает** (Шаг 5)

### Итого времени: ~15-20 минут

---

## 📝 Checklist перед деплоем

- [ ] `OPENAI_API_KEY` добавлен в Railway Variables
- [ ] `.env` в `.gitignore` (уже есть ✅)
- [ ] `openai` и `python-dotenv` в `requirements.txt` (уже есть ✅)
- [ ] Код закоммичен и запушен в GitHub
- [ ] Railway автоматически задеплоил изменения
- [ ] Колонка `name_embedding_text` добавлена в production БД
- [ ] Embeddings сгенерированы (или скопированы из локальной БД)
- [ ] Проверил что поиск работает на production

---

## 🎉 После успешного деплоя

Векторный поиск заработает автоматически для всех пользователей!

**Graceful fallback гарантирует:**
- Если OpenAI недоступен → обычный ILIKE поиск
- Если embeddings не найдены → обычный ILIKE поиск
- Проект **всегда** работает, даже при сбоях AI

**Стоимость эксплуатации:**
- ~$0.000001 за каждый поисковый запрос
- При 1000 запросов в день = $0.001/день = $0.30/месяц

**Практически бесплатно!** 🚀

---

## 📞 Поддержка

Если возникнут вопросы:
- Проверь логи в Railway dashboard
- Проверь статус БД через `psql`
- Проверь что все переменные окружения на месте

**Документация:**
- VECTOR_SEARCH_QUICKSTART.md - быстрый старт
- VECTOR_SEARCH_READY.md - полная документация
- VECTOR_SEARCH_SETUP.md - техническая инструкция

**Версия:** 1.0.0  
**Дата:** 10 октября 2025


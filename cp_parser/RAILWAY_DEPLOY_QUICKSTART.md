# 🚀 Railway Деплой - Краткая инструкция

**Время: ~15-20 минут**

---

## ⚡ Быстрый путь (рекомендуется)

### 1. Добавь OpenAI ключ в Railway (1 мин)

Railway Dashboard → Твой сервис → **Variables** → Добавь:
```
OPENAI_API_KEY = sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

### 2. Закоммить и запушить код (2 мин)

```bash
cd /Users/bakirovresad/Downloads/Reshad\ 1/projects/cp_parser

git add -A
git commit -m "✨ Добавлен AI векторный поиск с graceful fallback"
git push origin main
```

Railway автоматически задеплоит! 🚀

---

### 3. Добавь колонку в Railway БД (2 мин)

**Вариант A: Через psql (быстрее)**

```bash
# Получи DATABASE_URL из Railway Dashboard → PostgreSQL → Connect
psql postgresql://postgres:...@...railway.app:5432/railway

# В psql выполни:
ALTER TABLE products ADD COLUMN IF NOT EXISTS name_embedding_text TEXT;

# Проверь:
SELECT COUNT(*) FROM products WHERE name_embedding_text IS NULL;

# Выход
\q
```

**Вариант B: Через Python скрипт**

```bash
# Экспортируй URL Railway БД
export DATABASE_URL="postgresql://postgres:...railway.app:5432/railway"

# Запусти скрипт
python3 setup_embeddings_simple.py
```

---

### 4. Скопируй embeddings в Railway БД (10-15 мин)

```bash
# Добавь в .env Railway БД URL
echo 'RAILWAY_DATABASE_URL="postgresql://postgres:...railway.app:5432/railway"' >> .env

# Запусти копирование (2 минуты)
python3 copy_embeddings_to_railway.py

# Или сгенерируй заново (50 минут, $0.03)
# export DATABASE_URL="postgresql://postgres:...railway.app:5432/railway"
# python3 generate_embeddings_simple.py
```

---

### 5. Проверь что работает (1 мин)

1. Открой сайт на Railway
2. Попробуй поиск: **"кружка"** → должна найти чашки, mugs
3. Проверь Railway Logs → должен быть: `✅ Vector search enabled`

---

## 🎯 Итого

✅ **15-20 минут** и векторный поиск работает на production!

---

## ⚠️ Если что-то пошло не так

### OpenAI ключ не работает
→ Проверь что добавлен в Railway Variables (не в .env файл!)

### Колонка не существует
→ Запусти Шаг 3 заново

### Embeddings не работают
→ Проверь в Railway БД:
```sql
SELECT COUNT(name_embedding_text) FROM products;
```
Должно быть > 0

### Fallback на обычный поиск
→ Это нормально! Graceful fallback гарантирует что проект всегда работает

---

## 📖 Подробная документация

→ **RAILWAY_DEPLOY_VECTOR_SEARCH.md** - полная инструкция со всеми вариантами


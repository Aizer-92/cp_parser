# 🚀 Векторный поиск - Быстрый старт

## За 5 минут

### 1️⃣ Получите OpenAI API ключ
https://platform.openai.com/api-keys

### 2️⃣ Добавьте в Railway Variables
```
OPENAI_API_KEY=sk-proj-ваш_ключ
```

### 3️⃣ Установите pgvector (Railway Query Console)
```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE products ADD COLUMN name_embedding vector(1536);
CREATE INDEX products_name_embedding_idx ON products 
USING hnsw (name_embedding vector_cosine_ops);
```

### 4️⃣ Сгенерируйте embeddings

**Локально:**
```bash
cd /Users/bakirovresad/Downloads/Reshad\ 1/projects/cp_parser
python3 generate_embeddings.py
```

**Или через Railway:**
Подключитесь к Railway database и запустите скрипт.

---

## ✅ Проверка

Откройте веб-интерфейс и найдите в логах:

```
✅ [APP] Векторный поиск доступен (OpenAI)
```

Попробуйте поискать:
- "рюкзак" → найдет backpack
- "кружка" → найдет mug, чашка

---

## ⚠️ Если что-то не работает

**Не переживайте!** Проект продолжит работать с обычным поиском.

Подробности: [VECTOR_SEARCH_SETUP.md](./VECTOR_SEARCH_SETUP.md)

---

## 💰 Стоимость

~$0.50-1.00/месяц при активном использовании

---

## 📚 Документация

- [VECTOR_SEARCH_SETUP.md](./VECTOR_SEARCH_SETUP.md) - Подробная установка
- [VECTOR_SEARCH_CHANGELOG.md](./VECTOR_SEARCH_CHANGELOG.md) - Что изменилось

---

**Готово!** 🎉


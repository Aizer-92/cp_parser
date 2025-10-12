# ⚡ pgvector Quickstart - Быстрый старт

## 🎯 Цель
Мигрировать текстовые embeddings (13,710 шт) в отдельную pgvector БД для:
- ⚡ **10-50x быстрее** поиска
- 💾 Меньше нагрузки на основную БД
- 🛡️ Безопаснее (отдельная БД)

---

## 🚀 Три команды для старта

```bash
# 1. Настроить pgvector БД (создать таблицу и индексы)
python3 setup_pgvector_db.py

# 2. Мигрировать 13,710 embeddings (~3 минуты)
python3 migrate_embeddings_to_pgvector.py

# 3. Готово! Теперь поиск работает через pgvector
```

---

## 📋 Переменные окружения

Добавь в `.env` или экспортируй:

```bash
# Основная БД (расшарена из Railway)
export DATABASE_URL_PRIVATE="postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway"

# Векторная БД (новая)
export VECTOR_DATABASE_URL="postgresql://postgres:Q3Kq3SG.LCSQYpWcc333JlUpsUfJOxfG@switchback.proxy.rlwy.net:53625/railway"

# OpenAI (уже есть)
export OPENAI_API_KEY="sk-proj-..."
```

---

## ✅ Проверка результата

После миграции проверь:

```bash
# Подключись к pgvector БД
psql "postgresql://postgres:Q3Kq3SG.LCSQYpWcc333JlUpsUfJOxfG@switchback.proxy.rlwy.net:53625/railway"

# Проверь количество записей
SELECT COUNT(*) FROM product_embeddings;
-- Должно быть: 13710

# Тестовый поиск
SELECT product_id, product_name, 
       1 - (name_embedding <=> (SELECT name_embedding FROM product_embeddings LIMIT 1)) as similarity
FROM product_embeddings
ORDER BY similarity DESC
LIMIT 5;
```

---

## 🎉 Что дальше?

После успешной миграции:

1. **Модифицируй app.py** - используй pgvector для поиска
2. **Тестируй локально** - поиск должен быть в 10x быстрее
3. **Деплой на Railway** - добавь `VECTOR_DATABASE_URL` в Variables
4. **Image embeddings** - делай по тому же принципу

---

## 📊 Ожидаемые результаты

```
МИГРАЦИЯ:
✅ Обработано: 13,710 товаров
✅ Время: ~180 секунд
✅ Скорость: ~76 embeddings/сек

ПОИСК:
⚡ Старый способ: 2-5 секунд
⚡ pgvector: 0.1-0.5 секунд (10-50x быстрее!)
```

---

**Готов начать?** Запускай команды выше! 🚀


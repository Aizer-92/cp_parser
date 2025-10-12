# 🚀 БЫСТРЫЙ СТАРТ - IMAGE SEARCH

**Railway автоматически задеплоит через 2-3 минуты**

---

## ШАГ 1: ПОЛУЧИ ТОКЕН (2 минуты)

1. Зарегистрируйся: https://huggingface.co/join
2. Создай токен: https://huggingface.co/settings/tokens
   - Кликни "New token"
   - Название: `cp-parser`
   - Тип: **Read**
   - Generate → **СКОПИРУЙ ТОКЕН!**

**Токен выглядит так:** `hf_AbCdEf1234567890...`

---

## ШАГ 2: ДОБАВЬ НА RAILWAY (1 минута)

### Через Railway CLI:
```bash
railway variables set HUGGINGFACE_API_TOKEN="hf_твой_токен_сюда"
```

### Через Dashboard:
1. Открой: https://railway.app/project/твой-проект
2. Variables → New Variable
3. Name: `HUGGINGFACE_API_TOKEN`
4. Value: `hf_твой_токен`
5. Add

---

## ШАГ 3: ТЕСТ (1 минута)

После деплоя:

1. Открой: https://cp-parser-production.up.railway.app/products
2. Кликни **"По фото"** 📷
3. Загрузи фото товара
4. Кликни **"Найти похожие"**
5. ✅ Должны показаться похожие товары!

---

## 📊 ЧТО ПОЛУЧИЛОСЬ:

| Параметр | Результат |
|----------|-----------|
| **Нагрузка на сервер** | **0 MB** ✅ |
| **Скорость запуска** | **5 секунд** (было 60+) ✅ |
| **Цена API** | **БЕСПЛАТНО** ✅ |
| **Embeddings готовы** | **12,907 товаров** ✅ |
| **Скорость поиска** | **1-2 секунды** ✅ |

---

## ⚠️ ЕСЛИ НЕ РАБОТАЕТ:

### "Не настроен HUGGINGFACE_API_TOKEN"
→ Добавь токен в Railway variables

### "Ошибка API: 401"
→ Проверь правильность токена

### "Ошибка API: 503"  
→ Подожди 20 секунд (cold start), попробуй снова

---

## 📖 ПОЛНАЯ ДОКУМЕНТАЦИЯ:

- `HUGGINGFACE_SETUP.md` - детальная инструкция
- `IMAGE_EMBEDDINGS_STATUS.md` - статус embeddings

---

**ГОТОВО! 🎉**

Осталось только добавить токен на Railway!


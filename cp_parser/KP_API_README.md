# ✅ БАЗА + API ДЛЯ КП - ГОТОВО!

## 📊 ЧТО СОЗДАНО:

### 1. База Данных: `kp_items`

**Таблица для хранения товаров в КП:**
```sql
CREATE TABLE kp_items (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    product_id INTEGER NOT NULL REFERENCES products(id),
    price_offer_id INTEGER NOT NULL REFERENCES price_offers(id),
    quantity INTEGER DEFAULT 1,
    user_comment TEXT,
    added_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, price_offer_id)
)
```

**Индексы:**
- `idx_kp_items_session_id` - быстрый поиск по сессии
- `idx_kp_items_session_price` - проверка "товар в КП?"

**Создание:**
```bash
python3 database/create_kp_items_table.py
```

---

### 2. API Endpoints

Все эндпоинты в `web_interface/app.py`:

#### POST `/api/kp/add`
**Добавляет конкретный вариант цены в КП**

Request:
```json
{
  "product_id": 123,
  "price_offer_id": 456
}
```

Response:
```json
{
  "success": true,
  "message": "Добавлено в КП: Кружка (500 шт, Highway ЖД)",
  "kp_count": 5
}
```

#### GET `/api/kp`
**Получает все товары в КП**

Response:
```json
{
  "success": true,
  "kp_items": [
    {
      "kp_item_id": 1,
      "quantity": 1,
      "added_at": "2024-10-12T13:30:00",
      "product": {
        "id": 123,
        "name": "Кружка керамическая",
        "description": "...",
        "image_url": "https://..."
      },
      "price_offer": {
        "id": 456,
        "quantity": 500,
        "route": "Highway ЖД",
        "price_usd": 25.50,
        "price_rub": 2550,
        "delivery_days": 14
      }
    }
  ],
  "total_items": 5
}
```

#### DELETE `/api/kp/remove/<kp_item_id>`
**Удаляет товар из КП**

Response:
```json
{
  "success": true,
  "message": "Удалено из КП",
  "kp_count": 4
}
```

#### DELETE `/api/kp/clear`
**Очищает весь КП**

Response:
```json
{
  "success": true,
  "message": "КП очищен",
  "kp_count": 0
}
```

#### POST `/api/kp/check`
**Проверяет какие варианты уже в КП**

Request:
```json
{
  "price_offer_ids": [1, 5, 10, 20]
}
```

Response:
```json
{
  "success": true,
  "in_kp": [1, 10]
}
```

---

## 🎯 КЛЮЧЕВЫЕ ОСОБЕННОСТИ:

1. **Добавление по price_offer_id** - пользователь выбирает конкретный вариант (тираж + маршрут)
2. **Уникальность** - один price_offer может быть добавлен только раз
3. **Session-based** - корзина привязана к сессии браузера (cookie)
4. **Изображения** - приоритет столбцу A, если нет - первое доступное
5. **Graceful fallback** - если нет image_url, формируется из image_filename

---

## 🧪 ТЕСТИРОВАНИЕ:

```bash
# Запуск сервера
cd web_interface
python3 app.py

# В другом терминале - тест API
python3 test_kp_api.py
```

---

## 📝 ЧТО ДАЛЬШЕ:

### ✅ ГОТОВО:
- [x] Таблица `kp_items`
- [x] API `/api/kp/*`
- [x] Session management
- [x] Тестовый скрипт

### ⏳ СЛЕДУЮЩИЕ ШАГИ:
- [ ] UI: кнопки "Добавить в КП" на странице товара
- [ ] UI: иконка КП в шапке с счетчиком
- [ ] UI: страница `/kp` для просмотра КП
- [ ] Генерация PDF
- [ ] Генерация Excel
- [ ] Генерация Google Sheets

---

## 🔑 ВАЖНО:

**Session ID хранится в cookie и сохраняется между визитами:**
```python
if 'session_id' not in session:
    session['session_id'] = str(uuid.uuid4())
    session.permanent = True
```

**Изображения всегда в столбце A (приоритет):**
```sql
ORDER BY CASE WHEN pi.column_number = 1 THEN 0 ELSE 1 END, pi.id LIMIT 1
```

**Graceful image handling:**
- Сначала ищем `image_url`
- Если нет → формируем из `image_filename`
- Всегда возвращаем хотя бы одно изображение если оно есть

---

**API готово к использованию! 🚀**




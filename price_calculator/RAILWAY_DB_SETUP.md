# Railway PostgreSQL - Настройка подключения

## Утилита railway_db.py

Прямое подключение к PostgreSQL на Railway для управления базой данных.

---

## 🔧 Настройка

### 1. Установите переменные окружения

**Для текущей сессии терминала:**

```bash
export RAILWAY_DB_HOST="gondola.proxy.rlwy.net"
export RAILWAY_DB_PORT="13805"
export RAILWAY_DB_USER="postgres"
export RAILWAY_DB_PASSWORD="your_password_here"  # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ ПАРОЛЬ!
export RAILWAY_DB_NAME="railway"
```

### 2. Или создайте файл `.env.railway.local` (НЕ коммитить!)

```bash
# .env.railway.local (добавить в .gitignore!)
RAILWAY_DB_HOST=gondola.proxy.rlwy.net
RAILWAY_DB_PORT=13805
RAILWAY_DB_USER=postgres
RAILWAY_DB_PASSWORD=your_password_here
RAILWAY_DB_NAME=railway
```

Загрузите переменные:
```bash
export $(cat .env.railway.local | xargs)
```

---

## 📋 Использование

### Тест подключения
```bash
python3 railway_db.py test
```

### Добавить "Новая категория"
```bash
python3 railway_db.py add_new_category
```

### Список всех категорий
```bash
python3 railway_db.py list
```

### Получить данные категории
```bash
python3 railway_db.py get "кружки"
```

---

## 🔍 Примеры использования

### Поиск категории
```bash
$ python3 railway_db.py get "Новая категория"
🔍 Поиск категории: Новая категория
✅ Подключение к Railway PostgreSQL установлено

✅ Найдена категория:
   ID: 121
   Category: Новая категория
   Material: 

   Data:
     vat_rate: 20%
     duty_rate: 0%
     description: Для товаров, не распознанных автоматически...
```

### Список категорий
```bash
$ python3 railway_db.py list | head -20
📋 Список категорий в Railway PostgreSQL:
✅ Подключение к Railway PostgreSQL установлено

Всего категорий: 105

    5. сумка
       └─ кожа
    6. кружка
       └─ керамика, фарфор
...
```

---

## ⚠️ БЕЗОПАСНОСТЬ

- **НЕ КОММИТИТЬ** файлы с credentials в Git!
- Добавьте в `.gitignore`:
  ```
  .env.railway.local
  *_credentials.txt
  ```
- Используйте переменные окружения
- Пароль хранится только локально

---

## 🛠️ Функции

| Функция | Описание |
|---------|----------|
| `get_railway_connection()` | Создает подключение к Railway PostgreSQL |
| `execute_query(query, params, fetch)` | Выполняет SQL запросы |
| `add_new_category_to_railway()` | Добавляет "Новая категория" в БД |
| `list_categories()` | Список всех категорий |
| `get_category(name)` | Получает данные категории |

---

## 📦 Требования

- Python 3.6+
- psycopg2 (уже установлен в проекте)

---

## 🔗 Подключение

**Raw psql command для справки:**
```bash
PGPASSWORD=your_password psql -h gondola.proxy.rlwy.net -U postgres -p 13805 -d railway
```

**Python через railway_db.py:**
```python
from railway_db import get_railway_connection

conn = get_railway_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM categories LIMIT 5")
results = cursor.fetchall()
```









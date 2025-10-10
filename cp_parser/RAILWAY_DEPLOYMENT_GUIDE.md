# 🚀 Руководство по пополнению Railway PostgreSQL

**Дата создания**: 08.10.2025  
**Версия**: 1.0

---

## 📋 Оглавление

1. [Обзор процесса](#обзор-процесса)
2. [Пошаговая инструкция](#пошаговая-инструкция)
3. [Важные правила](#важные-правила)
4. [Структура данных](#структура-данных)
5. [Проверка результатов](#проверка-результатов)

---

## 🎯 Обзор процесса

### Архитектура системы

```
┌─────────────────┐      ┌──────────────┐      ┌─────────────────┐
│  Google Sheets  │ ───> │  Локальный   │ ───> │    Railway      │
│   (источник)    │      │  PostgreSQL  │      │   PostgreSQL    │
└─────────────────┘      └──────────────┘      └─────────────────┘
        │                        │                       │
        │                        ▼                       │
        │                ┌──────────────┐               │
        └───────────────>│  FTP Cloud   │<──────────────┘
                         │  (images)    │
                         └──────────────┘
```

### Этапы миграции

1. **Парсинг** → Извлечение данных из Google Sheets
2. **Загрузка изображений** → FTP облако
3. **Миграция данных** → Railway PostgreSQL (с защитой от дублей)

---

## 📝 Пошаговая инструкция

### Шаг 1: Парсинг новых проектов

```bash
# 1. Валидация структуры таблиц
python3 validate_all_1586.py

# 2. Парсинг валидных таблиц
python3 parse_validated_272_files.py

# Ожидаемый результат:
# - Товары добавлены в локальную БД
# - Предложения (price_offers) добавлены
# - Изображения сохранены локально в storage/images
# - Метаданные изображений в БД
```

**Статус проектов после парсинга:**
- `pending` → `completed` (успешно)
- `pending` → `error` (ошибка парсинга)

---

### Шаг 2: Загрузка изображений на облако

```bash
# Загрузка изображений на FTP
python3 upload_images_multithread.py
```

**Важно**: Этот шаг ОБЯЗАТЕЛЕН перед миграцией!

**Что происходит:**
1. Скрипт читает `valid_files_list.txt` (список проектов)
2. Извлекает `project_id` из имен файлов
3. Находит все изображения для этих проектов в локальной БД
4. Загружает ТОЛЬКО изображения без `image_url` (новые)
5. Обновляет `image_url` в БД после загрузки

**FTP настройки:**
```python
FTP_HOST = 'ftp.ru1.storage.beget.cloud'
FTP_REMOTE_DIR = '/73d16f7545b3-promogoods/images'
FTP_BASE_URL = 'https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/'
```

**Производительность:**
- Скорость: ~3.0-3.5 изображений/сек
- Потоки: 3 (настраивается в `MAX_WORKERS`)

---

### Шаг 3: Миграция данных на Railway

```bash
# Миграция всех новых данных
python3 migrate_new_products_to_railway.py
```

**Что мигрируется:**
- ✅ Проекты (projects)
- ✅ Товары (products)
- ✅ Предложения (price_offers)
- ✅ Метаданные изображений (product_images)

**Защита от дублей:**
- Перед вставкой проверяется наличие записи по `id`
- Существующие записи пропускаются
- Счетчики: `migrated` (новые) и `skipped` (пропущенные)

**Railway URL:**
```
postgresql://postgres:wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB@centerbeam.proxy.rlwy.net:26590/railway
```

---

### Шаг 4: Проверка результатов

```bash
# Проверка синхронизации данных
python3 check_railway_data.py
```

**Что проверяется:**
- Количество проектов (локально vs Railway)
- Количество товаров
- Количество предложений
- Количество изображений
- Примеры последних товаров для ручной проверки

---

## ⚠️ Важные правила

### 1. Порядок выполнения

```mermaid
graph LR
    A[Парсинг] --> B[Загрузка изображений]
    B --> C[Миграция на Railway]
    C --> D[Проверка]
```

**НИКОГДА не пропускайте загрузку изображений!**

### 2. Проверка перед миграцией

```bash
# Убедитесь, что ВСЕ изображения загружены
python3 << 'EOF'
import sys
from pathlib import Path
from sqlalchemy import text
sys.path.insert(0, str(Path.cwd()))
from database.postgresql_manager import PostgreSQLManager

db = PostgreSQLManager()
with db.get_session() as session:
    no_url = session.execute(text("""
        SELECT COUNT(*) FROM product_images 
        WHERE image_url IS NULL OR image_url = ''
    """)).scalar()
    
    if no_url > 0:
        print(f"❌ СТОП! {no_url} изображений без URL!")
        print("   Сначала загрузите изображения на облако!")
        sys.exit(1)
    else:
        print("✅ Все изображения загружены на облако")
EOF
```

### 3. Очистка локальных изображений

```bash
# ТОЛЬКО после успешной миграции!
rm -rf storage/images
mkdir -p storage/images
```

**Освобождается**: ~15 GB дискового пространства

### 4. Список проектов

Скрипт `migrate_new_products_to_railway.py` использует файл:
- **`valid_files_list.txt`** - список ВСЕХ валидных проектов

Этот файл автоматически создается при валидации.

---

## 📊 Структура данных

### Таблица: `projects`

```sql
id                  INTEGER PRIMARY KEY
table_id            TEXT
project_name        TEXT
google_sheets_url   TEXT
parsing_status      TEXT    -- 'pending', 'completed', 'error'
parsed_at           TEXT
created_at          TEXT
updated_at          TEXT
```

### Таблица: `products`

```sql
id                  INTEGER PRIMARY KEY
project_id          INTEGER (FK)
name                TEXT NOT NULL
description         TEXT
custom_field        TEXT
created_at          TEXT
updated_at          TEXT
```

### Таблица: `price_offers`

```sql
id                  INTEGER PRIMARY KEY
product_id          INTEGER (FK)
quantity            BIGINT
price_usd           TEXT
price_rub           TEXT
route               TEXT    -- 'ЖД', 'АВИА'
delivery_time_days  INTEGER
created_at          TEXT
updated_at          TEXT
```

### Таблица: `product_images`

```sql
id                  INTEGER PRIMARY KEY
product_id          INTEGER (FK)
table_id            TEXT
image_filename      TEXT
image_url           TEXT    -- URL на FTP облаке
cell_position       TEXT
row_number          INTEGER
column_number       INTEGER
created_at          TEXT
updated_at          TEXT
```

---

## 🔍 Проверка результатов

### 1. Проверка в pgAdmin/DBeaver

**Подключение:**
- Host: `centerbeam.proxy.rlwy.net`
- Port: `26590`
- Database: `railway`
- User: `postgres`
- Password: `wpqIxsBFYwmaNBFmCtBahhIMVSSskeiB`

### 2. SQL запросы для проверки

```sql
-- Общая статистика
SELECT 
    (SELECT COUNT(*) FROM projects WHERE parsing_status = 'completed') as completed_projects,
    (SELECT COUNT(*) FROM projects WHERE parsing_status = 'pending') as pending_projects,
    (SELECT COUNT(*) FROM products) as total_products,
    (SELECT COUNT(*) FROM price_offers) as total_offers,
    (SELECT COUNT(*) FROM product_images) as total_images;

-- Последние 10 товаров
SELECT 
    p.id,
    p.project_id,
    p.name,
    (SELECT COUNT(*) FROM price_offers WHERE product_id = p.id) as offers,
    (SELECT COUNT(*) FROM product_images WHERE product_id = p.id) as images
FROM products p
ORDER BY p.id DESC
LIMIT 10;

-- Проверка изображений (все должны иметь URL)
SELECT COUNT(*) 
FROM product_images 
WHERE image_url IS NULL OR image_url = '';
-- Ожидаемый результат: 0

-- Товары без предложений (должно быть минимум)
SELECT COUNT(*) 
FROM products p 
LEFT JOIN price_offers po ON p.id = po.product_id
WHERE po.id IS NULL;
```

### 3. Проверка изображений на FTP

Формат URL:
```
https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/{filename}.png
```

Пример:
```
https://ru1.storage.beget.cloud/73d16f7545b3-promogoods/images/1MaeobniO05uUYXDk6cPxy1qEMsScyV4mGM3X4ENGeZU_A4_abc123.png
```

---

## 🐛 Troubleshooting

### Проблема: "0 новых товаров" при миграции

**Причина**: Данные уже мигрированы ранее

**Решение**: Проверьте статус в Railway:
```bash
python3 check_railway_data.py
```

### Проблема: Изображения не отображаются

**Причина**: `image_url` пустой или неверный

**Решение**:
1. Проверьте загрузку: `python3 check_upload_progress.py`
2. Перезагрузите: `python3 upload_images_multithread.py`

### Проблема: Ошибка подключения к Railway

**Причина**: Неверный URL или сетевые проблемы

**Решение**:
1. Проверьте URL в скрипте
2. Проверьте доступность: `ping centerbeam.proxy.rlwy.net`
3. Попробуйте через VPN (если ограничения по региону)

### Проблема: Медленная загрузка изображений

**Решение**: Увеличьте количество потоков
```python
# В upload_images_multithread.py
MAX_WORKERS = 5  # Было 3
```

---

## 📈 Текущая статистика (08.10.2025)

```
Проекты:      3,261
├─ completed: 1,825 (56.0%)
├─ pending:   1,431 (43.9%)
└─ error:         5 (0.2%)

Товары:       8,717
Предложения:  24,128
Изображения:  35,769 (все на FTP)
```

---

## 🔐 Безопасность

### Секреты

**НИКОГДА не коммитьте:**
- FTP пароли
- Railway URL с паролем
- API ключи

**Используйте:**
- `.env` файлы
- Environment variables
- Приватные репозитории

### Backup

Перед миграцией:
```bash
# Создайте snapshot локальной БД
pg_dump your_local_db > backup_$(date +%Y%m%d).sql
```

---

## 📝 Changelog

### v1.0 (08.10.2025)
- ✅ Первая версия документации
- ✅ Процесс миграции 272 проектов
- ✅ 910 товаров, 2,583 предложения, 6,618 изображений
- ✅ FTP загрузка с многопоточностью (3.0-3.5 img/s)
- ✅ Защита от дублей при миграции

---

**Автор**: Reshad  
**Контакт**: @promogoods  
**Проект**: Commercial Proposals Parser




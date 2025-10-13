# CP Parser - Веб-интерфейс

Веб-приложение для просмотра и управления спарсенными коммерческими предложениями.

## 🌐 Адрес

**Production:** https://headcp.up.railway.app

## 📁 Структура проекта

```
cp_parser/
├── web_interface/          # Flask веб-приложение
│   ├── app.py             # Основное приложение
│   ├── api_kp.py          # API для работы с КП
│   ├── config.py          # Конфигурация
│   ├── models.py          # ORM модели
│   ├── templates/         # HTML шаблоны
│   └── static/            # CSS/JS/Fonts
│
├── kp_generator_*.py      # Генераторы КП (Excel, PDF, Google Sheets)
├── check_broken_images.py # Проверка битых изображений
├── compress_final.py      # Сжатие изображений (WebP)
├── oauth_authorize.py     # OAuth для Google API
│
├── railway.json           # Конфигурация Railway
├── requirements.txt       # Python зависимости
└── README.md             # Этот файл
```

## 🚀 Возможности

### Просмотр данных
- ✅ **Проекты** - список всех спарсенных проектов
- ✅ **Товары** - карточки товаров с изображениями
- ✅ **Ценовые предложения** - тиражи и цены (USD/RUB)
- ✅ **Поиск** - по названиям, артикулам, регионам
- ✅ **Фильтры** - по шаблонам, датам, наличию образцов
- ✅ **Planfix интеграция** - ссылки на задачи

### Генерация КП
- 📄 **Excel** - экспорт в .xlsx
- 📄 **PDF** - красивые PDF с изображениями
- 📄 **Google Sheets** - создание в Google Drive
- 🎨 **Кастомизация** - выбор товаров, тиражей, настройка формата

### Управление изображениями
- 🖼️ **Облачное хранилище** - Beget S3/FTP
- ✅ **99.2% покрытие** - почти все товары с фото
- 🗜️ **WebP сжатие** - автоматическая оптимизация
- 🔧 **Автоисправление** - замена битых ссылок

## 🛠️ Технологии

- **Backend:** Flask, SQLAlchemy, PostgreSQL
- **Frontend:** Jinja2, Vanilla JS, Tailwind CSS
- **Storage:** Beget S3/FTP для изображений
- **Deploy:** Railway (автодеплой из GitHub)
- **Google API:** Sheets API v4, Drive API

## ⚙️ Настройка локально

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка БД

```bash
# Создать БД PostgreSQL
createdb cp_parser

# Или использовать Railway БД
export DATABASE_URL="postgresql://user:pass@host:port/db"
```

### 3. Настройка Google API

```bash
# Положить service_account.json в корень
# Или настроить OAuth через oauth_authorize.py
python oauth_authorize.py
```

### 4. Запуск

```bash
cd web_interface
python app.py
```

Откроется на http://localhost:5000

## 📊 База данных

**Таблицы:**
- `projects` - проекты (Google Sheets ID, регион, шаблон)
- `products` - товары (название, описание, артикул)
- `price_offers` - ценовые предложения (тираж, цены, сроки)
- `product_images` - изображения (URL, позиция, главное фото)

**Схема:** См. `/web_interface/models.py`

## 🎯 Основные маршруты

- `/` - Главная (статистика)
- `/projects` - Список проектов
- `/project/<id>` - Детали проекта
- `/products` - Список товаров
- `/product/<id>` - Детали товара
- `/kp` - Генератор КП

## 🔧 Утилиты

### Проверка битых изображений

```bash
python check_broken_images.py
```

### Сжатие изображений

```bash
# Когда FTP доступен
python compress_final.py
```

Инструкция: `HOW_TO_RESUME_COMPRESSION.md`

## 📝 Логи

Логи приложения доступны в Railway Dashboard или через CLI:

```bash
railway logs
```

## 🔗 Связанные проекты

- **cp_parser_core** - ядро парсинга (парсеры шаблонов)
- **price_calculator** - калькулятор цен для товаров

## 📊 Статистика

**По состоянию на 13.10.2025:**
- ✅ Проектов: 3,265
- ✅ Товаров: 19,450+
- ✅ Изображений: 49,674 (99.2% покрытие)
- ✅ Размер БД: ~2 GB
- ✅ FTP Storage: ~20 GB (после оптимизации)

## 🐛 Известные проблемы

- ⏸️ FTP сжатие заблокировано (SSL/TLS issue)
- ⏸️ Ожидается автоматическая WebP генерация

## 📞 Контакты

**Railway:** https://railway.app  
**Beget FTP:** ftp.ru1.storage.beget.cloud  
**Production URL:** https://headcp.up.railway.app

---

**Версия:** 2.0  
**Дата обновления:** 13 октября 2025  
**Статус:** ✅ Production Ready

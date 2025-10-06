# ✅ Чеклист для деплоя на Railway

## Что было исправлено

### 1. ✅ Конфликт с PORT
- **Проблема**: `app.py` использовал жестко заданный порт 5000
- **Решение**: Теперь использует `os.getenv('PORT', 5000)`
- **Файл**: `web_interface/app.py` строка 302

### 2. ✅ PostgreSQL драйвер
- **Проблема**: Отсутствовал `psycopg2` в зависимостях
- **Решение**: Добавлен `psycopg2-binary==2.9.9`
- **Файл**: `web_interface/requirements.txt` строка 10

### 3. ✅ Переменные окружения Railway
- **Проблема**: Хардкод DATABASE_URL
- **Решение**: Используются `DATABASE_PUBLIC_URL` или `DATABASE_URL` из env
- **Файлы**: 
  - `web_interface/config.py` строка 32
  - `database/postgresql_manager.py` строка 17

### 4. ✅ Конфигурация Railway
- **Добавлено**: `railway.toml` с настройками билда и деплоя
- **Добавлено**: `RAILWAY_DEPLOY.md` с инструкциями

### 5. ✅ Навигация
- **Добавлено**: Вкладка "Сырые расчеты" в шапке сайта
- **Ссылка**: https://promo-calculator-production.up.railway.app/
- **Файл**: `web_interface/templates/base.html` строки 34-40

### 6. ✅ Архивирование
- **Архивировано**: Старый интерфейс `web_viewer.py` → `archive/`

## 📋 Переменные окружения для Railway

Railway **автоматически** предоставляет:
- ✅ `DATABASE_URL` - внутренний URL PostgreSQL
- ✅ `DATABASE_PUBLIC_URL` - публичный URL PostgreSQL
- ✅ `PORT` - порт для приложения

Нужно **вручную добавить** в Railway Dashboard:
```
CLOUD_STORAGE_ENABLED=True
S3_BASE_URL=https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods
CLOUD_IMAGES_PREFIX=images/
SECRET_KEY=your-random-secret-key-here
```

## 🚀 Готово к коммиту

Все изменения готовы для коммита в GitHub. Railway автоматически:
1. Обнаружит изменения через GitHub webhook
2. Установит зависимости из `requirements.txt`
3. Запустит приложение через `Procfile`
4. Подключится к PostgreSQL используя `DATABASE_PUBLIC_URL`

## 📊 Статус базы данных

✅ **Полностью мигрирована на Railway PostgreSQL**:
- Projects: 3,261 записей
- Products: 7,967 записей
- Price Offers: 21,545 записей
- Product Images: 23,229 записей
- **Всего: 56,002 записи**

## 🎯 Следующие шаги

1. Закоммитьте изменения в GitHub
2. Railway автоматически начнет деплой
3. Проверьте логи в Railway Dashboard
4. Откройте URL приложения и проверьте работу

## 🔗 Полезные ссылки

- База данных: Railway PostgreSQL (centerbeam.proxy.rlwy.net:26590)
- Изображения: Beget S3 (s3.ru1.storage.beget.cloud)
- Калькулятор: https://promo-calculator-production.up.railway.app/

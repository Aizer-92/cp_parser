# Деплой на Railway

## ✅ Готово к деплою

Приложение полностью адаптировано для Railway и готово к автоматическому деплою через GitHub.

## 📋 Что было сделано

### 1. Исправлен конфликт с PORT
- ✅ `app.py` теперь использует `os.getenv('PORT', 5000)`
- ✅ Railway автоматически установит свой порт через переменную окружения

### 2. Добавлена поддержка PostgreSQL
- ✅ Добавлен `psycopg2-binary==2.9.9` в `requirements.txt`
- ✅ `config.py` использует `DATABASE_PUBLIC_URL` или `DATABASE_URL` из Railway
- ✅ `postgresql_manager.py` использует переменные окружения Railway

### 3. Настроены файлы для Railway
- ✅ `Procfile` - команда запуска через gunicorn
- ✅ `railway.toml` - конфигурация билда и деплоя
- ✅ `requirements.txt` - все зависимости включая PostgreSQL драйвер

## 🚀 Как задеплоить

### Шаг 1: Переменные окружения в Railway
Railway автоматически предоставляет:
- `DATABASE_URL` - внутренний URL базы данных
- `DATABASE_PUBLIC_URL` - публичный URL базы данных
- `PORT` - порт для приложения

Дополнительно установите в Railway Dashboard:
```
CLOUD_STORAGE_ENABLED=True
S3_BASE_URL=https://s3.ru1.storage.beget.cloud/73d16f7545b3-promogoods
CLOUD_IMAGES_PREFIX=images/
SECRET_KEY=your-random-secret-key-here
```

### Шаг 2: Подключите GitHub репозиторий
1. В Railway Dashboard выберите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Выберите ваш репозиторий `cp_parser`
4. Railway автоматически обнаружит `web_interface/` и начнет деплой

### Шаг 3: Проверьте деплой
- Railway автоматически запустит `gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
- Приложение подключится к PostgreSQL используя `DATABASE_PUBLIC_URL`
- Изображения будут загружаться из S3 хранилища

## 📦 Структура проекта

```
web_interface/
├── app.py                    # Главное приложение Flask
├── config.py                 # Конфигурация (использует env vars)
├── requirements.txt          # Зависимости Python
├── Procfile                  # Команда запуска для Railway
├── railway.toml              # Конфигурация Railway
├── database/
│   ├── models.py            # SQLAlchemy модели
│   └── postgresql_manager.py # Менеджер PostgreSQL
└── templates/               # HTML шаблоны
```

## 🔧 Технические детали

### База данных
- Приложение использует PostgreSQL на Railway
- Все 56,002 записи мигрированы:
  - Projects: 3,261
  - Products: 7,967
  - Price Offers: 21,545
  - Product Images: 23,229

### Изображения
- Хранятся в S3 (Beget Cloud Storage)
- 23,229 изображений загружены
- Публичный доступ настроен

### Производительность
- Gunicorn с 4 воркерами
- Connection pooling для PostgreSQL
- Кэширование статики

## ⚠️ Важно

1. **Не коммитьте секреты** - все чувствительные данные через переменные окружения
2. **DATABASE_PUBLIC_URL** - Railway автоматически создаст эту переменную
3. **PORT** - Railway автоматически установит порт, не меняйте в коде

## 🐛 Отладка

Если деплой не работает:

1. Проверьте логи в Railway Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте, что PostgreSQL сервис запущен
4. Проверьте healthcheck: `https://your-app.railway.app/`

## 📊 Мониторинг

Railway предоставляет:
- Логи в реальном времени
- Метрики использования ресурсов
- Автоматические рестарты при сбоях
- Health checks каждые 100 секунд






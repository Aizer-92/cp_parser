# Changelog - Адаптация для Railway

## 2025-10-06 - Подготовка к деплою на Railway

### 🔧 Исправления

1. **Конфликт с PORT** (КРИТИЧНО)
   - Исправлен `app.py`: теперь использует `os.getenv('PORT', 5000)`
   - Railway больше не будет крашиться из-за конфликта портов

2. **PostgreSQL драйвер**
   - Добавлен `psycopg2-binary==2.9.9` в `requirements.txt`
   - Приложение теперь может подключаться к PostgreSQL

3. **Переменные окружения**
   - `config.py`: использует `DATABASE_PUBLIC_URL` или `DATABASE_URL`
   - `postgresql_manager.py`: использует переменные окружения Railway
   - Убран хардкод DATABASE_URL

### ✨ Новые функции

1. **Навигация**
   - Добавлена вкладка "Сырые расчеты" в шапке
   - Ссылка на https://promo-calculator-production.up.railway.app/
   - Открывается в новой вкладке с иконкой

2. **Конфигурация Railway**
   - Создан `railway.toml` с настройками билда
   - Создан `RAILWAY_DEPLOY.md` с инструкциями
   - Создан `DEPLOY_CHECKLIST.md` с чеклистом

### 🗂️ Очистка

1. **Архивирование**
   - Старый `web_viewer.py` перемещен в `archive/`
   - Проект очищен от устаревших файлов

### 📊 База данных

- ✅ Полностью мигрирована на Railway PostgreSQL
- ✅ 56,002 записи успешно перенесены
- ✅ Структура таблиц проверена и совпадает

### 🎯 Готовность к деплою

- ✅ Все зависимости установлены
- ✅ Переменные окружения настроены
- ✅ Procfile готов для Railway
- ✅ Приложение протестировано локально

## Файлы изменены

- `web_interface/app.py` - исправлен PORT
- `web_interface/config.py` - добавлены env vars
- `web_interface/requirements.txt` - добавлен psycopg2
- `web_interface/templates/base.html` - добавлена вкладка
- `database/postgresql_manager.py` - env vars для Railway
- `web_interface/railway.toml` - новый файл
- `RAILWAY_DEPLOY.md` - новый файл
- `DEPLOY_CHECKLIST.md` - новый файл

## Готово к коммиту ✅

Все изменения протестированы и готовы для push в GitHub.
Railway автоматически начнет деплой после коммита.

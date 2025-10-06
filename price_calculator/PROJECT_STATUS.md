# Price Calculator - Статус проекта

**Дата:** 06.10.2025  
**Версия:** 1.0 Production Ready  
**URL:** https://price-calculator-production.up.railway.app/

---

## Статус: ГОТОВ К ПРОДАКШЕНУ

### Основные функции:
- Быстрый расчет цен товаров из Китая
- Точный расчет с детальными параметрами
- История расчетов с возможностью редактирования
- Управление категориями товаров
- Настройки курсов валют и формул
- Расчет себестоимости под контракт с учетом пошлин

---

## Архитектура

### Backend:
- **FastAPI** - основной фреймворк
- **PostgreSQL** (Railway) / SQLite (локально)
- **Модульная структура:**
  - `backend/api/` - API роутеры (auth, calculator, categories, history, settings)
  - `database.py` - работа с БД
  - `price_calculator.py` - бизнес-логика расчетов
  - `load_customs_data.py` - данные по пошлинам

### Frontend:
- **Vue.js 3** (CDN)
- **Компонентная архитектура:**
  - `CategorySelector` - выбор категории
  - `ProductForm` - быстрый расчет
  - `ProductFormPrecise` - точный расчет
  - `ResultsDisplay` - отображение результатов
  - `HistoryPanel` - история расчетов
  - `SettingsPanel` - настройки
  - `CategoriesPanel` - управление категориями

---

## База данных

### Таблицы:
1. **calculations** - история расчетов
   - Основные поля: product_name, category, price_yuan, weight_kg, quantity
   - Результаты: cost_price_rub/usd, sale_price_rub/usd, profit_rub/usd
   - Пошлины: tnved_code, duty_rate, vat_rate, duty_amount_usd, vat_amount_usd

2. **categories** - категории товаров (JSONB)
   - category, material, density, tnved_code
   - rates: rail_base, air_base
   - duty_rate, vat_rate, certificates
   - duty_type (ad_valorem, specific, combined)

---

## Пошлины и сертификация

### Типы пошлин:
- **Ad Valorem** - процент от стоимости (большинство товаров)
- **Specific** - фиксированная ставка за кг/единицу
- **Combined** - больше из двух (текстиль: футболки, худи, плед и т.д.)

### Источники данных:
- ФТС России (официальные ставки)
- Ручная верификация ключевых категорий
- Обновление: октябрь 2025

---

## Конфигурация

### Переменные окружения (Railway):
```
DATABASE_PUBLIC_URL - PostgreSQL URL (автоматически)
PORT - порт приложения (автоматически)
SECRET_KEY - ключ для сессий
```

### Файлы конфигурации:
- `config/calculation_settings.yaml` - параметры формул
- `config/currencies.yaml` - курсы валют
- `config/categories.yaml` - категории (резервная копия)

---

## Деплой

### Railway:
- Автоматический деплой из `main` ветки GitHub
- PostgreSQL база данных
- Healthcheck: `/`
- Логи в реальном времени

### Локальная разработка:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Критические исправления (06.10.2025)

### Проблема: ID категорий = undefined
**Причина:** Старый эндпоинт `/api/categories` в `main.py` блокировал новый модульный роутер

**Решение:**
1. Удален старый эндпоинт (68 строк)
2. Подключен роутер: `app.include_router(categories.router)`
3. Исправлена обработка PostgreSQL JSONB:
   ```python
   result = {'id': category_id, **category_data}
   ```

### Проблема: Миграция БД при каждом деплое
**Решение:** Отключен `init_database()` в `lifespan` - БД уже настроена

---

## Документация

### Основные файлы:
- `README.md` - общее описание проекта
- `FIXES_CATEGORIES_AND_CUSTOMS.md` - детали последних исправлений
- `PROJECT_STATUS.md` (этот файл) - текущий статус

### Архив:
- `archive/` - старые версии, отчеты, бэкапы

---

## Метрики

- **Категорий товаров:** 107
- **Типов доставки:** 2 (ЖД, Авиа)
- **Валют:** 3 (CNY, USD, RUB)
- **Пользователей:** Многопользовательский (с авторизацией)

---

## Следующие шаги

1. **Vue Router** - для навигации между модулями (личные кабинеты, проекты)
2. **Многопользовательский режим** - разделение данных по пользователям
3. **API для мобильных приложений**
4. **Экспорт в Excel/PDF**
5. **Интеграция с 1С**

---

## Контакты

- **GitHub:** https://github.com/Aizer-92/price-calculator
- **Railway:** https://price-calculator-production.up.railway.app/
- **Email:** aizer1992@gmail.com

---

## История версий

### v1.0 (06.10.2025)
- Готов к продакшену
- Исправлены критические баги с ID категорий
- Отключена автоматическая миграция БД
- Модульная архитектура backend
- Управление категориями через UI

### v0.9 (05.10.2025)
- Добавлено управление категориями
- Интеграция пошлин в расчеты
- Расчет себестоимости под контракт

### v0.8 (04.10.2025)
- Рефакторинг backend в модули
- Улучшена обработка ошибок
- Добавлены настройки

---

**Проект готов к использованию! 🚀**

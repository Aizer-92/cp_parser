# Веб-интерфейс для просмотра коммерческих предложений

Современный веб-интерфейс для просмотра результатов парсинга коммерческих предложений с поддержкой Tailwind CSS, пагинации и полнотекстового поиска.

## Возможности

- 📊 **Статистика**: Общая статистика по проектам, товарам, предложениям и изображениям
- 🔍 **Поиск**: Полнотекстовый поиск по названию и описанию товаров
- 📄 **Пагинация**: Удобная навигация по большим спискам
- 🖼️ **Изображения**: Просмотр изображений товаров
- 💰 **Цены**: Отображение ценовых предложений с маршрутами и сроками
- 🎯 **Образцы**: Информация о ценах и сроках изготовления образцов
- 📱 **Адаптивность**: Современный дизайн с Tailwind CSS

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Убедитесь, что база данных находится в правильном месте:
```
../database/commercial_proposals.db
```

3. Убедитесь, что изображения находятся в правильном месте:
```
../storage/images/
```

## Запуск

### Локально
```bash
python app.py
```

### Для продакшена
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Деплой

### Railway
1. Подключите репозиторий к Railway
2. Установите переменные окружения (если нужно)
3. Railway автоматически установит зависимости и запустит приложение

### Heroku
1. Создайте Procfile:
```
web: gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

2. Деплой:
```bash
git push heroku main
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Структура

```
web_interface/
├── app.py              # Основное приложение Flask
├── requirements.txt    # Зависимости Python
├── README.md          # Документация
├── templates/         # HTML шаблоны
│   ├── base.html
│   ├── index.html
│   ├── products_list.html
│   ├── product_detail.html
│   ├── projects_list.html
│   └── project_detail.html
└── static/           # Статические файлы (CSS, JS, изображения)
    ├── css/
    ├── js/
    └── images/
```

## API Endpoints

- `GET /` - Главная страница
- `GET /products` - Список товаров с пагинацией и поиском
- `GET /projects` - Список проектов
- `GET /product/<id>` - Детальная информация о товаре
- `GET /project/<id>` - Детальная информация о проекте
- `GET /images/<filename>` - Отдача изображений
- `GET /api/stats` - API статистики
- `GET /api/search` - API поиска товаров

## Переменные окружения

- `FLASK_ENV` - Режим Flask (development/production)
- `DATABASE_URL` - URL базы данных (если нужно)
- `PORT` - Порт для запуска (по умолчанию 5000)

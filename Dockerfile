FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY cp_parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект cp_parser
COPY cp_parser/ ./cp_parser/

# Создаем директорию для изображений
RUN mkdir -p cp_parser/web_interface/storage/images

# Открываем порт (будет переопределен Railway через $PORT)
EXPOSE 5000

# Запускаем Python из cp_parser/web_interface
WORKDIR /app/cp_parser
CMD ["python", "web_interface/app.py"]

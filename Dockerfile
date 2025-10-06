FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY cp_parser/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект cp_parser
COPY cp_parser/ ./

# Создаем директорию для изображений
RUN mkdir -p web_interface/storage/images

# Открываем порт (будет переопределен Railway через $PORT)
EXPOSE 5000

# Запускаем Python из web_interface
CMD ["python", "web_interface/app.py"]

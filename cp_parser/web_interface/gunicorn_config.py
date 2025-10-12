import os

# Получаем порт из переменной окружения
port = os.environ.get('PORT', '5000')

# Конфигурация Gunicorn
bind = f"0.0.0.0:{port}"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5

# Логирование
accesslog = "-"
errorlog = "-"
loglevel = "info"

print(f"🚀 Gunicorn starting on port: {port}")









# Получаем порт из переменной окружения
port = os.environ.get('PORT', '5000')

# Конфигурация Gunicorn
bind = f"0.0.0.0:{port}"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5

# Логирование
accesslog = "-"
errorlog = "-"
loglevel = "info"

print(f"🚀 Gunicorn starting on port: {port}")












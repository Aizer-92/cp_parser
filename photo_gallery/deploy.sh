#!/bin/bash

# Скрипт для быстрого развертывания галереи фотографий
# Использование: ./deploy.sh /path/to/photos

if [ $# -eq 0 ]; then
    echo "Использование: $0 /path/to/photos"
    echo "Пример: $0 /home/user/photos"
    exit 1
fi

PHOTOS_PATH="$1"

echo "🚀 Развертывание галереи фотографий..."
echo "📁 Путь к фотографиям: $PHOTOS_PATH"

# Проверяем существование папки с фотографиями
if [ ! -d "$PHOTOS_PATH" ]; then
    echo "❌ Ошибка: Папка $PHOTOS_PATH не существует!"
    exit 1
fi

# Проверяем права доступа
if [ ! -r "$PHOTOS_PATH" ]; then
    echo "❌ Ошибка: Нет прав на чтение папки $PHOTOS_PATH!"
    exit 1
fi

echo "✅ Папка с фотографиями найдена и доступна для чтения"

# Обновляем пути в PHP файле
if [ -f "api/photos.php" ]; then
    echo "🔧 Настройка PHP версии..."
    sed -i "s|/path/to/your/photos/|$PHOTOS_PATH|g" api/photos.php
    echo "✅ PHP версия настроена"
fi

# Обновляем пути в Node.js файле
if [ -f "server.js" ]; then
    echo "🔧 Настройка Node.js версии..."
    sed -i "s|/path/to/your/photos/|$PHOTOS_PATH|g" server.js
    echo "✅ Node.js версия настроена"
fi

echo ""
echo "🎉 Развертывание завершено!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Загрузите файлы на ваш веб-сервер"
echo "2. Настройте веб-сервер для обслуживания фотографий"
echo "3. Откройте index.html в браузере"
echo ""
echo "📖 Подробные инструкции в README.md"

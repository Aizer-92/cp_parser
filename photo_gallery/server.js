const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

// Путь к папке с фотографиями (измените на ваш путь)
const PHOTOS_DIR = '/path/to/your/photos/';

// Поддерживаемые форматы изображений
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'];

// Middleware для статических файлов
app.use(express.static('.'));

// API для получения списка фотографий
app.get('/api/photos', (req, res) => {
    try {
        // Проверяем существование директории
        if (!fs.existsSync(PHOTOS_DIR)) {
            return res.status(500).json({
                success: false,
                error: 'Директория с фотографиями не найдена'
            });
        }

        const files = fs.readdirSync(PHOTOS_DIR);
        const photos = [];

        files.forEach(file => {
            // Пропускаем скрытые файлы и директории
            if (file.startsWith('.') || fs.statSync(path.join(PHOTOS_DIR, file)).isDirectory()) {
                return;
            }

            // Проверяем расширение файла
            const extension = path.extname(file).toLowerCase();
            if (ALLOWED_EXTENSIONS.includes(extension)) {
                const filePath = path.join(PHOTOS_DIR, file);
                const stats = fs.statSync(filePath);
                
                photos.push({
                    name: file,
                    url: `/photos/${file}`,
                    size: stats.size,
                    extension: extension,
                    modified: stats.mtime.getTime()
                });
            }
        });

        // Сортируем по дате изменения (новые сначала)
        photos.sort((a, b) => b.modified - a.modified);

        res.json({
            success: true,
            photos: photos,
            count: photos.length
        });

    } catch (error) {
        console.error('Ошибка при получении списка фотографий:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Маршрут для обслуживания фотографий
app.use('/photos', express.static(PHOTOS_DIR));

// Запуск сервера
app.listen(PORT, () => {
    console.log(`🚀 Сервер запущен на порту ${PORT}`);
    console.log(`📸 Галерея доступна по адресу: http://localhost:${PORT}`);
    console.log(`📁 Папка с фотографиями: ${PHOTOS_DIR}`);
});

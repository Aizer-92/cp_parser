<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

// Путь к папке с фотографиями (измените на ваш путь)
$photosDirectory = '/path/to/your/photos/';

// Поддерживаемые форматы изображений
$allowedExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];

try {
    // Проверяем существование директории
    if (!is_dir($photosDirectory)) {
        throw new Exception('Директория с фотографиями не найдена');
    }

    $photos = [];
    $files = scandir($photosDirectory);

    foreach ($files as $file) {
        // Пропускаем скрытые файлы и директории
        if ($file[0] === '.' || is_dir($photosDirectory . $file)) {
            continue;
        }

        // Проверяем расширение файла
        $extension = strtolower(pathinfo($file, PATHINFO_EXTENSION));
        if (in_array($extension, $allowedExtensions)) {
            $filePath = $photosDirectory . $file;
            $fileSize = file_exists($filePath) ? filesize($filePath) : 0;
            
            $photos[] = [
                'name' => $file,
                'url' => '/photos/' . $file, // URL для доступа к файлу
                'size' => $fileSize,
                'extension' => $extension,
                'modified' => filemtime($filePath)
            ];
        }
    }

    // Сортируем по дате изменения (новые сначала)
    usort($photos, function($a, $b) {
        return $b['modified'] - $a['modified'];
    });

    echo json_encode([
        'success' => true,
        'photos' => $photos,
        'count' => count($photos)
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>

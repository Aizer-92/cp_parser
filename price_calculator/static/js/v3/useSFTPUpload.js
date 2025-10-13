// useSFTPUpload.js - Композабл для загрузки фото на SFTP через API
window.useSFTPUpload = function() {
    const API_BASE = window.location.origin;
    
    return {
        /**
         * Загрузить одно фото
         * @param {File} file - файл изображения
         * @param {number} positionId - ID позиции
         * @returns {Promise<string>} URL загруженного файла
         */
        async uploadPhoto(file, positionId) {
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('position_id', positionId);
                
                const response = await axios.post(
                    `${API_BASE}/api/v3/upload/photo`,
                    formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    }
                );
                
                return response.data.url;
            } catch (error) {
                console.error('Ошибка загрузки фото:', error);
                throw error;
            }
        },
        
        /**
         * Загрузить несколько фото
         * @param {File[]} files - массив файлов изображений
         * @param {number} positionId - ID позиции
         * @returns {Promise<string[]>} массив URL загруженных файлов
         */
        async uploadMultiplePhotos(files, positionId) {
            try {
                const formData = new FormData();
                files.forEach(file => {
                    formData.append('files', file);
                });
                formData.append('position_id', positionId);
                
                const response = await axios.post(
                    `${API_BASE}/api/v3/upload/photos`,
                    formData,
                    {
                        headers: {
                            'Content-Type': 'multipart/form-data'
                        }
                    }
                );
                
                return response.data.urls;
            } catch (error) {
                console.error('Ошибка загрузки фото:', error);
                throw error;
            }
        },
        
        /**
         * Проверка валидности файла
         * @param {File} file
         * @returns {boolean}
         */
        isValidImage(file) {
            const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
            const maxSize = 10 * 1024 * 1024; // 10 MB
            
            if (!allowedTypes.includes(file.type)) {
                alert(`Недопустимый формат файла: ${file.type}. Разрешены: JPEG, PNG, WebP`);
                return false;
            }
            
            if (file.size > maxSize) {
                alert(`Файл слишком большой: ${(file.size / 1024 / 1024).toFixed(2)} MB. Максимум 10 MB`);
                return false;
            }
            
            return true;
        },
        
        /**
         * Создать превью изображения
         * @param {File} file
         * @returns {Promise<string>} Data URL для превью
         */
        createPreview(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });
        }
    };
};


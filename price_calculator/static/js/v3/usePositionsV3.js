// usePositionsV3.js - Композабл для работы с позициями через V3 API
window.usePositionsV3 = function() {
    const API_BASE = window.location.origin;
    
    return {
        /**
         * Получить список всех позиций
         * @param {number} skip - смещение для пагинации
         * @param {number} limit - количество записей
         * @returns {Promise<{items: Array, total: number}>}
         */
        async getPositions(skip = 0, limit = 100) {
            try {
                const response = await axios.get(`${API_BASE}/api/v3/positions/`, {
                    params: { skip, limit }
                });
                return response.data;
            } catch (error) {
                console.error('Ошибка получения позиций:', error);
                throw error;
            }
        },
        
        /**
         * Получить позицию по ID
         * @param {number} positionId
         * @returns {Promise<Object>}
         */
        async getPosition(positionId) {
            try {
                const response = await axios.get(`${API_BASE}/api/v3/positions/${positionId}`);
                return response.data;
            } catch (error) {
                console.error(`Ошибка получения позиции ${positionId}:`, error);
                throw error;
            }
        },
        
        /**
         * Создать новую позицию
         * @param {Object} positionData
         * @param {string} positionData.name - название позиции
         * @param {string} [positionData.description] - описание товара
         * @param {string} [positionData.category] - категория
         * @param {Array<string>} [positionData.photo_urls] - массив URL фотографий
         * @param {Object} [positionData.custom_fields] - кастомные поля {customization, material, colors, etc}
         * @returns {Promise<Object>}
         */
        async createPosition(positionData) {
            try {
                // Переименовываем photo_urls в design_files_urls для соответствия модели
                const payload = {
                    ...positionData,
                    design_files_urls: positionData.photo_urls || []
                };
                delete payload.photo_urls;
                
                const response = await axios.post(`${API_BASE}/api/v3/positions/`, payload);
                return response.data;
            } catch (error) {
                console.error('Ошибка создания позиции:', error);
                throw error;
            }
        },
        
        /**
         * Обновить позицию
         * @param {number} positionId
         * @param {Object} positionData - обновляемые данные
         * @returns {Promise<Object>}
         */
        async updatePosition(positionId, positionData) {
            try {
                // Переименовываем photo_urls в design_files_urls
                const payload = { ...positionData };
                if (payload.photo_urls) {
                    payload.design_files_urls = payload.photo_urls;
                    delete payload.photo_urls;
                }
                
                const response = await axios.put(`${API_BASE}/api/v3/positions/${positionId}`, payload);
                return response.data;
            } catch (error) {
                console.error(`Ошибка обновления позиции ${positionId}:`, error);
                throw error;
            }
        },
        
        /**
         * Удалить позицию
         * @param {number} positionId
         * @returns {Promise<Object>}
         */
        async deletePosition(positionId) {
            try {
                const response = await axios.delete(`${API_BASE}/api/v3/positions/${positionId}`);
                return response.data;
            } catch (error) {
                console.error(`Ошибка удаления позиции ${positionId}:`, error);
                throw error;
            }
        },
        
        /**
         * Поиск позиций по названию
         * @param {string} query - поисковый запрос
         * @returns {Promise<Array>}
         */
        async searchPositions(query) {
            try {
                const { items } = await this.getPositions(0, 1000);
                const lowerQuery = query.toLowerCase();
                return items.filter(p => 
                    p.name.toLowerCase().includes(lowerQuery) ||
                    (p.category && p.category.toLowerCase().includes(lowerQuery))
                );
            } catch (error) {
                console.error('Ошибка поиска позиций:', error);
                return [];
            }
        }
    };
};



// useFactoriesV3.js - Композабл для работы с фабриками через V3 API
window.useFactoriesV3 = function() {
    const API_BASE = window.location.origin;
    
    return {
        /**
         * Получить список всех фабрик
         * @param {number} skip - смещение для пагинации
         * @param {number} limit - количество записей
         * @returns {Promise<{items: Array, total: number}>}
         */
        async getFactories(skip = 0, limit = 100) {
            try {
                const response = await axios.get(`${API_BASE}/api/v3/factories/`, {
                    params: { skip, limit }
                });
                return response.data;
            } catch (error) {
                console.error('Ошибка получения фабрик:', error);
                throw error;
            }
        },
        
        /**
         * Получить фабрику по ID
         * @param {number} factoryId
         * @returns {Promise<Object>}
         */
        async getFactory(factoryId) {
            try {
                const response = await axios.get(`${API_BASE}/api/v3/factories/${factoryId}`);
                return response.data;
            } catch (error) {
                console.error(`Ошибка получения фабрики ${factoryId}:`, error);
                throw error;
            }
        },
        
        /**
         * Создать новую фабрику
         * @param {Object} factoryData - данные фабрики
         * @param {string} factoryData.name - название фабрики
         * @param {string} [factoryData.contact_url] - WeChat/URL
         * @param {number} [factoryData.sample_lead_time_days] - срок изготовления образца (дней)
         * @param {number} [factoryData.production_lead_time_days] - срок производства (дней)
         * @param {number} [factoryData.standard_sample_price_yuan] - стандартная цена образца (¥)
         * @param {string} [factoryData.notes] - комментарий
         * @returns {Promise<Object>}
         */
        async createFactory(factoryData) {
            try {
                const response = await axios.post(`${API_BASE}/api/v3/factories/`, factoryData);
                return response.data;
            } catch (error) {
                console.error('Ошибка создания фабрики:', error);
                throw error;
            }
        },
        
        /**
         * Обновить фабрику
         * @param {number} factoryId
         * @param {Object} factoryData - обновляемые данные
         * @returns {Promise<Object>}
         */
        async updateFactory(factoryId, factoryData) {
            try {
                const response = await axios.put(`${API_BASE}/api/v3/factories/${factoryId}`, factoryData);
                return response.data;
            } catch (error) {
                console.error(`Ошибка обновления фабрики ${factoryId}:`, error);
                throw error;
            }
        },
        
        /**
         * Удалить фабрику
         * @param {number} factoryId
         * @returns {Promise<Object>}
         */
        async deleteFactory(factoryId) {
            try {
                const response = await axios.delete(`${API_BASE}/api/v3/factories/${factoryId}`);
                return response.data;
            } catch (error) {
                console.error(`Ошибка удаления фабрики ${factoryId}:`, error);
                throw error;
            }
        },
        
        /**
         * Найти фабрику по URL/WeChat
         * @param {string} contactUrl
         * @returns {Promise<Object|null>}
         */
        async findFactoryByContact(contactUrl) {
            try {
                const { items } = await this.getFactories(0, 1000);
                return items.find(f => f.contact_url === contactUrl) || null;
            } catch (error) {
                console.error('Ошибка поиска фабрики:', error);
                return null;
            }
        }
    };
};



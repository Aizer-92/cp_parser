// useCalculationsV3.js - Композабл для работы с расчётами через V3 API
window.useCalculationsV3 = function() {
    const API_BASE = window.location.origin;
    
    return {
        /**
         * Получить список всех расчётов
         * @param {number} skip - смещение для пагинации
         * @param {number} limit - количество записей
         * @returns {Promise<{items: Array, total: number}>}
         */
        async getCalculations(skip = 0, limit = 100) {
            try {
                const response = await axios.get(`${API_BASE}/api/v3/calculations/`, {
                    params: { skip, limit }
                });
                return response.data;
            } catch (error) {
                console.error('Ошибка получения расчётов:', error);
                throw error;
            }
        },
        
        /**
         * Получить расчёты для конкретной позиции
         * @param {number} positionId
         * @returns {Promise<Array>}
         */
        async getCalculationsByPosition(positionId) {
            try {
                const { items } = await this.getCalculations(0, 1000);
                return items.filter(c => c.position_id === positionId);
            } catch (error) {
                console.error(`Ошибка получения расчётов для позиции ${positionId}:`, error);
                return [];
            }
        },
        
        /**
         * Получить расчёт по ID
         * @param {number} calculationId
         * @returns {Promise<Object>}
         */
        async getCalculation(calculationId) {
            try {
                const response = await axios.get(`${API_BASE}/api/v3/calculations/${calculationId}`);
                return response.data;
            } catch (error) {
                console.error(`Ошибка получения расчёта ${calculationId}:`, error);
                throw error;
            }
        },
        
        /**
         * Создать новый расчёт
         * @param {Object} calculationData
         * @param {number} calculationData.position_id - ID позиции
         * @param {number} [calculationData.factory_id] - ID фабрики (опционально)
         * @param {number} calculationData.price_yuan - цена за единицу (¥)
         * @param {number} calculationData.quantity - количество (шт)
         * @param {number} calculationData.markup - наценка (например 1.7)
         * @param {number} [calculationData.weight_kg] - вес единицы (кг)
         * @param {string} [calculationData.category] - категория для recalculate
         * @returns {Promise<Object>}
         */
        async createCalculation(calculationData) {
            try {
                const response = await axios.post(`${API_BASE}/api/v3/calculations/`, calculationData);
                return response.data;
            } catch (error) {
                console.error('Ошибка создания расчёта:', error);
                throw error;
            }
        },
        
        /**
         * Пересчитать существующий расчёт
         * @param {number} calculationId
         * @param {Object} params
         * @param {string} [params.category] - новая категория
         * @returns {Promise<Object>}
         */
        async recalculate(calculationId, params = {}) {
            try {
                const response = await axios.post(
                    `${API_BASE}/api/v3/calculations/${calculationId}/recalculate`,
                    params
                );
                return response.data;
            } catch (error) {
                console.error(`Ошибка пересчёта ${calculationId}:`, error);
                throw error;
            }
        },
        
        /**
         * Обновить расчёт
         * @param {number} calculationId
         * @param {Object} calculationData - обновляемые данные
         * @returns {Promise<Object>}
         */
        async updateCalculation(calculationId, calculationData) {
            try {
                const response = await axios.put(
                    `${API_BASE}/api/v3/calculations/${calculationId}`,
                    calculationData
                );
                return response.data;
            } catch (error) {
                console.error(`Ошибка обновления расчёта ${calculationId}:`, error);
                throw error;
            }
        },
        
        /**
         * Удалить расчёт
         * @param {number} calculationId
         * @returns {Promise<Object>}
         */
        async deleteCalculation(calculationId) {
            try {
                const response = await axios.delete(`${API_BASE}/api/v3/calculations/${calculationId}`);
                return response.data;
            } catch (error) {
                console.error(`Ошибка удаления расчёта ${calculationId}:`, error);
                throw error;
            }
        }
    };
};


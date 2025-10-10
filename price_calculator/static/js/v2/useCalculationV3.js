/**
 * Vue Composable для работы с V3 API (State Machine + Strategy Pattern)
 * 
 * Скрывает сложность архитектуры от компонентов.
 * UI остаётся прежним - меняется только внутренняя логика.
 */

window.useCalculationV3 = function() {
    return {
        /**
         * Выполняет расчёт с автоматическим определением workflow
         * 
         * @param {Object} requestData - Данные для расчёта
         * @returns {Promise<Object>} Результат расчёта
         */
        async calculate(requestData) {
            console.log('🔵 V3 Calculate:', requestData.product_name);
            console.log('   forced_category:', requestData.forced_category);
            console.log('   custom_logistics:', !!requestData.custom_logistics);
            
            try {
                // СТРАТЕГИЯ: Используем /api/v3/calculate/execute для всех случаев
                // Он сам определит нужен ли ввод параметров и что делать
                
                const response = await axios.post('/api/v3/calculate/execute', requestData);
                
                console.log('✅ V3 Calculate SUCCESS:', response.data.id);
                
                return response.data;
                
            } catch (error) {
                console.error('❌ V3 Calculate ERROR:', error);
                
                // Проверяем специфичные ошибки V3
                if (error.response?.status === 400) {
                    const detail = error.response.data?.detail || 'Ошибка расчёта';
                    
                    // Если требуются параметры - показываем понятное сообщение
                    if (detail.includes('Невозможно выполнить расчёт')) {
                        throw new Error('Для этой категории требуется указать параметры логистики');
                    }
                    
                    if (detail.includes('Невалидные параметры')) {
                        throw new Error(detail);
                    }
                    
                    throw new Error(detail);
                }
                
                throw error;
            }
        },
        
        /**
         * Проверяет нужен ли ввод параметров для категории
         * 
         * @param {Object} requestData - Данные товара
         * @returns {Promise<Object>} { needsInput, requiredParams, category }
         */
        async checkRequirements(requestData) {
            try {
                const response = await axios.post('/api/v3/calculate/start', requestData);
                
                return {
                    needsInput: response.data.needs_user_input,
                    requiredParams: response.data.required_params || [],
                    category: response.data.category,
                    state: response.data.state,
                    message: response.data.message
                };
                
            } catch (error) {
                console.error('❌ V3 Check Requirements ERROR:', error);
                // В случае ошибки считаем что параметры не нужны
                return {
                    needsInput: false,
                    requiredParams: [],
                    category: null,
                    state: 'unknown'
                };
            }
        },
        
        /**
         * Валидирует кастомные параметры перед расчётом
         * 
         * @param {Object} requestData - Полные данные с custom_logistics
         * @returns {Promise<Object>} { valid, errors, canCalculate }
         */
        async validateCustomParams(requestData) {
            try {
                const response = await axios.post('/api/v3/calculate/params', {
                    product_name: requestData.product_name,
                    quantity: requestData.quantity,
                    weight_kg: requestData.weight_kg,
                    unit_price_yuan: requestData.price_yuan,
                    markup: requestData.markup,
                    forced_category: requestData.forced_category,
                    custom_logistics: requestData.custom_logistics
                });
                
                return {
                    valid: response.data.valid,
                    errors: response.data.errors || [],
                    canCalculate: response.data.can_calculate,
                    state: response.data.state
                };
                
            } catch (error) {
                console.error('❌ V3 Validate Params ERROR:', error);
                return {
                    valid: false,
                    errors: ['Ошибка валидации параметров'],
                    canCalculate: false
                };
            }
        },
        
        /**
         * Загружает список категорий
         * 
         * @returns {Promise<Array>} Список категорий
         */
        async getCategories() {
            try {
                const response = await axios.get('/api/v3/categories');
                return response.data.categories || [];
            } catch (error) {
                console.error('❌ V3 Get Categories ERROR:', error);
                return [];
            }
        },
        
        /**
         * Обновляет существующий расчёт
         * 
         * @param {number} calculationId - ID расчёта
         * @param {Object} requestData - Новые данные
         * @returns {Promise<Object>} Обновлённый результат
         */
        async updateCalculation(calculationId, requestData) {
            try {
                // Пока используем V2 endpoint для обновления
                // TODO: создать V3 endpoint для update
                const response = await axios.put(`/api/v2/calculation/${calculationId}`, requestData);
                
                console.log('✅ V3 Update SUCCESS:', calculationId);
                
                return response.data;
                
            } catch (error) {
                console.error('❌ V3 Update ERROR:', error);
                throw error;
            }
        },
        
        /**
         * Определяет нужно ли показывать форму редактирования для категории
         * 
         * Форма НЕ показывается автоматически если:
         * - Категория стандартная (есть базовые ставки)
         * - Параметры уже заполнены (custom_logistics существует)
         * 
         * Форма показывается только если:
         * - "Новая категория" И custom_logistics пустой
         * 
         * @param {string} category - Название категории
         * @param {Object} customLogistics - Существующие custom_logistics
         * @returns {boolean} Нужно ли показывать форму
         */
        shouldShowEditForm(category, customLogistics) {
            // Если категория "Новая" и параметры не заполнены - показываем форму
            if (category === 'Новая категория') {
                // Проверяем есть ли хоть один маршрут с параметрами
                if (!customLogistics) return true;
                
                const hasAnyParams = Object.values(customLogistics).some(route => {
                    if (!route) return false;
                    return route.custom_rate != null || 
                           route.duty_rate != null || 
                           route.vat_rate != null;
                });
                
                return !hasAnyParams;
            }
            
            // Для всех остальных категорий - НЕ показываем автоматически
            // Пользователь сам откроет через кнопку "Редактировать" если нужно
            return false;
        },
        
        /**
         * Создаёт пустой объект custom_logistics для всех маршрутов
         * 
         * @returns {Object} Пустые параметры для всех маршрутов
         */
        createEmptyCustomLogistics() {
            return {
                highway_rail: { custom_rate: null, duty_rate: null, vat_rate: null, specific_rate: null },
                highway_air: { custom_rate: null, duty_rate: null, vat_rate: null, specific_rate: null },
                highway_contract: { custom_rate: null, duty_rate: null, vat_rate: null, specific_rate: null },
                prologix: { custom_rate: null, duty_rate: null, vat_rate: null, specific_rate: null },
                sea_container: { custom_rate: null, duty_rate: null, vat_rate: null, specific_rate: null }
            };
        },
        
        /**
         * Проверяет заполнены ли параметры для маршрута
         * 
         * @param {Object} routeParams - Параметры маршрута
         * @returns {boolean} Заполнены ли параметры
         */
        isRouteParamsFilled(routeParams) {
            if (!routeParams) return false;
            
            return routeParams.custom_rate != null || 
                   routeParams.duty_rate != null || 
                   routeParams.vat_rate != null ||
                   routeParams.specific_rate != null;
        }
    };
};


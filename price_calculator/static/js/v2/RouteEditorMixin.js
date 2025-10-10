// RouteEditorMixin.js - Общая логика для редактирования маршрутов
window.RouteEditorMixin = {
    methods: {
        /**
         * Безопасное преобразование значения в число
         * @param {any} value - Значение для преобразования
         * @returns {number|null} - Число или null
         */
        parseFloatSafe(value) {
            if (value === null || value === undefined || value === '') {
                return null;
            }
            const parsed = parseFloat(value);
            return isNaN(parsed) ? null : parsed;
        },
        
        /**
         * Очистка параметров: преобразование строк в числа
         * @param {Object} params - Параметры для очистки
         * @returns {Object} - Очищенные параметры
         */
        cleanNumericParams(params) {
            const cleaned = { ...params };
            const numericFields = ['custom_rate', 'duty_rate', 'vat_rate', 'specific_rate'];
            
            numericFields.forEach(field => {
                if (field in cleaned) {
                    cleaned[field] = this.parseFloatSafe(cleaned[field]);
                }
            });
            
            return cleaned;
        },
        
        /**
         * Получить дефолтную ставку для маршрута
         * @param {string} routeKey - Ключ маршрута
         * @returns {number} - Дефолтная ставка
         */
        getDefaultRate(routeKey) {
            const defaults = {
                'highway_rail': 5.0,
                'highway_air': 7.1,
                'highway_contract': 4.5,
                'prologix': 20000
            };
            return defaults[routeKey] || 5.0;
        },
        
        /**
         * Извлечь логистическую ставку из маршрута
         * @param {Object} route - Объект маршрута
         * @param {string} routeKey - Ключ маршрута
         * @param {boolean} isNewCategory - Флаг новой категории
         * @returns {number|null} - Логистическая ставка
         */
        extractLogisticsRate(route, routeKey, isNewCategory = false) {
            // Для Prologix
            if (routeKey === 'prologix') {
                if (route.rate_rub_per_m3) {
                    return route.rate_rub_per_m3;
                }
                if (route.breakdown && route.breakdown.prologix_rate) {
                    return route.breakdown.prologix_rate;
                }
                return this.getDefaultRate('prologix');
            }
            
            // Для Highway маршрутов
            if (route.breakdown && route.breakdown.logistics_rate) {
                return route.breakdown.logistics_rate;
            }
            if (route.logistics_rate_usd) {
                return route.logistics_rate_usd;
            }
            
            // Для "Новая категория" - пустое поле
            if (isNewCategory) {
                return null;
            }
            
            // Дефолтное значение
            return this.getDefaultRate(routeKey);
        },
        
        /**
         * Извлечь данные о пошлинах из маршрута
         * @param {Object} route - Объект маршрута
         * @param {string} routeKey - Ключ маршрута
         * @returns {Object} - Данные о пошлинах
         */
        extractDutyData(route, routeKey) {
            const result = {
                duty_type: 'percent',
                duty_rate: null,
                vat_rate: null,
                specific_rate: null
            };
            
            if (!route.breakdown) {
                return result;
            }
            
            const breakdown = route.breakdown;
            
            // Определяем тип пошлины
            result.duty_type = breakdown.duty_type || 'percent';
            
            // Извлекаем ставки в зависимости от типа маршрута
            if (routeKey === 'sea_container') {
                // Для sea_container: duty_rate и vat_rate (не _pct)
                result.duty_rate = breakdown.duty_rate ? (breakdown.duty_rate * 100) : null;
                result.vat_rate = breakdown.vat_rate ? (breakdown.vat_rate * 100) : null;
            } else {
                // Для Contract и Prologix: duty_rate_pct и vat_rate_pct
                result.duty_rate = breakdown.duty_rate_pct || null;
                result.vat_rate = breakdown.vat_rate_pct || null;
            }
            
            // Загружаем данные для комбинированных и весовых пошлин
            if (breakdown.duty_ad_valorem_rate) {
                result.duty_rate = breakdown.duty_ad_valorem_rate;
            }
            if (breakdown.duty_specific_rate_eur) {
                result.specific_rate = breakdown.duty_specific_rate_eur;
            }
            
            return result;
        },
        
        /**
         * Валидация параметров перед сохранением
         * @param {Object} params - Параметры для валидации
         * @param {string} routeKey - Ключ маршрута
         * @param {boolean} isNewCategory - Флаг новой категории
         * @returns {Object} - { isValid: boolean, message: string }
         */
        validateRouteParams(params, routeKey, isNewCategory) {
            // Для "Новая категория" и Highway: обязательная ставка
            const isHighway = routeKey === 'highway_rail' || routeKey === 'highway_air';
            
            if (isNewCategory && isHighway) {
                if (!params.custom_rate || params.custom_rate <= 0) {
                    return {
                        isValid: false,
                        message: 'Для "Новая категория" необходимо указать логистическую ставку (больше 0)'
                    };
                }
            }
            
            return { isValid: true, message: '' };
        },
        
        /**
         * Получить название маршрута
         * @param {string} routeKey - Ключ маршрута
         * @returns {string} - Название маршрута
         */
        getRouteTitle(routeKey) {
            const titles = {
                'highway_rail': 'Highway ЖД',
                'highway_air': 'Highway Авиа',
                'highway_contract': 'Highway Контракт',
                'prologix': 'Prologix',
                'sea_container': 'Морской контейнер'
            };
            return titles[routeKey] || routeKey;
        },
        
        /**
         * Проверка типа маршрута
         * @param {string} routeKey - Ключ маршрута
         * @returns {Object} - { isHighway, isContract, isPrologix, isSeaContainer }
         */
        getRouteType(routeKey) {
            return {
                isHighway: routeKey === 'highway_rail' || routeKey === 'highway_air',
                isContract: routeKey === 'highway_contract',
                isPrologix: routeKey === 'prologix',
                isSeaContainer: routeKey === 'sea_container'
            };
        }
    }
};


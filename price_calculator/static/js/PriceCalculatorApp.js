/**
 * 🚀 PRICE CALCULATOR APP - MAIN COMPONENT - FIXED VERSION
 * Главный компонент приложения с ES5-совместимым синтаксисом
 */

const PriceCalculatorApp = {
    name: 'PriceCalculatorApp',
    
    components: {
        CategorySelector: window.CategorySelector,
        ProductForm: window.ProductForm,
        ProductFormPrecise: window.ProductFormPrecise,
        ResultsDisplay: window.ResultsDisplay,
        RoutesComparison: window.RoutesComparison,
        HistoryPanel: window.HistoryPanel,
        SettingsPanel: window.SettingsPanel,
        CategoriesPanel: window.CategoriesPanel
    },
    
    data: function() {
        return {
            // UI State
            // activeTab теперь computed из $route.path
            settingsSubTab: 'general', // general или categories
            isCalculating: false,
            editingCalculationId: null,
            // ID текущего расчета на странице (для UPDATE при изменениях)
            currentPreciseCalculationId: null,
            // Выбранный маршрут для детального отображения
            selectedRoute: null,
            cachedRouteData: null, // Кэш для selectedRouteData
            
            // Form Data (быстрые расчеты)
            form: {
                product_name: '',
                product_url: '',
                price_yuan: null,
                weight_kg: null,
                quantity: null,
                custom_rate: null,
                delivery_type: 'rail',
                markup: 1.7
            },
            
                // Form Data (точные расчеты с пакингом)
                preciseForm: {
                    product_name: '',
                    product_url: '',
                    price_yuan: null,
                    weight_kg: null, // Вычисляется автоматически из данных пакинга
                    quantity: null,
                    custom_rate: null,
                    delivery_type: 'rail',
                    markup: 1.7,
                    // Поля пакинга для точных расчетов
                    packing_units_per_box: null,
                    packing_box_weight: null,
                    packing_box_length: null,
                    packing_box_width: null,
                    packing_box_height: null
                },
            
            // Results & History
            result: null,               // Результаты быстрых расчетов
            preciseResult: null,        // Результаты точных расчетов
            history: [],
            expandedHistory: [],
            
            // Categories
            detectedCategory: null,
            detectedCategoryPrecise: null, // Для точных расчетов
            categories: [],
            selectedCategoryIndex: null,
            selectedCategoryIndexPrecise: null, // Для точных расчетов
            
            // System State
            databaseAvailable: true,
            
            // Settings
            settings: {
                currencies: {
                    yuan_to_usd: 0.139,
                    usd_to_rub: 84.0,
                    yuan_to_rub: 11.67
                },
                formula: {
                    toni_commission_percent: 5.0,
                    transfer_percent: 18.0,
                    local_delivery_rate_yuan_per_kg: 2.0,
                    msk_pickup_total_rub: 1000.0,
                    other_costs_percent: 2.5
                }
            },
            isSavingSettings: false,
            
            // Exchange Rates
            exchangeRates: {
                yuan_to_usd: 0.139,
                usd_to_rub: 84,
                yuan_to_rub: 11.67
            }
        }
    },
    
    computed: {
        // 🔥 НОВОЕ: activeTab определяется из маршрута
        activeTab: function() {
            // Маппинг путей на табы
            var path = this.$route ? this.$route.path : '/';
            var routeToTab = {
                '/': 'calculator',
                '/precise': 'precise',
                '/history': 'history',
                '/settings': 'settings'
            };
            return routeToTab[path] || 'calculator';
        },
        
        isFormValid: function() {
            return this.form.product_name &&
                   parseFloat(this.form.price_yuan) > 0 &&
                   parseFloat(this.form.weight_kg) > 0 &&
                   parseInt(this.form.quantity) > 0;
        },
        
        isPreciseFormValid: function() {
            return this.preciseForm.product_name &&
                   parseFloat(this.preciseForm.price_yuan) > 0 &&
                   parseInt(this.preciseForm.quantity) > 0 &&
                   this.preciseForm.packing_units_per_box > 0 &&
                   parseFloat(this.preciseForm.packing_box_weight) > 0 &&
                   parseFloat(this.preciseForm.packing_box_length) > 0 &&
                   parseFloat(this.preciseForm.packing_box_width) > 0 &&
                   parseFloat(this.preciseForm.packing_box_height) > 0;
        },

        suggestedRate: function() {
            if (!this.detectedCategory) return 0;
            var rates = this.detectedCategory.rates;
            return this.form.delivery_type === 'air' ? rates.air_base : rates.rail_base;
        },
        
        suggestedRatePrecise: function() {
            if (!this.detectedCategoryPrecise) return 0;
            var rates = this.detectedCategoryPrecise.rates;
            return this.preciseForm.delivery_type === 'air' ? rates.air_base : rates.rail_base;
        },
        
        // Адаптированные данные для выбранного маршрута (для ResultsDisplay)
        selectedRouteData: function() {
            if (!this.preciseResult || !this.selectedRoute || !this.preciseResult.routes) {
                return null;
            }
            
            var route = this.preciseResult.routes[this.selectedRoute];
            if (!route) {
                console.error('❌ Маршрут не найден:', this.selectedRoute);
                return null;
            }
            
            // Защита от undefined: проверяем обязательные поля
            if (!route.total_cost_rub || !route.cost_per_unit_rub) {
                console.error('❌ Маршрут не содержит цены:', route);
                return null;
            }
            
            console.log('✅ Адаптирую маршрут:', this.selectedRoute, 'данные:', {
                cost_rub: route.total_cost_rub,
                per_unit: route.cost_per_unit_rub,
                sale_rub: route.sale_total_rub
            });
            
            console.log('📋 Структура cost_price будет:', {
                total: { rub: route.total_cost_rub, usd: route.total_cost_usd || route.total_cost_rub / 97 },
                per_unit: { rub: route.cost_per_unit_rub, usd: route.cost_per_unit_usd || route.cost_per_unit_rub / 97 }
            });
            
            // ВАЖНО: НЕ используем Object.assign - он не копирует вложенные объекты!
            // Копируем только базовые поля, остальное перезаписываем
            var adaptedResult = {
                // Базовая информация о товаре
                product_name: this.preciseResult.product_name,
                category: this.preciseResult.category,
                quantity: this.preciseResult.quantity,
                weight_kg: this.preciseResult.weight_kg,
                markup: this.preciseResult.markup,
                
                // Данные пакинга (ВАЖНО для отображения блока!)
                packing_units_per_box: this.preciseResult.packing_units_per_box,
                packing_box_weight: this.preciseResult.packing_box_weight,
                packing_box_length: this.preciseResult.packing_box_length,
                packing_box_width: this.preciseResult.packing_box_width,
                packing_box_height: this.preciseResult.packing_box_height,
                
                // Цены выбранного маршрута
                cost_price: {
                    total: { rub: route.total_cost_rub, usd: route.total_cost_usd || route.total_cost_rub / 97 },
                    per_unit: { rub: route.cost_per_unit_rub, usd: route.cost_per_unit_usd || route.cost_per_unit_rub / 97 }
                },
                sale_price: {
                    total: { rub: route.sale_total_rub, usd: (route.sale_total_rub || 0) / 97 },
                    per_unit: { rub: route.sale_per_unit_rub, usd: (route.sale_per_unit_rub || 0) / 97 }
                },
                
                // total_price - стоимость товара от фабрики (для детального расчета)
                total_price: this.preciseResult.total_price || {
                    yuan: 0,
                    usd: 0,
                    rub: 0
                },
                
                // КРИТИЧНО: Рассчитываем profit из разницы sale - cost
                profit: {
                    total: { 
                        rub: (route.sale_total_rub || 0) - route.total_cost_rub,
                        usd: ((route.sale_total_rub || 0) - route.total_cost_rub) / 97
                    },
                    per_unit: { 
                        rub: (route.sale_per_unit_rub || 0) - route.cost_per_unit_rub,
                        usd: ((route.sale_per_unit_rub || 0) - route.cost_per_unit_rub) / 97
                    }
                },
                
                // Логистика выбранного маршрута
                logistics: {
                    rate_usd: route.logistics_rate_usd || route.base_rate_usd || 0,
                    base_rate_usd: route.base_rate_usd || route.logistics_rate_usd || 0,
                    density_surcharge_usd: route.density_surcharge_usd || 0,
                    cost_rub: route.logistics_cost_rub || 0,
                    cost_usd: route.logistics_cost_usd || 0,
                    delivery_type: this.selectedRoute.includes('air') ? 'air' : 'rail'
                },
                
                // Плотность (если есть)
                density_info: this.preciseResult.density_info || null,
                
                // Пошлины (если есть)
                customs_info: this.preciseResult.customs_info || null,
                
                // Дополнительные расходы (КРИТИЧНО для отображения)
                additional_costs: this.preciseResult.additional_costs || {
                    local_delivery_rub: 0,
                    msk_pickup_rub: 0,
                    other_costs_rub: 0,
                    total_rub: 0
                },
                
                // Contract cost и cost_difference (для отображения под контрактом)
                contract_cost: this.preciseResult.contract_cost || null,
                cost_difference: this.preciseResult.cost_difference || null
            };
            
            // Если это Prologix - добавляем его данные
            if (this.selectedRoute === 'prologix' && route) {
                adaptedResult.prologix_cost = {
                    route_name: route.name,
                    total_volume_m3: this.preciseResult.prologix_cost ? this.preciseResult.prologix_cost.total_volume_m3 : 0,
                    rate_rub_per_m3: route.rate_rub_per_m3,
                    logistics_cost_rub: route.logistics_cost_rub || 0,
                    logistics_cost_usd: route.logistics_cost_usd || 0,
                    total_cost_rub: route.total_cost_rub,
                    total_cost_usd: route.total_cost_usd || route.total_cost_rub / 97,
                    cost_per_unit_rub: route.cost_per_unit_rub,
                    cost_per_unit_usd: route.cost_per_unit_usd || route.cost_per_unit_rub / 97,
                    fixed_cost_rub: 25000,
                    delivery_days_min: 25,
                    delivery_days_max: 35,
                    delivery_days_avg: 30
                };
            }
            
            // Все данные подготовлены для ResultsDisplay
            console.log('📦 Финальный adaptedResult:', JSON.stringify({
                has_cost_price: !!adaptedResult.cost_price,
                has_sale_price: !!adaptedResult.sale_price,
                cost_price_total_rub: adaptedResult.cost_price ? adaptedResult.cost_price.total.rub : null,
                cost_price_per_unit_rub: adaptedResult.cost_price ? adaptedResult.cost_price.per_unit.rub : null
            }, null, 2));
            
            // 🚀 КРИТИЧНО: Возвращаем plain object через JSON для убирания Proxy
            // Это гарантирует что ResultsDisplay получит чистый объект без Vue reactivity
            return JSON.parse(JSON.stringify(adaptedResult));
        }
    },
    
    watch: {
        // 🔄 СБРОС currentPreciseCalculationId ПРИ СМЕНЕ СТРАНИЦЫ
        '$route': function(newRoute, oldRoute) {
            // Если уходим со страницы /precise, сбрасываем ID текущего расчета
            if (oldRoute && oldRoute.path === '/precise' && newRoute.path !== '/precise') {
                this.currentPreciseCalculationId = null;
                console.log('🔄 Переход со страницы /precise, currentPreciseCalculationId сброшен');
            }
        },
        
        // 🔄 Принудительное обновление при смене маршрута
        'selectedRoute': function(newRoute, oldRoute) {
            if (newRoute && newRoute !== oldRoute) {
                console.log('🔄 selectedRoute изменен:', oldRoute, '→', newRoute);
            }
        },
        
        // 🔥 АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ СТАВКИ ПРИ СМЕНЕ МАРШРУТА (БЫСТРЫЙ РАСЧЕТ)
        'form.delivery_type': function(newType, oldType) {
            if (this.detectedCategory && this.detectedCategory.rates) {
                var newRate = newType === 'air' ? this.detectedCategory.rates.air_base : this.detectedCategory.rates.rail_base;
                this.form.custom_rate = newRate;
                console.log('🚚 Маршрут изменен:', oldType, '→', newType, '| Новая ставка:', newRate, '$/кг');
            }
        },
        
        // 🔥 АВТОМАТИЧЕСКОЕ ОБНОВЛЕНИЕ СТАВКИ ПРИ СМЕНЕ МАРШРУТА (ТОЧНЫЙ РАСЧЕТ)
        'preciseForm.delivery_type': function(newType, oldType) {
            if (this.detectedCategoryPrecise && this.detectedCategoryPrecise.rates) {
                var newRate = newType === 'air' ? this.detectedCategoryPrecise.rates.air_base : this.detectedCategoryPrecise.rates.rail_base;
                this.preciseForm.custom_rate = newRate;
                console.log('🚚 Маршрут изменен (точный):', oldType, '→', newType, '| Новая ставка:', newRate, '$/кг');
            }
        }
    },
    
    methods: {
        // === SETTINGS MANAGEMENT ===
        loadSettings: function() {
            var self = this;
            return axios.get('/api/settings').then(function(response) {
                self.settings = response.data;
                // Синхронизируем с exchangeRates для обратной совместимости
                self.exchangeRates = {
                    yuan_to_usd: self.settings.currencies.yuan_to_usd,
                    usd_to_rub: self.settings.currencies.usd_to_rub,
                    yuan_to_rub: self.settings.currencies.yuan_to_rub
                };
                console.log('Settings loaded:', self.settings);
            }).catch(function(error) {
                console.error('Ошибка загрузки настроек:', error);
                // Используем дефолтные значения при ошибке
            });
        },
        
        saveSettings: function(newSettings) {
            var self = this;
            this.isSavingSettings = true;
            
            return axios.post('/api/settings', newSettings).then(function(response) {
                if (response.data.success) {
                    self.settings = JSON.parse(JSON.stringify(newSettings));
                    // Синхронизируем с exchangeRates
                    self.exchangeRates = {
                        yuan_to_usd: self.settings.currencies.yuan_to_usd,
                        usd_to_rub: self.settings.currencies.usd_to_rub,
                        yuan_to_rub: self.settings.currencies.yuan_to_rub
                    };
                    
                    alert('✅ Настройки успешно сохранены!');
                    console.log('Settings saved successfully');
                } else {
                    throw new Error(response.data.message || 'Неизвестная ошибка');
                }
            }).catch(function(error) {
                console.error('Ошибка сохранения настроек:', error);
                var errorMessage = 'Ошибка при сохранении настроек';
                if (error.response && error.response.data && error.response.data.detail) {
                    errorMessage = error.response.data.detail;
                }
                alert('❌ ' + errorMessage);
            }).finally(function() {
                self.isSavingSettings = false;
            });
        },
        
        // === EXCHANGE RATES ===
        loadExchangeRates: function() {
            var self = this;
            return axios.get('/api/exchange-rates').then(function(response) {
                self.exchangeRates = response.data;
                console.log('Exchange rates loaded:', self.exchangeRates);
            }).catch(function(error) {
                console.error('Ошибка загрузки курсов валют:', error);
                // Используем дефолтные значения при ошибке
            });
        },
        
        // === CATEGORY MANAGEMENT ===
        loadCategories: function(forceReload) {
            var self = this;
            forceReload = forceReload || false;
            
            return new Promise(function(resolve, reject) {
                try {
                    if (!forceReload && Array.isArray(self.categories) && self.categories.length) {
                        resolve();
                        return;
                    }

                    axios.get('/api/categories').then(function(response) {
                        self.categories = response.data || [];
                        console.log('PriceCalculatorApp: Categories loaded:', self.categories.length);
                        resolve();
                    }).catch(function(error) {
                        console.error('Ошибка загрузки категорий:', error);
                        self.categories = [];
                        reject(error);
                    });
                } catch (error) {
                    console.error('Ошибка загрузки категорий:', error);
                    self.categories = [];
                    reject(error);
                }
            });
        },
        
        onProductNameChange: function() {
            var self = this;
            if (this.form.product_name.length > 2) {
                axios.get('/api/category/' + encodeURIComponent(this.form.product_name)).then(function(response) {
                    self.detectedCategory = response.data;

                    if (!Array.isArray(self.categories) || self.categories.length === 0) {
                        self.loadCategories(true);
                    }

                    self.selectedCategoryIndex = self.categories.findIndex(function(cat) {
                        return cat.category === self.detectedCategory.category &&
                               cat.material === self.detectedCategory.material;
                    });
                    
                    self.updateSuggestedRate();

                }).catch(function(error) {
                    console.error('Ошибка определения категории:', error);
                });
            } else {
                this.detectedCategory = null;
                this.selectedCategoryIndex = null;
            }
        },
        
        onProductNameChangePrecise: function() {
            var self = this;
            if (this.preciseForm.product_name.length > 2) {
                axios.get('/api/category/' + encodeURIComponent(this.preciseForm.product_name)).then(function(response) {
                    self.detectedCategoryPrecise = response.data;

                    if (!Array.isArray(self.categories) || self.categories.length === 0) {
                        self.loadCategories(true);
                    }

                    self.selectedCategoryIndexPrecise = self.categories.findIndex(function(cat) {
                        return cat.category === self.detectedCategoryPrecise.category &&
                               cat.material === self.detectedCategoryPrecise.material;
                    });
                    
                    self.updateSuggestedRatePrecise();

                }).catch(function(error) {
                    console.error('Ошибка определения категории (точные расчеты):', error);
                });
            } else {
                this.detectedCategoryPrecise = null;
                this.selectedCategoryIndexPrecise = null;
            }
        },
        
        onCategoryChange: function(event) {
            var category = event.category;
            var index = event.index;
            this.detectedCategory = category;
            this.selectedCategoryIndex = index;
            this.updateSuggestedRate();
        },
        
        onCategoryChangePrecise: function(event) {
            var category = event.category;
            var index = event.index;
            this.detectedCategoryPrecise = category;
            this.selectedCategoryIndexPrecise = index;
            this.updateSuggestedRatePrecise();
        },
        
        onCategoriesLoadRequired: function() {
            this.loadCategories(true);
        },
        
        updateSuggestedRate: function() {
            if (this.detectedCategory) {
                var rates = this.detectedCategory.rates;
                var suggestedRate = this.form.delivery_type === 'air' ? rates.air_base : rates.rail_base;
                this.form.custom_rate = suggestedRate;
                console.log('PriceCalculatorApp: Updated suggested rate to:', suggestedRate);
            }
        },
        
        updateSuggestedRatePrecise: function() {
            if (this.detectedCategoryPrecise) {
                var rates = this.detectedCategoryPrecise.rates;
                var suggestedRate = this.preciseForm.delivery_type === 'air' ? rates.air_base : rates.rail_base;
                this.preciseForm.custom_rate = suggestedRate;
                console.log('PriceCalculatorApp: Updated suggested rate (precise) to:', suggestedRate);
            }
        },
        
        // === CALCULATION ===
        performCalculation: function() {
            var self = this;
            if (!this.isFormValid) return Promise.resolve();
            
            this.isCalculating = true;
            // Очищаем точные результаты при быстром расчете
            this.preciseResult = null;
            
            var calculationData = {
                product_name: this.form.product_name,
                product_url: this.form.product_url,
                price_yuan: parseFloat(this.form.price_yuan) || 0,
                weight_kg: parseFloat(this.form.weight_kg) || 0,
                quantity: parseInt(this.form.quantity) || 1,
                custom_rate: parseFloat(this.form.custom_rate) || this.suggestedRate,
                delivery_type: this.form.delivery_type,
                markup: parseFloat(this.form.markup) || 1.7,
                // Флаг быстрого расчета (без пакинга)
                is_precise_calculation: false
            };
            
            return axios.post('/api/calculate', calculationData).then(function(response) {
                self.result = response.data;
                
                // Обновляем историю после расчета
                if (self.result.id) {
                    self.loadHistory();
                }
            }).catch(function(error) {
                console.error('Ошибка расчета:', error);
                alert('Ошибка при выполнении расчета. Проверьте введенные данные.');
            }).finally(function() {
                self.isCalculating = false;
            });
        },
        
        // === ROUTES MANAGEMENT ===
        handleSelectRoute: function(routeKey) {
            var self = this;
            console.log('🔘 handleSelectRoute вызван:', routeKey);
            console.log('📊 Текущий selectedRoute (до):', self.selectedRoute);
            
            // ВАЖНО: Просто меняем selectedRoute, Vue сам обновит через :key
            self.selectedRoute = routeKey;
            
            console.log('📊 Текущий selectedRoute (после):', self.selectedRoute);
            console.log('✅ Vue автоматически обновит ResultsDisplay через :key');
            
            // Пересчитываем cachedRouteData СРАЗУ
            self.updateCachedRouteData();
        },
        
        updateCachedRouteData: function() {
            // Просто триггерим пересчет - computed property сделает всю работу
            // cachedRouteData больше не используется, данные идут из getPlainRouteData()
            console.log('💾 updateCachedRouteData вызван, selectedRoute:', this.selectedRoute);
        },
        
        getPlainRouteData: function() {
            // Вызывается при каждом рендере ResultsDisplay
            // Возвращает ЧИСТЫЙ объект без Vue reactivity
            var data = this.selectedRouteData;
            if (!data) return null;
            
            // Конвертируем в plain object через JSON
            var plain = JSON.parse(JSON.stringify(data));
            
            console.log('🎯 getPlainRouteData вызван');
            console.log('🎯 ПОЛНАЯ структура plain (JSON):', JSON.stringify(plain, null, 2));
            console.log('🎯 plain.cost_price (JSON):', JSON.stringify(plain.cost_price, null, 2));
            console.log('🎯 plain.sale_price (JSON):', JSON.stringify(plain.sale_price, null, 2));
            console.log('🎯 plain.profit (JSON):', JSON.stringify(plain.profit, null, 2));
            console.log('🎯 plain.additional_costs (JSON):', JSON.stringify(plain.additional_costs, null, 2));
            
            return plain;
        },
        
        performPreciseCalculation: function() {
            var self = this;
            if (!this.isPreciseFormValid) return Promise.resolve();
            
            this.isCalculating = true;
            // Очищаем быстрые результаты при точном расчете
            this.result = null;
            
            var calculationData = {
                product_name: this.preciseForm.product_name,
                product_url: this.preciseForm.product_url,
                price_yuan: parseFloat(this.preciseForm.price_yuan) || 0,
                weight_kg: parseFloat(this.preciseForm.weight_kg) || 0,
                quantity: parseInt(this.preciseForm.quantity) || 1,
                custom_rate: parseFloat(this.preciseForm.custom_rate) || this.suggestedRatePrecise,
                delivery_type: this.preciseForm.delivery_type,
                markup: parseFloat(this.preciseForm.markup) || 1.7,
                // ВАЖНО: Флаг точного расчета для включения данных пакинга
                is_precise_calculation: true,
                // Данные пакинга
                packing_units_per_box: parseInt(this.preciseForm.packing_units_per_box) || null,
                packing_box_weight: parseFloat(this.preciseForm.packing_box_weight) || null,
                packing_box_length: parseFloat(this.preciseForm.packing_box_length) || null,
                packing_box_width: parseFloat(this.preciseForm.packing_box_width) || null,
                packing_box_height: parseFloat(this.preciseForm.packing_box_height) || null
            };
            
            // ✨ Умная логика: UPDATE если уже есть расчет на странице, INSERT если новый
            var apiCall;
            var calculationId = self.currentPreciseCalculationId || self.editingCalculationId;
            
            if (calculationId) {
                console.log('🔄 Обновление существующего расчета ID:', calculationId);
                apiCall = axios.put('/api/history/' + calculationId, calculationData);
            } else {
                console.log('➕ Создание нового расчета');
                apiCall = axios.post('/api/calculate', calculationData);
            }
            
            return apiCall.then(function(response) {
                console.log('📥 Получен ответ от API:', response.data);
                console.log('🔍 routes в ответе:', response.data.routes);
                console.log('🔍 Ключи routes:', response.data.routes ? Object.keys(response.data.routes) : 'НЕТ');
                self.preciseResult = response.data;
                
                // 📊 Автоматически выбираем самый дешевый маршрут после расчета
                if (self.preciseResult.routes && Object.keys(self.preciseResult.routes).length > 0) {
                    var routes = self.preciseResult.routes;
                    console.log('📊 Доступные маршруты:', Object.keys(routes));
                    var cheapestRoute = null;
                    var lowestCost = Infinity;
                    
                    for (var key in routes) {
                        console.log('💰 Маршрут', key, 'стоимость:', routes[key].total_cost_rub);
                        if (routes[key].total_cost_rub < lowestCost) {
                            lowestCost = routes[key].total_cost_rub;
                            cheapestRoute = key;
                        }
                    }
                    
                    console.log('✅ Выбран самый дешевый маршрут:', cheapestRoute, 'стоимость:', lowestCost);
                    self.selectedRoute = cheapestRoute;
                    
                    // Принудительно обновляем Vue, чтобы computed property пересчитался
                    self.$nextTick(function() {
                        console.log('🔄 Vue обновлен, selectedRoute:', self.selectedRoute);
                        // Обновляем cachedRouteData
                        self.updateCachedRouteData();
                    });
                } else {
                    console.error('❌ Нет маршрутов в ответе!', self.preciseResult);
                    console.error('❌ response.data.routes:', response.data.routes);
                    console.error('❌ typeof routes:', typeof response.data.routes);
                }
                
                // Сохраняем ID текущего расчета для дальнейших UPDATE
                if (self.preciseResult.id) {
                    self.currentPreciseCalculationId = self.preciseResult.id;
                    console.log('💾 Сохранен ID текущего расчета:', self.currentPreciseCalculationId);
                    self.loadHistory();
                }
                
                // Очищаем editingCalculationId после успешного сохранения
                if (self.editingCalculationId) {
                    console.log('✅ Расчет обновлен, сбрасываем editingCalculationId');
                    self.editingCalculationId = null;
                }
                
                // ✨ Умный роутинг: переход на /precise после расчета
                // Визуально остаемся на той же странице, но URL обновляется для истории браузера
                var currentPath = self.$route ? self.$route.path : '/';
                if (currentPath !== '/precise') {
                    console.log('📍 Переход на /precise с', currentPath);
                    self.$router.push('/precise').catch(function(err) {
                        // Игнорируем ошибку "NavigationDuplicated"
                        if (err.name !== 'NavigationDuplicated') {
                            console.error('Ошибка навигации:', err);
                        }
                    });
                }
            }).catch(function(error) {
                console.error('Ошибка точного расчета:', error);
                alert('Ошибка при выполнении точного расчета. Проверьте введенные данные.');
            }).finally(function() {
                self.isCalculating = false;
                console.log('✅ Точный расчет завершен, isCalculating:', self.isCalculating);
                console.log('📝 isPreciseFormValid:', self.isPreciseFormValid);
            });
        },
        
        resetForm: function() {
            this.form = {
                product_name: '',
                product_url: '',
                price_yuan: null,
                weight_kg: null,
                quantity: null,
                custom_rate: null,
                delivery_type: 'rail',
                markup: 1.7
            };
            this.result = null;
            this.detectedCategory = null;
            this.selectedCategoryIndex = null;
            this.editingCalculationId = null;
        },
        
        resetPreciseForm: function() {
            this.preciseForm = {
                product_name: '',
                product_url: '',
                price_yuan: null,
                weight_kg: null,
                quantity: null,
                custom_rate: null,
                delivery_type: 'rail',
                markup: 1.7,
                // Поля пакинга
                packing_units_per_box: null,
                packing_box_weight: null,
                packing_box_length: null,
                packing_box_width: null,
                packing_box_height: null
            };
            this.preciseResult = null;
            this.detectedCategoryPrecise = null;
            this.selectedCategoryIndexPrecise = null;
            this.editingCalculationId = null;
            this.currentPreciseCalculationId = null;
            console.log('🔄 Форма очищена, currentPreciseCalculationId сброшен');
        },
        
        // === HISTORY MANAGEMENT ===
        loadHistory: function() {
            var self = this;
            return axios.get('/api/history').then(function(response) {
                self.history = response.data.history || [];
                self.databaseAvailable = !response.data.error;
            }).catch(function(error) {
                console.error('Ошибка загрузки истории:', error);
                self.history = [];
                self.databaseAvailable = false;
            });
        },
        
        saveCalculation: function(calculationData) {
            var self = this;
            return axios.post('/api/history', calculationData).then(function(response) {
                console.log('Расчет сохранен в историю');
                return self.loadHistory();
            }).then(function() {
                // Используем router для навигации
                self.$router.push('/history');
            }).catch(function(error) {
                console.error('Ошибка сохранения:', error);
                alert('Ошибка при сохранении расчета');
            });
        },
        
        updateCalculation: function(event) {
            var self = this;
            var id = event.id;
            var data = event.data;
            
            return axios.put('/api/history/' + id, data).then(function() {
                console.log('Расчет обновлен');
                return self.loadHistory();
            }).then(function() {
                self.editingCalculationId = null;
                // Используем router для навигации
                self.$router.push('/history');
            }).catch(function(error) {
                console.error('Ошибка обновления:', error);
                alert('Ошибка при обновлении расчета');
            });
        },
        
        toggleHistoryDetails: function(item) {
            var index = this.expandedHistory.indexOf(item.id);
            if (index > -1) {
                this.expandedHistory.splice(index, 1);
            } else {
                this.expandedHistory.push(item.id);
            }
        },
        
        editCalculation: function(item) {
            var self = this;
            
            // Отладка: проверяем данные элемента
            console.log('=== EDITING CALCULATION ===');
            console.log('Full item data:', JSON.stringify(item, null, 2));
            console.log('calculation_type:', item.calculation_type);
            console.log('packing_units_per_box:', item.packing_units_per_box);
            console.log('packing_box_weight:', item.packing_box_weight);
            
            // Определяем тип расчета и заполняем соответствующую форму
            var isPreciseCalculation = (item.calculation_type === 'precise' || (item.packing_units_per_box && item.packing_units_per_box > 0));
            
            console.log('isPreciseCalculation:', isPreciseCalculation);
            console.log('Will switch to tab:', isPreciseCalculation ? 'precise-calculator' : 'calculator');
            
            if (isPreciseCalculation) {
                // Заполняем форму точных расчетов
                this.preciseForm.product_name = item.product_name;
                this.preciseForm.product_url = item.product_url || '';
                this.preciseForm.price_yuan = item.price_yuan;
                this.preciseForm.weight_kg = item.weight_kg;
                this.preciseForm.quantity = item.quantity;
                this.preciseForm.custom_rate = item.custom_rate;
                this.preciseForm.delivery_type = item.delivery_type || 'rail';
                this.preciseForm.markup = item.markup;
                // Поля пакинга
                this.preciseForm.packing_units_per_box = item.packing_units_per_box || null;
                this.preciseForm.packing_box_weight = item.packing_box_weight || null;
                this.preciseForm.packing_box_length = item.packing_box_length || null;
                this.preciseForm.packing_box_width = item.packing_box_width || null;
                this.preciseForm.packing_box_height = item.packing_box_height || null;
                
                // Определяем категорию для точных расчетов
                axios.get('/api/category/' + encodeURIComponent(item.product_name)).then(function(response) {
                    self.detectedCategoryPrecise = response.data;
                    self.selectedCategoryIndexPrecise = self.categories.findIndex(function(cat) {
                        return cat.category === self.detectedCategoryPrecise.category;
                    });
                }).catch(function(error) {
                    self.detectedCategoryPrecise = null;
                    self.selectedCategoryIndexPrecise = null;
                });
                
                // Используем router для навигации
                this.$router.push('/precise');
                console.log('EDIT: Switched to precise tab via router');
            } else {
                // Заполняем форму быстрых расчетов
                this.form.product_name = item.product_name;
                this.form.product_url = item.product_url || '';
                this.form.price_yuan = item.price_yuan;
                this.form.weight_kg = item.weight_kg;
                this.form.quantity = item.quantity;
                this.form.custom_rate = item.custom_rate;
                this.form.delivery_type = item.delivery_type || 'rail';
                this.form.markup = item.markup;
                
                // Определяем категорию для быстрых расчетов
                axios.get('/api/category/' + encodeURIComponent(item.product_name)).then(function(response) {
                    self.detectedCategory = response.data;
                    self.selectedCategoryIndex = self.categories.findIndex(function(cat) {
                        return cat.category === self.detectedCategory.category;
                    });
                }).catch(function(error) {
                    self.detectedCategory = null;
                    self.selectedCategoryIndex = null;
                });
                
                // Используем router для навигации
                this.$router.push('/');
                console.log('EDIT: Switched to calculator tab via router');
            }

            this.editingCalculationId = item.id;

            setTimeout(function() {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }, 100);
        },
        
        copyCalculation: function(item) {
            // Отладка: проверяем данные элемента
            console.log('=== COPYING CALCULATION ===');
            console.log('Full item data:', JSON.stringify(item, null, 2));
            console.log('calculation_type:', item.calculation_type);
            console.log('packing_units_per_box:', item.packing_units_per_box);
            console.log('packing_box_weight:', item.packing_box_weight);
            
            // Определяем тип расчета и заполняем соответствующую форму
            var isPreciseCalculation = (item.calculation_type === 'precise' || (item.packing_units_per_box && item.packing_units_per_box > 0));
            
            console.log('isPreciseCalculation:', isPreciseCalculation);
            console.log('Will switch to tab:', isPreciseCalculation ? 'precise-calculator' : 'calculator');
            
            if (isPreciseCalculation) {
                // Копируем в форму точных расчетов
                this.preciseForm.product_name = item.product_name;
                this.preciseForm.product_url = item.product_url || '';
                this.preciseForm.price_yuan = item.price_yuan;
                this.preciseForm.weight_kg = item.weight_kg;
                this.preciseForm.quantity = item.quantity;
                this.preciseForm.custom_rate = item.custom_rate;
                this.preciseForm.delivery_type = item.delivery_type || 'rail';
                this.preciseForm.markup = item.markup;
                // Поля пакинга
                this.preciseForm.packing_units_per_box = item.packing_units_per_box || null;
                this.preciseForm.packing_box_weight = item.packing_box_weight || null;
                this.preciseForm.packing_box_length = item.packing_box_length || null;
                this.preciseForm.packing_box_width = item.packing_box_width || null;
                this.preciseForm.packing_box_height = item.packing_box_height || null;
                
                // Используем router для навигации
                this.$router.push('/precise');
                console.log('COPY: Switched to precise tab via router');
            } else {
                // Копируем в форму быстрых расчетов
                this.form.product_name = item.product_name;
                this.form.product_url = item.product_url || '';
                this.form.price_yuan = item.price_yuan;
                this.form.weight_kg = item.weight_kg;
                this.form.quantity = item.quantity;
                this.form.custom_rate = item.custom_rate;
                this.form.delivery_type = item.delivery_type || 'rail';
                this.form.markup = item.markup;
                
                // Используем router для навигации
                this.$router.push('/');
                console.log('COPY: Switched to calculator tab via router');
            }

            this.editingCalculationId = null;

            setTimeout(function() {
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }, 100);
        },
        
        deleteCalculation: function(item) {
            var self = this;
            return axios.delete('/api/history/' + item.id).then(function() {
                console.log('Расчет удален');
                return self.loadHistory();
            }).catch(function(error) {
                console.error('Ошибка удаления:', error);
                alert('Ошибка при удалении расчета');
            });
        },
        
        exportHistoryToCSV: function() {
            if (!this.history.length) return;
            
            var headers = [
                'Дата', 'Товар', 'Категория', 'Цена (¥)', 'Цена (₽)', 
                'Вес (кг)', 'Количество', 'Доставка', 'Ставка ($/кг)', 
                'Логистика (₽)', 'Комиссия (₽)', 'Переводы (₽)', 
                'Доставка МСК (₽)', 'Прочие (₽)', 'Итого (₽)', 'Наценка'
            ];
            
            var rows = this.history.map(function(item) {
                return [
                    new Date(item.created_at).toLocaleDateString('ru-RU'),
                    item.product_name,
                    item.category,
                    item.unit_price_yuan,
                    item.unit_price_rub.toFixed(2),
                    item.weight_kg,
                    item.quantity,
                    item.delivery_type === 'air' ? 'Авиа' : 'ЖД',
                    item.logistics_rate_usd,
                    item.logistics_cost_rub.toFixed(2),
                    item.toni_commission_rub.toFixed(2),
                    item.transfer_cost_rub.toFixed(2),
                    item.local_delivery_rub.toFixed(2),
                    item.other_costs_rub.toFixed(2),
                    item.total_cost_rub.toFixed(2),
                    item.markup
                ];
            });
            
            var csvContent = [headers].concat(rows)
                .map(function(row) {
                    return row.map(function(field) {
                        return '"' + field + '"';
                    }).join(',');
                })
                .join('\n');
            
            var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'price_calculator_history_' + new Date().toISOString().split('T')[0] + '.csv';
            link.click();
        },
        
        logout: function() {
            var self = this;
            axios.post('/api/logout').then(function() {
                window.location.href = '/login';
            }).catch(function(error) {
                console.error('Logout error:', error);
                window.location.href = '/login';
            });
        }
    },
    
        mounted: function() {
        var self = this;
        console.log('PriceCalculatorApp: App mounted, loading initial data...');
        
        return this.loadSettings().then(function() {
            return self.loadCategories();
        }).then(function() {
            return self.loadHistory();
        }).then(function() {
            console.log('PriceCalculatorApp: Initial data loaded');
        }).catch(function(error) {
            console.error('PriceCalculatorApp: Error loading initial data:', error);
        });
    },
    
    template: 
        '<!-- Header -->' +
        '<header class="header">' +
            '<div class="container">' +
                '<div class="header-content">' +
                    '<div class="logo">Price Calculator</div>' +
                    '<div class="exchange-rates">' +
                        '<div class="rate-item">1¥ = ${{ exchangeRates.yuan_to_usd.toFixed(3) }}</div>' +
                        '<div class="rate-item">1$ = {{ exchangeRates.usd_to_rub.toFixed(0) }}₽</div>' +
                        '<div class="rate-item">1¥ = {{ exchangeRates.yuan_to_rub.toFixed(2) }}₽</div>' +
                    '</div>' +
                    '<nav class="nav">' +
                        '<router-link to="/" custom v-slot="{ navigate, isActive }">' +
                            '<button @click="navigate" :class="[\'nav-button\', { active: isActive }]">' +
                                'Быстрые расчеты' +
                            '</button>' +
                        '</router-link>' +
                        '<router-link to="/precise" custom v-slot="{ navigate, isActive }">' +
                            '<button @click="navigate" :class="[\'nav-button\', { active: isActive }]">' +
                                'Точные расчеты' +
                            '</button>' +
                        '</router-link>' +
                        '<router-link to="/history" custom v-slot="{ navigate, isActive }">' +
                            '<button @click="navigate" :class="[\'nav-button\', { active: isActive }]">' +
                                'История' +
                            '</button>' +
                        '</router-link>' +
                        '<router-link to="/settings" custom v-slot="{ navigate, isActive }">' +
                            '<button @click="navigate" :class="[\'nav-button\', { active: isActive }]">' +
                                'Настройки' +
                            '</button>' +
                        '</router-link>' +
                        '<button @click="logout" class="logout-button">' +
                            'Выход' +
                        '</button>' +
                    '</nav>' +
                '</div>' +
            '</div>' +
        '</header>' +
        
        '<!-- Main Content -->' +
        '<div class="container">' +
            
            '<!-- Quick Calculator Tab -->' +
            '<div v-if="activeTab === \'calculator\'">' +
                
                '<!-- Input Form -->' +
                '<div class="card">' +
                    '<h2 class="card-title">Быстрый расчет стоимости товара</h2>' +
                    '<p class="card-subtitle">Введите данные о товаре для быстрого расчета себестоимости и цены продажи</p>' +
                    '<form @submit.prevent="performCalculation">' +
                        '<ProductForm v-model:form="form" :detected-category="detectedCategory" :categories="categories" :selected-category-index="selectedCategoryIndex" :is-calculating="isCalculating" :is-form-valid="isFormValid" :suggested-rate="suggestedRate" @product-name-change="onProductNameChange" @category-change="onCategoryChange" @calculate="performCalculation" @reset-form="resetForm" />' +
                        
                        '<!-- Submit Button -->' +
                        '<button type="submit" :disabled="isCalculating || !isFormValid" class="submit-button">' +
                            '<span v-if="isCalculating">' +
                                '<span class="loading"></span>' +
                                'Расчитываю...' +
                            '</span>' +
                            '<span v-else>' +
                                'Рассчитать стоимость' +
                            '</span>' +
                        '</button>' +
                    '</form>' +
                '</div>' +
                
                '<!-- Results -->' +
                '<ResultsDisplay :result="result" :is-calculating="isCalculating" />' +
            '</div>' +
            
            '<!-- Precise Calculator Tab -->' +
            '<div v-if="activeTab === \'precise\'">' +
                
                '<!-- Input Form -->' +
                '<div class="card">' +
                    '<h2 class="card-title">Точный расчет стоимости товара</h2>' +
                    '<p class="card-subtitle">Введите данные о товаре и его упаковке для точного расчета себестоимости и цены продажи</p>' +
                    '<form @submit.prevent="performPreciseCalculation">' +
                        '<ProductFormPrecise v-model:form="preciseForm" :detected-category="detectedCategoryPrecise" :categories="categories" :selected-category-index="selectedCategoryIndexPrecise" :is-calculating="isCalculating" :is-form-valid="isPreciseFormValid" :suggested-rate="suggestedRatePrecise" :density-warning="preciseResult ? preciseResult.density_warning : null" @product-name-change="onProductNameChangePrecise" @category-change="onCategoryChangePrecise" @calculate="performPreciseCalculation" @reset-form="resetPreciseForm" />' +
                        
                        '<!-- Submit Button -->' +
                        '<button type="submit" :disabled="isCalculating || !isPreciseFormValid" class="submit-button">' +
                            '<span v-if="isCalculating">' +
                                '<span class="loading"></span>' +
                                'Расчитываю...' +
                            '</span>' +
                            '<span v-else>' +
                                'Рассчитать стоимость (точно)' +
                            '</span>' +
                        '</button>' +
                    '</form>' +
                '</div>' +
                
                '<!-- Routes Comparison -->' +
                '<RoutesComparison v-if="preciseResult && preciseResult.routes" :routes="preciseResult.routes" :selected-route="selectedRoute" @select-route="handleSelectRoute" />' +
                
                '<!-- Results -->' +
                '<div v-if="selectedRouteData && selectedRoute" class="results-container">' +
                    '<ResultsDisplay :result="getPlainRouteData()" :is-calculating="isCalculating" />' +
                '</div>' +
            '</div>' +
            
            '<!-- History Tab -->' +
            '<div v-if="activeTab === \'history\'">' +
                '<HistoryPanel :history="history" :expanded-history="expandedHistory" @toggle-details="toggleHistoryDetails" @edit-calculation="editCalculation" @copy-calculation="copyCalculation" @delete-calculation="deleteCalculation" @export-csv="exportHistoryToCSV" />' +
            '</div>' +
            
            '<!-- Settings Tab -->' +
            '<div v-if="activeTab === \'settings\'">' +
                '<div class="card">' +
                    '<div class="settings-tabs">' +
                        '<button @click="settingsSubTab = \'general\'" :class="[\'settings-tab-btn\', { active: settingsSubTab === \'general\' }]">Общие настройки</button>' +
                        '<button @click="settingsSubTab = \'categories\'" :class="[\'settings-tab-btn\', { active: settingsSubTab === \'categories\' }]">Категории товаров</button>' +
                    '</div>' +
                    
                    '<div v-if="settingsSubTab === \'general\'">' +
                        '<SettingsPanel :settings="settings" :is-saving="isSavingSettings" @save-settings="saveSettings" />' +
                    '</div>' +
                    
                    '<div v-if="settingsSubTab === \'categories\'">' +
                        '<CategoriesPanel />' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>'
};

// Регистрируем главный компонент глобально
if (typeof window !== 'undefined') {
    window.PriceCalculatorApp = PriceCalculatorApp;
}
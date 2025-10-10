// PriceCalculatorAppV2.js - Главный компонент с двумя этапами
window.PriceCalculatorAppV2 = {
    data() {
        return {
            activeTab: 'calculator',  // 'calculator', 'history', 'settings'
            
            currentStep: 1,  // 1 = данные товара, 2 = маршруты логистики
            calculationMode: 'precise',  // 'quick' или 'precise'
            isCalculating: false,
            
            // Данные товара (Этап 1)
            productData: {
                calculation_id: null,  // ID расчета для обновления (null = новый расчет)
                name: '',
                product_url: '',  // Ссылка на товар или WeChat поставщика
                price_yuan: 0,
                quantity: 0,
                markup: 1.4,
                weight_kg: 0,
                packing_units_per_box: 0,
                packing_box_weight: 0,
                packing_box_length: 0,
                packing_box_width: 0,
                packing_box_height: 0,
                forcedCategory: null  // Принудительная категория
            },
            
            // Результаты расчета (Этап 2)
            calculationResult: null,
            selectedRoute: null,
            
            // Кастомные параметры логистики (для этого расчета)
            customLogistics: null,
            
            // Редактирование
            isEditingCategory: false,
            selectedCategory: '',  // Выбранная категория для изменения
            availableCategories: [],
            categorySearchQuery: '',  // Поисковый запрос для автокомплита
            filteredCategories: [],  // Отфильтрованные категории
            editingRoute: null,  // Какой маршрут редактируем (highway_rail, highway_air, etc.)
            
            // Быстрое редактирование на Этапе 2
            isEditingQuickParams: false,
            quickEditParams: {
                price_yuan: 0,
                quantity: 0,
                markup: 1.4
            },
            
            // История
            history: [],
            
            // Настройки
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
                },
                defaultMarkup: 1.4,
                defaultQuantity: 1000,
                autoSaveCalculations: true
            }
        };
    },
    
    computed: {
        // Готовы ли данные для перехода на Этап 2
        canProceedToStep2() {
            return this.calculationResult && this.calculationResult.routes;
        },
        
        // Проверка: является ли категория "Новая категория"
        isNewCategory() {
            return this.calculationResult && this.calculationResult.category === 'Новая категория';
        }
    },
    
    methods: {
        // Загрузка списка категорий (только названия для автокомплита)
        async loadCategories() {
            try {
                // V3 API - получаем полные данные категорий
                const v3 = window.useCalculationV3();
                const categories = await v3.getCategories();
                
                // Извлекаем только названия для автокомплита
                this.availableCategories = categories.map(cat => cat.category);
                
                console.log('📦 Загружено категорий (V3):', this.availableCategories.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        // Открыть редактирование категории
        openCategoryEdit() {
            // Ищем value категории (без материала в скобках)
            const currentCategory = this.calculationResult.category;
            // Если категория содержит материал в скобках, берем только название
            const categoryValue = currentCategory ? currentCategory.split(' (')[0] : '';
            
            // Устанавливаем начальное значение в поисковую строку
            this.categorySearchQuery = categoryValue;
            this.selectedCategory = categoryValue;
            this.isEditingCategory = true;
            this.filterCategories();
            
            console.log('📝 Открыто редактирование категории:', currentCategory, '→', categoryValue);
        },
        
        filterCategories() {
            if (!this.categorySearchQuery || this.categorySearchQuery.trim() === '') {
                this.filteredCategories = this.availableCategories.slice(0, 10); // Показываем первые 10
                return;
            }
            
            const query = this.categorySearchQuery.toLowerCase();
            this.filteredCategories = this.availableCategories
                .filter(cat => cat.label.toLowerCase().includes(query))
                .slice(0, 10); // Ограничиваем 10 результатами
        },
        
        selectCategory(categoryValue) {
            this.selectedCategory = categoryValue;
            this.categorySearchQuery = categoryValue;
            this.filteredCategories = [];
        },
        
        // Изменить категорию и пересчитать
        async changeCategory(newCategory) {
            console.log('🔄 Меняем категорию на:', newCategory);
            this.isEditingCategory = false;
            
            // Сохраняем принудительную категорию
            this.productData.forcedCategory = newCategory;
            
            // ВАЖНО: Сбрасываем кастомные пошлины/НДС для маршрутов Contract/Prologix
            // Чтобы использовались значения из новой категории
            if (this.customLogistics) {
                // Сохраняем только кастомные ставки (custom_rate), удаляем duty_rate и vat_rate
                const updatedLogistics = {};
                for (const [routeKey, params] of Object.entries(this.customLogistics)) {
                    if (params.custom_rate !== undefined && params.custom_rate !== null) {
                        updatedLogistics[routeKey] = { custom_rate: params.custom_rate };
                    }
                }
                this.customLogistics = Object.keys(updatedLogistics).length > 0 ? updatedLogistics : null;
                console.log('🔄 Сброшены кастомные пошлины/НДС, оставлены только ставки:', this.customLogistics);
            }
            
            // Пересчитываем с новой категорией
            await this.performCalculation();
        },
        
        // Быстрое редактирование параметров на Этапе 2
        openQuickEdit() {
            this.quickEditParams.price_yuan = this.productData.price_yuan;
            this.quickEditParams.quantity = this.productData.quantity;
            this.quickEditParams.markup = this.productData.markup;
            this.isEditingQuickParams = true;
            console.log('✏️ Открыто быстрое редактирование:', this.quickEditParams);
        },
        
        // Применить быстрые изменения и пересчитать
        async applyQuickEdit() {
            console.log('💾 Применяем быстрые изменения:', this.quickEditParams);
            
            // Валидация
            if (this.quickEditParams.price_yuan <= 0) {
                alert('Цена должна быть больше 0');
                return;
            }
            if (this.quickEditParams.quantity <= 0) {
                alert('Количество должно быть больше 0');
                return;
            }
            if (this.quickEditParams.markup < 1) {
                alert('Наценка должна быть не менее 1.0 (т.е. 0% наценки)');
                return;
            }
            
            // Обновляем productData
            this.productData.price_yuan = parseFloat(this.quickEditParams.price_yuan);
            this.productData.quantity = parseInt(this.quickEditParams.quantity);
            this.productData.markup = parseFloat(this.quickEditParams.markup);
            
            // Закрываем редактирование
            this.isEditingQuickParams = false;
            
            // Пересчитываем
            await this.performCalculation();
        },
        
        cancelQuickEdit() {
            this.isEditingQuickParams = false;
            console.log('❌ Быстрое редактирование отменено');
        },
        
        // Открыть редактирование маршрута
        openRouteEdit(routeKey) {
            this.editingRoute = routeKey;
            console.log('✏️ Открыто редактирование маршрута:', routeKey);
        },
        
        // Сохранить изменения маршрута и пересчитать
        async saveRouteChanges(routeKey, newParams) {
            console.log('💾 Сохранение изменений маршрута:', routeKey, newParams);
            console.log('   Старые данные маршрута:', this.calculationResult.routes[routeKey]);

            // Сохраняем кастомные параметры для этого маршрута
            if (!this.customLogistics) {
                this.customLogistics = {};
            }
            this.customLogistics[routeKey] = newParams;

            console.log('📝 Все кастомные параметры логистики:', this.customLogistics);

            // Пересчитываем с новыми параметрами (только для этого расчета)
            try {
                this.isCalculating = true;
                console.log('🔄 Начинаем пересчет...');
                
                await this.performCalculation();
                
                console.log('📊 Новые данные маршрута после пересчета:', this.calculationResult.routes[routeKey]);
                
                // Принудительное обновление UI
                this.$forceUpdate();
                
                console.log('✅ Пересчет завершен, UI обновлен');
            } catch (error) {
                console.error('❌ Ошибка пересчета:', error);
            } finally {
                this.isCalculating = false;
                this.editingRoute = null;
            }
        },
        
        // Отменить редактирование
        cancelRouteEdit() {
            this.editingRoute = null;
        },
        
        // История: Открыть/Закрыть
        // Смена вкладки
        switchTab(tabName) {
            this.activeTab = tabName;
            if (tabName === 'history') {
                this.loadHistory();
            }
        },
        
        // Сохранение настроек
        saveSettings() {
            // Сохраняем в localStorage
            localStorage.setItem('priceCalculatorSettings', JSON.stringify(this.settings));
            alert('Настройки сохранены!');
        },
        
        // Загрузка настроек из localStorage
        loadSettings() {
            const saved = localStorage.getItem('priceCalculatorSettings');
            if (saved) {
                try {
                    const savedSettings = JSON.parse(saved);
                    // Мержим с дефолтными настройками (deep merge)
                    this.settings = {
                        ...this.settings,
                        ...savedSettings,
                        currencies: { ...this.settings.currencies, ...savedSettings.currencies },
                        formula: { ...this.settings.formula, ...savedSettings.formula }
                    };
                    console.log('✅ Настройки загружены из localStorage:', this.settings);
                } catch (e) {
                    console.error('❌ Ошибка загрузки настроек из localStorage:', e);
                    // Используем дефолтные настройки
                }
            }
        },
        
        // Проверка URL и загрузка расчета по ID
        async checkUrlAndLoadCalculation() {
            // Получаем ID из URL: /v2?calculation=123 или /v2/123
            const urlParams = new URLSearchParams(window.location.search);
            const calculationId = urlParams.get('calculation');
            
            if (calculationId) {
                console.log(`🔗 Найден ID расчета в URL: ${calculationId}`);
                await this.loadCalculationById(calculationId);
            }
        },
        
        // Загрузка расчета по ID
        async loadCalculationById(calculationId) {
            try {
                console.log(`📖 Загрузка расчета #${calculationId}...`);
                
                const response = await axios.get(`/api/v2/calculation/${calculationId}`);
                const calculation = response.data;
                
                console.log('✅ Расчет загружен:', calculation);
                console.log('📦 Маршруты:', calculation.routes);
                
                // Заполняем productData
                this.productData.calculation_id = parseInt(calculationId);  // Сохраняем ID для обновления
                this.productData.name = calculation.product_name;
                this.productData.product_url = calculation.product_url || '';
                this.productData.price_yuan = calculation.unit_price_yuan;
                this.productData.quantity = calculation.quantity;
                this.productData.markup = calculation.markup;
                this.productData.weight_kg = calculation.weight_kg || 0;
                
                // Если есть данные пакинга
                if (calculation.packing_units_per_box) {
                    this.productData.packing_units_per_box = calculation.packing_units_per_box;
                    this.productData.packing_box_weight = calculation.packing_box_weight;
                    this.productData.packing_box_length = calculation.packing_box_length;
                    this.productData.packing_box_width = calculation.packing_box_width;
                    this.productData.packing_box_height = calculation.packing_box_height;
                    this.calculationMode = 'precise';
                } else {
                    this.calculationMode = 'quick';
                }
                
                // Устанавливаем результат расчета
                this.calculationResult = calculation;
                
                // Автоматически выбираем самый дешевый маршрут
                if (calculation.routes) {
                    let cheapestRoute = null;
                    let lowestCost = Infinity;
                    
                    for (const key in calculation.routes) {
                        const cost = calculation.routes[key].cost_rub || calculation.routes[key].total_cost_rub;
                        if (cost < lowestCost) {
                            lowestCost = cost;
                            cheapestRoute = key;
                        }
                    }
                    
                    this.selectedRoute = cheapestRoute;
                    console.log(`✅ Самый дешевый маршрут: ${cheapestRoute} (${lowestCost.toLocaleString()} ₽)`);
                }
                
                // Открываем вкладку калькулятора
                this.activeTab = 'calculator';
                
                // Ждём следующий tick для обновления DOM
                await this.$nextTick();
                
                // Переходим сразу на Этап 2 (результаты)
                this.currentStep = 2;
                
                console.log('✅ Переход на Этап 2:', {
                    currentStep: this.currentStep,
                    hasResult: !!this.calculationResult,
                    hasRoutes: !!this.calculationResult?.routes,
                    selectedRoute: this.selectedRoute
                });
                
                // Принудительно обновляем UI
                this.$forceUpdate();
                
            } catch (error) {
                console.error('❌ Ошибка загрузки расчета:', error);
                alert(`Не удалось загрузить расчет #${calculationId}: ${error.response?.data?.detail || error.message}`);
            }
        },
        
        // История: Загрузить из API
        async loadHistory() {
            try {
                const response = await axios.get('/api/v2/history');
                this.history = response.data;
                console.log('📚 Загружена история:', this.history.length, 'расчетов');
            } catch (error) {
                console.error('❌ Ошибка загрузки истории:', error);
                this.history = [];
            }
        },
        
        // История: Скопировать данные из истории (создать новый расчет)
        copyFromHistory(item) {
            console.log('📋 Копирование из истории (новый расчет):', item);
            this._loadDataFromHistory(item, false);  // false = не устанавливать calculation_id
            // Очищаем URL (это новый расчет)
            window.history.pushState({}, '', '/v2');
            console.log('📍 URL очищен (новый расчет)');
        },
        
        // История: Редактировать расчет (обновить существующий)
        editFromHistory(item) {
            console.log('✏️ Редактирование расчета #' + item.id);
            this._loadDataFromHistory(item, true);  // true = установить calculation_id
            // Обновляем URL
            const newUrl = `/v2?calculation=${item.id}`;
            window.history.pushState({}, '', newUrl);
            console.log(`📍 URL обновлён: ${newUrl}`);
        },
        
        // Вспомогательный метод для загрузки данных из истории
        _loadDataFromHistory(item, setCalculationId) {
            // ВАЖНО: Обновляем поля РЕАКТИВНО, а не перезаписываем объект
            this.productData.calculation_id = setCalculationId ? item.id : null;  // Устанавливаем ID только при редактировании
            this.productData.name = item.product_name;
            this.productData.product_url = item.product_url || '';
            this.productData.price_yuan = item.price_yuan;
            this.productData.quantity = item.quantity;
            this.productData.markup = item.markup;
            this.productData.weight_kg = item.weight_kg || 0;
            
            // Копируем данные пакинга если они есть
            this.productData.packing_units_per_box = item.packing_units_per_box || 0;
            this.productData.packing_box_weight = item.packing_box_weight || 0;
            this.productData.packing_box_length = item.packing_box_length || 0;
            this.productData.packing_box_width = item.packing_box_width || 0;
            this.productData.packing_box_height = item.packing_box_height || 0;
            this.productData.forcedCategory = null;
            
            console.log('📦 Данные пакинга скопированы:', {
                units: item.packing_units_per_box,
                weight: item.packing_box_weight,
                dimensions: `${item.packing_box_length}×${item.packing_box_width}×${item.packing_box_height}`
            });
            
            // Устанавливаем режим калькуляции
            if (item.calculation_type === 'precise') {
                this.calculationMode = 'precise';
            } else {
                this.calculationMode = 'quick';
            }
            
            // Переключаемся на вкладку калькулятора
            this.activeTab = 'calculator';
            
            // Переходим на Этап 1
            this.currentStep = 1;
            
            // Сбрасываем результаты расчета
            this.calculationResult = null;
            this.selectedRoute = null;
            
            // Принудительно обновляем UI
            this.$forceUpdate();
            
            console.log('✅ Данные загружены:', {
                calculation_id: this.productData.calculation_id,
                mode: setCalculationId ? 'редактирование' : 'копирование'
            });
        },
        
        // Получить ключ самого дешевого маршрута
        getCheapestRoute() {
            if (!this.calculationResult?.routes) return null;
            
            let cheapestKey = null;
            let lowestCost = Infinity;
            
            for (const key in this.calculationResult.routes) {
                const cost = this.calculationResult.routes[key].cost_rub || this.calculationResult.routes[key].cost_per_unit_rub;
                if (cost < lowestCost) {
                    lowestCost = cost;
                    cheapestKey = key;
                }
            }
            
            return cheapestKey;
        },
        
        // Расчет общего объема груза
        getTotalVolume() {
            if (!this.calculationResult?.density_info?.volume_m3 || !this.productData?.packing_units_per_box) {
                return null;
            }
            const boxVolume = this.calculationResult.density_info.volume_m3;
            const boxesCount = this.productData.quantity / this.productData.packing_units_per_box;
            const totalVolume = boxVolume * boxesCount;
            return totalVolume.toFixed(1);
        },
        
        // Обработка смены режима расчета
        handleModeChanged(mode) {
            this.calculationMode = mode;
            console.log('Режим изменен:', mode);
        },
        
        // Выполнение расчета и переход на Этап 2        
        applyCustomLogistics(settings) {
            console.log('🔧 Применение кастомных настроек логистики:', settings);
            this.customLogistics = settings;
            this.showSettingsModal = false;
            
            // Пересчитываем с новыми параметрами
            this.performCalculation();
        },
        
        async performCalculation() {
            this.isCalculating = true;
            
            try {
                // Подготовка данных для API
                const calculationData = {
                    product_name: this.productData.name,
                    product_url: this.productData.product_url || '',
                    price_yuan: this.productData.price_yuan,
                    quantity: this.productData.quantity,
                    markup: this.productData.markup,
                    is_precise_calculation: this.calculationMode === 'precise'
                };
                
                // Добавляем данные в зависимости от режима
                if (this.calculationMode === 'quick') {
                    calculationData.weight_kg = this.productData.weight_kg;
                } else {
                    // Полный режим - данные упаковки
                    calculationData.weight_kg = 0;  // Будет рассчитан из пакинга
                    calculationData.packing_units_per_box = this.productData.packing_units_per_box;
                    calculationData.packing_box_weight = this.productData.packing_box_weight;
                    calculationData.packing_box_length = this.productData.packing_box_length;
                    calculationData.packing_box_width = this.productData.packing_box_width;
                    calculationData.packing_box_height = this.productData.packing_box_height;
                }
                
                // Если есть кастомные параметры логистики - добавляем
                if (this.customLogistics) {
                    calculationData.custom_logistics = this.customLogistics;
                }
                
                // Если есть принудительная категория - добавляем
                if (this.productData.forcedCategory) {
                    calculationData.forced_category = this.productData.forcedCategory;
                }
                
                console.log('📤 Отправка данных на расчет (V3):', calculationData);
                
                // ✨ V3 API - используем composable
                const v3 = window.useCalculationV3();
                let result;
                
                if (this.productData.calculation_id) {
                    // Обновление существующего расчета
                    console.log(`🔄 Обновление расчета #${this.productData.calculation_id}`);
                    result = await v3.updateCalculation(this.productData.calculation_id, calculationData);
                    console.log(`✅ Расчет #${this.productData.calculation_id} обновлён`);
                } else {
                    // Создание нового расчета через V3
                    console.log('✨ Создание нового расчета (V3)');
                    result = await v3.calculate(calculationData);
                    
                    // Сохраняем ID нового расчета
                    if (result.id) {
                        this.productData.calculation_id = result.id;
                        console.log(`✅ Новый расчет создан с ID: ${result.id}`);
                        // Обновляем URL
                        const newUrl = `/v2?calculation=${result.id}`;
                        window.history.pushState({}, '', newUrl);
                        console.log(`📍 URL обновлён: ${newUrl}`);
                    }
                }
                
                console.log('📦 Получен результат от API (V3):', result);
                
                // Обновляем результаты расчета
                this.calculationResult = result;
                
                // Логируем маршруты для отладки
                if (result.routes) {
                    console.log('🛣️ Маршруты в ответе:');
                    Object.keys(result.routes).forEach(key => {
                        const route = result.routes[key];
                        console.log(`   ${key}: per_unit=${route.per_unit}₽, cost_rub=${route.cost_rub}₽`);
                    });
                }
                
                // Автоматически выбираем самый дешевый маршрут
                if (this.calculationResult.routes) {
                    const routes = this.calculationResult.routes;
                    let cheapestRoute = null;
                    let lowestCost = Infinity;
                    
                    console.log('🔍 Поиск самого дешевого маршрута:');
                    for (const key in routes) {
                        const cost = routes[key].cost_rub || routes[key].total_cost_rub;
                        console.log(`  ${key}: ${cost.toLocaleString()} руб (cost_rub: ${routes[key].cost_rub}, total_cost_rub: ${routes[key].total_cost_rub})`);
                        
                        if (cost < lowestCost) {
                            lowestCost = cost;
                            cheapestRoute = key;
                        }
                    }
                    
                    this.selectedRoute = cheapestRoute;
                    console.log(`✅ Самый дешевый маршрут: ${cheapestRoute} (${lowestCost.toLocaleString()} руб)`);
                }
                
                // Переход на Этап 2
                this.currentStep = 2;
                
            } catch (error) {
                console.error('Ошибка расчета:', error);
                alert('Ошибка при расчете. Проверьте введенные данные.');
            } finally {
                this.isCalculating = false;
            }
        },
        
        // Возврат к Этапу 1
        backToStep1() {
            this.currentStep = 1;
            // Данные товара сохраняются, можно изменить и пересчитать
        },
        
        // Создать копию расчета (сбросить calculation_id)
        saveAsNew() {
            console.log('📋 Создание копии расчета');
            this.productData.calculation_id = null;
            // Очищаем URL
            window.history.pushState({}, '', '/v2');
            console.log('📍 URL очищен (режим создания нового)');
            alert('Теперь при нажатии "Рассчитать" будет создан новый расчет');
        },
        
        // Выбор маршрута
        selectRoute(routeKey) {
            this.selectedRoute = routeKey;
            console.log('Выбран маршрут:', routeKey);
        },
        
        // Открытие настроек логистики
        openSettings() {
            this.showSettingsModal = true;
        },
        
        // Применение кастомных параметров
        applyCustomLogistics(params) {
            this.customLogistics = params;
            this.showSettingsModal = false;
            
            // Пересчитываем с новыми параметрами
            this.performCalculation();
        },
        
        // Сброс кастомных параметров
        resetCustomLogistics() {
            this.customLogistics = null;
            this.showSettingsModal = false;
            
            // Пересчитываем с дефолтными параметрами
            this.performCalculation();
        }
    },
    
    mounted() {
        // Загружаем список категорий при инициализации
        this.loadCategories();
        
        // Загружаем сохраненные настройки
        this.loadSettings();
        
        // Проверяем URL - если есть ID расчета, загружаем его
        this.checkUrlAndLoadCalculation();
    },
    
    template: `
        <div class="price-calculator-v2" style="max-width: 1200px; margin: 0 auto; padding: 20px;">
            <!-- Header с вкладками -->
            <div style="margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <h1 style="font-size: 24px; font-weight: 700; color: #111827;">Калькулятор цен</h1>
                    
                    <!-- Актуальный курс -->
                    <div style="display: flex; gap: 16px; font-size: 13px; color: #6b7280;">
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-weight: 500;">¥ → $:</span>
                            <span style="font-weight: 600; color: #111827;">{{ settings.currencies.yuan_to_usd }}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-weight: 500;">$ → ₽:</span>
                            <span style="font-weight: 600; color: #111827;">{{ settings.currencies.usd_to_rub }}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 6px;">
                            <span style="font-weight: 500;">¥ → ₽:</span>
                            <span style="font-weight: 600; color: #111827;">{{ (settings.currencies.yuan_to_usd * settings.currencies.usd_to_rub).toFixed(2) }}</span>
                        </div>
                    </div>
                </div>
                
                <!-- Вкладки -->
                <div style="display: flex; gap: 4px; border-bottom: 2px solid #e5e7eb;">
                    <button 
                        @click="switchTab('calculator')"
                        :style="'padding: 12px 24px; background: none; border: none; border-bottom: 2px solid ' + (activeTab === 'calculator' ? '#111827' : 'transparent') + '; cursor: pointer; font-size: 14px; font-weight: ' + (activeTab === 'calculator' ? '600' : '400') + '; color: ' + (activeTab === 'calculator' ? '#111827' : '#6b7280') + '; margin-bottom: -2px; transition: all 0.2s;'"
                    >
                        Расчет
                    </button>
                    <button 
                        @click="switchTab('history')"
                        :style="'padding: 12px 24px; background: none; border: none; border-bottom: 2px solid ' + (activeTab === 'history' ? '#111827' : 'transparent') + '; cursor: pointer; font-size: 14px; font-weight: ' + (activeTab === 'history' ? '600' : '400') + '; color: ' + (activeTab === 'history' ? '#111827' : '#6b7280') + '; margin-bottom: -2px; transition: all 0.2s;'"
                    >
                        История
                    </button>
                    <button 
                        @click="switchTab('settings')"
                        :style="'padding: 12px 24px; background: none; border: none; border-bottom: 2px solid ' + (activeTab === 'settings' ? '#111827' : 'transparent') + '; cursor: pointer; font-size: 14px; font-weight: ' + (activeTab === 'settings' ? '600' : '400') + '; color: ' + (activeTab === 'settings' ? '#111827' : '#6b7280') + '; margin-bottom: -2px; transition: all 0.2s;'"
                    >
                        Настройки
                    </button>
                </div>
            </div>
            
            <!-- Вкладка: Расчет -->
            <div v-if="activeTab === 'calculator'">
                <!-- Прогресс -->
                <div style="margin-bottom: 24px;">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="flex: 1; display: flex; align-items: center; gap: 8px;">
                            <div :style="'width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px;' + (currentStep === 1 ? 'background: #111827; color: white;' : 'background: #10b981; color: white;')">
                                {{ currentStep > 1 ? '✓' : '1' }}
                            </div>
                            <span style="font-size: 14px; font-weight: 500; color: #374151;">Данные товара</span>
                        </div>
                        
                        <div style="flex: 1; height: 2px; background: #e5e7eb;"></div>
                        
                        <div style="flex: 1; display: flex; align-items: center; gap: 8px;">
                            <div :style="'width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 14px;' + (currentStep === 2 ? 'background: #111827; color: white;' : 'background: #e5e7eb; color: #9ca3af;')">
                                2
                            </div>
                            <span :style="'font-size: 14px; font-weight: 500;' + (currentStep === 2 ? 'color: #374151;' : 'color: #9ca3af;')">
                                Выбор маршрута
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- Этап 1: Данные товара -->
                <div v-if="currentStep === 1" style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <ProductFormV2 
                    v-model="productData"
                    :calculation-mode="calculationMode"
                    :is-calculating="isCalculating"
                    @mode-changed="handleModeChanged"
                    @submit="performCalculation"
                />
            </div>
            
            <!-- Этап 2: Маршруты логистики -->
            <div v-if="currentStep === 2" style="display: flex; flex-direction: column; gap: 20px;">
                <!-- Кнопки управления -->
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <button 
                        @click="backToStep1"
                        style="padding: 8px 16px; background: white; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; color: #374151; cursor: pointer; transition: all 0.2s;"
                    >
                        ← Изменить данные товара
                    </button>
                    
                    <!-- Кнопка "Сохранить как новый" (только если редактируем существующий расчет) -->
                    <button 
                        v-if="productData.calculation_id"
                        @click="saveAsNew"
                        style="padding: 8px 16px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; color: #374151; cursor: pointer; transition: all 0.2s;"
                        title="Создать новый расчет на основе текущего"
                    >
                        💾 Сохранить как новый
                    </button>
                </div>
                
                <!-- Сводка по товару и грузу -->
                <div style="background: white; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="margin-bottom: 16px;">
                        <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin: 0 0 6px 0;">
                            {{ productData.name || 'Товар' }}
                        </h3>
                        <div v-if="productData.product_url" style="font-size: 13px; color: #6b7280; word-break: break-all;">
                            <a :href="productData.product_url.startsWith('http') ? productData.product_url : '#'" 
                               :target="productData.product_url.startsWith('http') ? '_blank' : '_self'"
                               style="color: #3b82f6; text-decoration: none;"
                               @mouseover="$event.target.style.textDecoration='underline'"
                               @mouseout="$event.target.style.textDecoration='none'">
                                {{ productData.product_url }}
                            </a>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                        <!-- Колонка 1: Основные данные -->
                        <div>
                            <div style="display: grid; gap: 8px;">
                                <!-- Режим просмотра -->
                                <template v-if="!isEditingQuickParams">
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                                        <span style="color: #6b7280; font-size: 13px;">Количество</span>
                                        <span style="color: #111827; font-weight: 600; font-size: 13px;">{{ productData.quantity.toLocaleString() }} шт</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                                        <span style="color: #6b7280; font-size: 13px;">Цена за шт (завод)</span>
                                        <span style="color: #111827; font-weight: 600; font-size: 13px;">{{ calculationResult?.unit_price_yuan || 0 }} ¥</span>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                                        <span style="color: #6b7280; font-size: 13px;">Наценка</span>
                                        <span style="color: #111827; font-weight: 600; font-size: 13px;">{{ ((productData.markup - 1) * 100).toFixed(0) }}%</span>
                                    </div>
                                    <div style="padding: 8px 0;">
                                        <button 
                                            @click="openQuickEdit"
                                            style="padding: 6px 12px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; font-size: 12px; cursor: pointer; color: #111827; font-weight: 500; transition: all 0.2s; display: flex; align-items: center; gap: 6px;"
                                            onmouseover="this.style.background='#e5e7eb'; this.style.borderColor='#9ca3af'"
                                            onmouseout="this.style.background='#f3f4f6'; this.style.borderColor='#d1d5db'"
                                        >
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                            </svg>
                                            Редактировать параметры
                                        </button>
                                    </div>
                                </template>
                                
                                <!-- Режим редактирования -->
                                <template v-else>
                                    <div style="padding: 12px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                                        <div style="display: grid; gap: 12px;">
                                            <div>
                                                <label style="display: block; color: #6b7280; font-size: 12px; margin-bottom: 4px; font-weight: 500;">Количество (шт)</label>
                                                <input 
                                                    v-model.number="quickEditParams.quantity"
                                                    type="number"
                                                    min="1"
                                                    step="1"
                                                    style="width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                                                />
                                            </div>
                                            <div>
                                                <label style="display: block; color: #6b7280; font-size: 12px; margin-bottom: 4px; font-weight: 500;">Цена за шт (¥)</label>
                                                <input 
                                                    v-model.number="quickEditParams.price_yuan"
                                                    type="number"
                                                    min="0.01"
                                                    step="0.01"
                                                    style="width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                                                />
                                            </div>
                                            <div>
                                                <label style="display: block; color: #6b7280; font-size: 12px; margin-bottom: 4px; font-weight: 500;">Наценка (1.0 = 0%, 1.4 = 40%)</label>
                                                <input 
                                                    v-model.number="quickEditParams.markup"
                                                    type="number"
                                                    min="1.0"
                                                    step="0.1"
                                                    style="width: 100%; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                                                />
                                                <div style="color: #6b7280; font-size: 11px; margin-top: 2px;">
                                                    {{ ((quickEditParams.markup - 1) * 100).toFixed(0) }}% наценки
                                                </div>
                                            </div>
                                            <div style="display: flex; gap: 8px; margin-top: 4px;">
                                                <button 
                                                    @click="applyQuickEdit"
                                                    style="flex: 1; padding: 6px 12px; background: #111827; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer; font-weight: 500;"
                                                >
                                                    Применить и пересчитать
                                                </button>
                                                <button 
                                                    @click="cancelQuickEdit"
                                                    style="padding: 6px 12px; background: white; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; cursor: pointer;"
                                                >
                                                    Отмена
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </template>
                                <div v-if="calculationResult && calculationResult.category" style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0;">
                                    <span style="color: #6b7280; font-size: 13px;">Категория</span>
                                    <div v-if="!isEditingCategory" style="display: flex; align-items: center; gap: 6px;">
                                        <span style="color: #111827; font-weight: 600; font-size: 13px;">{{ calculationResult.category }}</span>
                                        <button 
                                            @click="openCategoryEdit"
                                            title="Изменить категорию"
                                            style="padding: 4px; background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; cursor: pointer; display: flex; align-items: center; transition: all 0.2s;"
                                            onmouseover="this.style.borderColor='#111827'; this.style.background='#f9fafb'"
                                            onmouseout="this.style.borderColor='#e5e7eb'; this.style.background='transparent'"
                                        >
                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                                            </svg>
                                        </button>
                                    </div>
                                    <div v-else style="position: relative; display: flex; gap: 8px; align-items: center;">
                                        <div style="position: relative;">
                                            <input 
                                                v-model="categorySearchQuery"
                                                @input="filterCategories"
                                                placeholder="Начните вводить категорию..."
                                                style="padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; font-weight: 600; min-width: 300px;"
                                            />
                                            <!-- Автокомплит dropdown -->
                                            <div v-if="filteredCategories.length > 0" style="position: absolute; top: 100%; left: 0; right: 0; background: white; border: 1px solid #d1d5db; border-top: none; border-radius: 0 0 4px 4px; max-height: 250px; overflow-y: auto; z-index: 1000; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                                <div 
                                                    v-for="cat in filteredCategories" 
                                                    :key="cat.value"
                                                    @click="selectCategory(cat.value)"
                                                    style="padding: 8px 10px; cursor: pointer; font-size: 13px; border-bottom: 1px solid #f3f4f6;"
                                                    onmouseover="this.style.background='#f9fafb'"
                                                    onmouseout="this.style.background='white'"
                                                >
                                                    {{ cat.label }}
                                                </div>
                                            </div>
                                        </div>
                                        <button 
                                            @click="changeCategory(selectedCategory)"
                                            :disabled="!selectedCategory"
                                            style="padding: 4px 12px; background: #111827; color: white; border: none; border-radius: 4px; font-size: 12px; cursor: pointer;"
                                            :style="{opacity: selectedCategory ? 1 : 0.5, cursor: selectedCategory ? 'pointer' : 'not-allowed'}"
                                        >
                                            Применить
                                        </button>
                                        <button 
                                            @click="isEditingCategory = false; filteredCategories = []"
                                            style="padding: 4px 12px; background: white; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; cursor: pointer;"
                                        >
                                            Отмена
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Колонка 2: Данные груза -->
                        <div>
                            <div style="display: grid; gap: 8px;">
                                <div v-if="calculationResult?.weight_kg" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                                    <span style="color: #6b7280; font-size: 13px;">Вес 1 шт</span>
                                    <span style="color: #111827; font-weight: 600; font-size: 13px;">{{ calculationResult.weight_kg.toFixed(2) }} кг</span>
                                </div>
                                <div v-if="calculationResult?.estimated_weight" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                                    <span style="color: #6b7280; font-size: 13px;">Общий вес груза</span>
                                    <span style="color: #111827; font-weight: 700; font-size: 13px;">{{ calculationResult.estimated_weight.toFixed(1) }} кг</span>
                                </div>
                                <div v-if="getTotalVolume()" style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f3f4f6;">
                                    <span style="color: #6b7280; font-size: 13px;">Общий объем груза</span>
                                    <span style="color: #111827; font-weight: 700; font-size: 13px;">{{ getTotalVolume() }} м³</span>
                                </div>
                                <div v-if="calculationResult?.density_info?.density_kg_m3" style="display: flex; justify-content: space-between; padding: 8px 0;">
                                    <span style="color: #6b7280; font-size: 13px;">Плотность</span>
                                    <span style="color: #111827; font-weight: 600; font-size: 13px;">{{ calculationResult.density_info.density_kg_m3.toFixed(1) }} кг/м³</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Таблица маршрутов -->
                <div style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h2 style="font-size: 18px; font-weight: 600; color: #111827; margin: 0 0 20px 0;">
                        Сравнение маршрутов логистики
                    </h2>
                    
                    <div v-if="calculationResult && calculationResult.routes" style="display: flex; flex-direction: column; gap: 12px;">
                        <div 
                            v-for="(route, key) in calculationResult.routes" 
                            :key="key"
                            :style="'padding: 16px; border: 2px solid; border-radius: 8px; transition: all 0.2s;' + (selectedRoute === key ? 'border-color: #111827; background: #f9fafb;' : 'border-color: #e5e7eb; background: white;')"
                        >
                            <div 
                                @click="selectRoute(key)"
                                style="cursor: pointer;"
                            >
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <div style="font-size: 15px; font-weight: 600; color: #111827;">
                                            {{ route.name }}
                                        </div>
                                        <!-- Метка самого выгодного маршрута -->
                                        <span v-if="getCheapestRoute() === key" style="background: #111827; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">
                                            ВЫГОДНЕЕ
                                        </span>
                                    </div>
                                    <div style="font-size: 13px; color: #6b7280;">
                                        {{ route.delivery_days }} дней
                                    </div>
                                </div>
                                
                                <!-- Море контейнером: информация о контейнерах -->
                                <div v-if="key === 'sea_container' && route.containers_40ft !== undefined" style="padding: 8px 12px; background: #f0fdf4; border-radius: 6px; margin-top: 8px;">
                                    <div style="font-size: 12px; color: #059669; font-weight: 600; margin-bottom: 4px;">
                                        Контейнеры:
                                        <span v-if="route.containers_40ft > 0">{{ route.containers_40ft }}×40ft</span>
                                        <span v-if="route.containers_40ft > 0 && route.containers_20ft > 0"> + </span>
                                        <span v-if="route.containers_20ft > 0">{{ route.containers_20ft }}×20ft</span>
                                    </div>
                                    <div v-if="route.remaining_capacity_m3" style="font-size: 11px; color: #047857;">
                                        Остается <strong>{{ route.remaining_capacity_m3.toFixed(1) }} м³</strong> свободного места
                                    </div>
                                </div>
                                
                                <!-- Новый порядок: Цена продажи → Себестоимость → Прибыль -->
                                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 13px;">
                                    <div>
                                        <div style="color: #6b7280; margin-bottom: 2px;">Цена продажи</div>
                                        <div style="font-weight: 700; color: #111827; font-size: 14px;">{{ route.sale_per_unit_rub.toLocaleString() }} ₽/шт</div>
                                    </div>
                                    <div>
                                        <div style="color: #6b7280; margin-bottom: 2px;">Себестоимость</div>
                                        <div style="font-weight: 600; color: #6b7280;">{{ route.cost_per_unit_rub.toLocaleString() }} ₽/шт</div>
                                    </div>
                                    <div>
                                        <div style="color: #6b7280; margin-bottom: 2px;">Прибыль</div>
                                        <div style="font-weight: 600; color: #111827;">{{ (route.sale_per_unit_rub - route.cost_per_unit_rub).toLocaleString() }} ₽/шт</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Редактор параметров маршрута -->
                            <RouteEditorV2
                                :route-key="key"
                                :route="route"
                                :is-new-category="isNewCategory"
                                @save="saveRouteChanges"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- Детальный расчет выбранного маршрута -->
                <RouteDetailsV2
                    v-if="selectedRoute"
                    :route="calculationResult.routes[selectedRoute]"
                    :route-type="selectedRoute"
                    :result="calculationResult"
                />
            </div>
            </div>
            <!-- конец вкладки calculator -->
            
            <!-- Вкладка: История -->
            <div v-if="activeTab === 'history'">
                <div style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <h2 style="font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 16px;">История расчетов</h2>
                    <HistoryPanelV2 
                        :history="history"
                        @copy="copyFromHistory"
                        @edit="editFromHistory"
                        @refresh="loadHistory"
                    />
                </div>
            </div>
            
            <!-- Вкладка: Настройки -->
            <div v-if="activeTab === 'settings'">
                <SettingsPanelV2
                    v-model="settings"
                    @save="saveSettings"
                />
                
                <!-- Информация о системе -->
                <div style="margin-top: 20px; padding: 16px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="font-size: 14px; font-weight: 500; color: #111827; margin-bottom: 8px;">
                        Информация о системе
                    </div>
                    <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                        <div>Версия: 2.0</div>
                        <div>Последнее обновление: 08.10.2025</div>
                        <div>Всего расчетов в истории: {{ history.length }}</div>
                    </div>
                </div>
            </div>
        </div>
    `
};


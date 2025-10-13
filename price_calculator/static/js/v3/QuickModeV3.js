// QuickModeV3.js - Быстрый режим расчёта (Position + Calculation)
window.QuickModeV3 = {
    template: `
    <div class="quick-mode">
        <div class="card">
            <h2 class="card-title">Быстрый расчёт</h2>
            
            <form @submit.prevent="calculate" class="form">
                
                <!-- Название товара -->
                <div class="form-group">
                    <label for="product-name">Название товара *</label>
                    <input
                        id="product-name"
                        v-model="productName"
                        type="text"
                        placeholder="Например: Футболка хлопковая"
                        required
                        class="form-input"
                        @input="detectCategory"
                    />
                </div>
                
                <!-- Категория (автоопределяется) -->
                <div class="form-group">
                    <label for="category">
                        Категория 
                        <span style="color: #6b7280; font-size: 13px;">(автоопределяется)</span>
                    </label>
                    <input
                        id="category"
                        v-model="category"
                        type="text"
                        list="categories-list"
                        placeholder="Определится автоматически"
                        class="form-input"
                    />
                    <datalist id="categories-list">
                        <option v-for="cat in availableCategories" :key="cat" :value="cat">
                    </datalist>
                </div>
                
                <!-- Фабрика -->
                <div class="form-group">
                    <label for="factory">Фабрика (WeChat / URL)</label>
                    <input
                        id="factory"
                        v-model="factoryUrl"
                        type="text"
                        placeholder="https://... или WeChat ID"
                        class="form-input"
                    />
                </div>
                
                <!-- Цена и Количество -->
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label for="price">Цена (¥) *</label>
                        <input
                            id="price"
                            v-model.number="priceYuan"
                            type="number"
                            step="0.01"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="quantity">Кол-во *</label>
                        <input
                            id="quantity"
                            v-model.number="quantity"
                            type="number"
                            required
                            class="form-input"
                        />
                    </div>
                </div>
                    
                <!-- Переключатель режимов -->
                <div class="mode-toggle">
                    <label class="toggle-label">
                        <input
                            type="radio"
                            :value="false"
                            v-model="detailedMode"
                            class="toggle-radio"
                        />
                        <span>По весу</span>
                    </label>
                    <label class="toggle-label">
                        <input
                            type="radio"
                            :value="true"
                            v-model="detailedMode"
                            class="toggle-radio"
                        />
                        <span>Детальный (упаковка)</span>
                    </label>
                </div>
                
                <!-- Вес (быстрый режим) -->
                <div v-if="!detailedMode" class="form-group">
                    <label for="weight">Вес 1 единицы (кг) *</label>
                    <input
                        id="weight"
                        v-model.number="weightKg"
                        type="number"
                        step="0.01"
                        required
                        class="form-input"
                    />
                </div>
                
                <!-- Паккинг (детальный режим) -->
                <div v-else class="packing-section">
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="units-per-box">Штук в коробке *</label>
                            <input
                                id="units-per-box"
                                v-model.number="packingUnitsPerBox"
                                type="number"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="box-weight">Вес коробки (кг) *</label>
                            <input
                                id="box-weight"
                                v-model.number="packingBoxWeight"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="box-length">Длина (м) *</label>
                            <input
                                id="box-length"
                                v-model.number="packingBoxLength"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="box-width">Ширина (м) *</label>
                            <input
                                id="box-width"
                                v-model.number="packingBoxWidth"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="box-height">Высота (м) *</label>
                            <input
                                id="box-height"
                                v-model.number="packingBoxHeight"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- Наценка -->
                <div class="form-group">
                    <label for="markup">Наценка *</label>
                    <input
                        id="markup"
                        v-model.number="markup"
                        type="number"
                        step="0.01"
                        required
                        class="form-input"
                    />
                </div>
                
                <!-- Кнопка расчёта -->
                <div class="form-actions">
                    <button
                        type="submit"
                        :disabled="isCalculating"
                        class="btn-primary"
                    >
                        {{ isCalculating ? 'Расчёт...' : 'Рассчитать' }}
                    </button>
                </div>
            </form>
        </div>
        
        <!-- Второй этап: кастомные параметры логистики -->
        <CustomLogisticsFormV3
            v-if="needsCustomParams"
            :category="category"
            :routes="placeholderRoutes"
            @apply="applyCustomLogistics"
            @cancel="cancelCustomParams"
        />
        
        <!-- Результаты - детальный вид -->
        <div v-if="result && !needsCustomParams" class="card" style="margin-top: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 class="card-title">Результаты расчёта</h2>
                <button @click="reset" class="btn-text">Новый расчёт</button>
            </div>
            
            <!-- Информация о товаре -->
            <div class="result-summary">
                <div class="summary-row">
                    <span>Товар:</span>
                    <strong>{{ result.product_name }}</strong>
                </div>
                <div class="summary-row">
                    <span>Категория:</span>
                    <strong>{{ result.category }}</strong>
                </div>
                <div class="summary-row">
                    <span>Количество:</span>
                    <strong>{{ result.quantity }} шт</strong>
                </div>
                <div class="summary-row">
                    <span>Наценка:</span>
                    <strong>{{ result.markup }}x</strong>
                </div>
            </div>
            
            <!-- Краткие результаты по маршрутам (раскрываются по клику) -->
            <div v-for="(route, key) in result.routes" :key="key" class="route-details">
                <div class="route-header" @click="toggleRoute(key)" style="cursor: pointer;">
                    <h3 class="route-title">{{ formatRouteName(key) }}</h3>
                    <div class="route-quick-info">
                        <div class="route-prices">
                            <span class="route-label">Себестоимость:</span>
                            <span class="route-price">{{ formatPrice(route.cost_per_unit_rub || 0) }}₽</span>
                            <span class="route-divider">|</span>
                            <span class="route-label">Продажа:</span>
                            <span class="route-price">{{ formatPrice(route.sale_per_unit_rub || 0) }}₽</span>
                            <span class="route-divider">|</span>
                            <span class="route-label">Прибыль:</span>
                            <span class="route-price">{{ formatPrice((route.sale_per_unit_rub || 0) - (route.cost_per_unit_rub || 0)) }}₽</span>
                        </div>
                        <span class="route-arrow">{{ expandedRoutes[key] ? '▼' : '▶' }}</span>
                    </div>
                </div>
                
                <!-- Детали (раскрываются) -->
                <div v-show="expandedRoutes[key]" class="route-expanded">
                    <!-- Сводка (вверху) -->
                    <div class="route-summary">
                        <div class="summary-item">
                            <span>СЕБЕСТОИМОСТЬ 1 ШТ</span>
                            <strong>{{ formatPrice(route.cost_per_unit_rub || 0) }}₽</strong>
                        </div>
                        <div class="summary-item">
                            <span>ЦЕНА ПРОДАЖИ 1 ШТ</span>
                            <strong>{{ formatPrice(route.sale_per_unit_rub || 0) }}₽</strong>
                        </div>
                        <div class="summary-item">
                            <span>ПРИБЫЛЬ 1 ШТ</span>
                            <strong>{{ formatPrice((route.sale_per_unit_rub || 0) - (route.cost_per_unit_rub || 0)) }}₽</strong>
                        </div>
                    </div>
                
                <!-- Структура затрат (за 1 шт) -->
                <div class="cost-breakdown">
                    <h4 style="font-size: 14px; font-weight: 600; margin-bottom: 12px;">Структура затрат (за 1 шт)</h4>
                    
                    <!-- Стоимость в Китае -->
                    <div class="cost-section">
                        <div class="cost-section-header">
                            <strong>Стоимость в Китае</strong>
                            <strong>{{ formatPrice(route.china_cost_per_unit_rub) }}₽ ({{ route.china_cost_percentage }}%)</strong>
                        </div>
                        <div class="cost-item">
                            <span>Цена в юанях</span>
                            <span>{{ route.price_yuan_display || result.price_yuan }}¥</span>
                            <span>{{ formatPrice(route.price_rub_per_unit) }}₽</span>
                        </div>
                        <div class="cost-item">
                            <span>Пошлина за выкуп (5%)</span>
                            <span></span>
                            <span>{{ formatPrice(route.sourcing_fee_per_unit) }}₽</span>
                        </div>
                        <div class="cost-item">
                            <span>Локальная доставка</span>
                            <span></span>
                            <span>{{ formatPrice(route.local_delivery_per_unit) }}₽</span>
                        </div>
                    </div>
                    
                    <!-- Логистика -->
                    <div class="cost-section">
                        <div class="cost-section-header">
                            <strong>Логистика</strong>
                            <strong>{{ formatPrice(route.logistics_per_unit_rub) }}₽ ({{ route.logistics_percentage }}%)</strong>
                        </div>
                        <div class="cost-item">
                            <span>Доставка {{ route.logistics_type_display || key }}</span>
                            <span>{{ route.weight_display || '' }}</span>
                            <span>{{ formatPrice(route.delivery_cost_per_unit) }}₽</span>
                        </div>
                        <div class="cost-item">
                            <span>Пошлины</span>
                            <span>{{ route.duty_rate_display || '9.6%' }}</span>
                            <span>{{ formatPrice(route.duty_per_unit) }}₽</span>
                        </div>
                        <div class="cost-item">
                            <span>НДС</span>
                            <span>{{ route.vat_rate_display || '20%' }}</span>
                            <span>{{ formatPrice(route.vat_per_unit) }}₽</span>
                        </div>
                    </div>
                    
                    <!-- Прочие расходы -->
                    <div class="cost-section">
                        <div class="cost-section-header">
                            <strong>Прочие расходы</strong>
                            <strong>{{ formatPrice(route.other_costs_per_unit) }}₽ ({{ route.other_costs_percentage }}%)</strong>
                        </div>
                        <div class="cost-item">
                            <span>Забор МСК</span>
                            <span></span>
                            <span>{{ formatPrice(route.moscow_pickup_per_unit) }}₽</span>
                        </div>
                        <div class="cost-item">
                            <span>Прочие (2.5%)</span>
                            <span></span>
                            <span>{{ formatPrice(route.misc_costs_per_unit) }}₽</span>
                        </div>
                        <div class="cost-item">
                            <span>Фиксированные расходы</span>
                            <span></span>
                            <span>{{ formatPrice(route.fixed_costs_per_unit) }}₽</span>
                        </div>
                    </div>
                </div>
                
                    <!-- Итоги (внизу) -->
                    <div class="route-totals">
                        <div class="total-row">
                            <span>ОБЩАЯ СЕБЕСТОИМОСТЬ</span>
                            <strong>{{ formatPrice(route.cost_rub || 0) }}₽</strong>
                        </div>
                        <div class="total-row">
                            <span>ЦЕНА ПРОДАЖИ</span>
                            <strong>{{ formatPrice(route.sale_rub || 0) }}₽</strong>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Кнопки действий -->
            <div class="form-actions" style="margin-top: 24px;">
                <button @click="saveCalculation" class="btn-secondary">Сохранить расчёт</button>
                <button @click="saveAsPosition" class="btn-secondary">Сохранить в Позиции</button>
            </div>
        </div>
    </div>
    `,
    
    data() {
        return {
            // Основные поля
            productName: '',
            category: '',
            factoryUrl: '',
            priceYuan: 0,
            quantity: 1000,
            markup: 1.7,
            
            // Режим расчёта
            detailedMode: false,
            
            // Вес (быстрый режим)
            weightKg: 0.2,
            
            // Паккинг (детальный режим)
            packingUnitsPerBox: 0,
            packingBoxWeight: 0,
            packingBoxLength: 0,
            packingBoxWidth: 0,
            packingBoxHeight: 0,
            
            // Состояние
            isCalculating: false,
            result: null,
            expandedRoutes: {}, // Отслеживание развернутых маршрутов
            availableCategories: [],
            
            // Второй этап (кастомные параметры)
            needsCustomParams: false,
            placeholderRoutes: {},
            lastRequestData: null // Сохраняем данные первого запроса
        };
    },
    
    props: {
        position: {
            type: Object,
            default: null
        }
    },
    
    watch: {
        position: {
            immediate: true,
            handler(newPosition) {
                if (newPosition) {
                    console.log('📥 Получена позиция для расчета:', newPosition);
                    this.fillFromPosition(newPosition);
                    // Автоматически запускаем расчет через 100мс
                    setTimeout(() => {
                        this.calculate();
                    }, 100);
                }
            }
        }
    },
    
    async mounted() {
        await this.loadCategories();
    },
    
    
    methods: {
        async loadCategories() {
            try {
                const response = await axios.get(`${window.location.origin}/api/v3/categories`);
                const data = response.data;
                this.availableCategories = data.categories.map(c => c.category || c.name || c);
                console.log('✅ Загружено категорий:', this.availableCategories.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        fillFromPosition(position) {
            // Заполняем поля из позиции
            this.productName = position.name || '';
            this.category = position.category || '';
            this.factoryUrl = position.factory_url || '';
            this.priceYuan = position.price_yuan || 0;
            
            // Если есть паккинг - используем детальный режим
            if (position.packing_units_per_box && position.packing_box_weight) {
                this.detailedMode = true;
                this.packingUnitsPerBox = position.packing_units_per_box;
                this.packingBoxWeight = position.packing_box_weight;
                this.packingBoxLength = position.packing_box_length || 0;
                this.packingBoxWidth = position.packing_box_width || 0;
                this.packingBoxHeight = position.packing_box_height || 0;
            } else if (position.weight_kg) {
                // Иначе используем простой режим
                this.detailedMode = false;
                this.weightKg = position.weight_kg;
            }
            
            console.log('✅ Форма заполнена из позиции');
        },
        
        detectCategory() {
            if (!this.productName || this.productName.length < 2) return;
            
            const nameLower = this.productName.toLowerCase();
            const detected = this.availableCategories.find(cat => 
                nameLower.includes(cat.toLowerCase())
            );
            
            if (detected && detected !== this.category) {
                this.category = detected;
                console.log('✅ Автоопределена категория:', detected);
            }
        },
        
        async calculate() {
            this.isCalculating = true;
            this.result = null;
            this.needsCustomParams = false;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Подготавливаем данные для API
                const requestData = {
                    product_name: this.productName,
                    product_url: this.factoryUrl || '',
                    price_yuan: this.priceYuan,
                    quantity: this.quantity,
                    markup: this.markup,
                    forced_category: this.category || undefined,
                    is_precise_calculation: this.detailedMode
                };
                
                // Добавляем данные упаковки или веса
                if (this.detailedMode) {
                    requestData.packing_units_per_box = this.packingUnitsPerBox;
                    requestData.packing_box_weight = this.packingBoxWeight;
                    requestData.packing_box_length = this.packingBoxLength;
                    requestData.packing_box_width = this.packingBoxWidth;
                    requestData.packing_box_height = this.packingBoxHeight;
                } else {
                    requestData.weight_kg = this.weightKg;
                }
                
                // Сохраняем данные для второго этапа
                this.lastRequestData = requestData;
                
                console.log('📤 Отправка данных на расчет:', requestData);
                
                // Выполняем расчёт
                const result = await v3.calculate(requestData);
                
                // Проверяем нужны ли кастомные параметры
                if (result.needs_custom_params) {
                    console.log('⚠️ Требуются кастомные параметры');
                    this.needsCustomParams = true;
                    this.placeholderRoutes = result.routes || {};
                    this.category = result.category;
                } else {
                    this.result = result;
                    console.log('✅ Результат расчёта:', result);
                }
                
            } catch (error) {
                console.error('❌ Ошибка расчёта:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось выполнить расчёт';
                alert(`Ошибка: ${errorMsg}`);
            } finally {
                this.isCalculating = false;
            }
        },
        
        async applyCustomLogistics(customLogistics) {
            this.isCalculating = true;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Добавляем кастомные параметры к исходному запросу
                const requestData = {
                    ...this.lastRequestData,
                    custom_logistics: customLogistics
                };
                
                console.log('📤 Повторный расчет с кастомными параметрами:', requestData);
                
                // Выполняем расчёт с кастомными параметрами
                const result = await v3.calculate(requestData);
                
                // Скрываем форму кастомных параметров и показываем результат
                this.needsCustomParams = false;
                this.result = result;
                
                console.log('✅ Результат с кастомными параметрами:', result);
                
            } catch (error) {
                console.error('❌ Ошибка расчёта с кастомными параметрами:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось выполнить расчёт';
                alert(`Ошибка: ${errorMsg}`);
            } finally {
                this.isCalculating = false;
            }
        },
        
        cancelCustomParams() {
            this.needsCustomParams = false;
            this.placeholderRoutes = {};
        },
        
        reset() {
            this.result = null;
            this.productName = '';
            this.factoryUrl = '';
            this.priceYuan = 0;
            this.quantity = 1000;
            this.weightKg = 0.2;
            this.markup = 1.7;
            this.expandedRoutes = {};
        },
        
        toggleRoute(key) {
            // Vue 3 не требует $set, просто изменяем напрямую
            this.expandedRoutes[key] = !this.expandedRoutes[key];
        },
        
        formatRouteName(key) {
            const names = {
                highway_rail: 'ЖД',
                highway_air: 'Авиа',
                highway_contract: 'Контракт',
                prologix: 'Prologix',
                sea_container: 'Море'
            };
            return names[key] || key;
        },
        
        formatPrice(price) {
            if (price === null || price === undefined || isNaN(price)) return '0';
            return Number(price).toLocaleString('ru-RU', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            });
        }
    }
};


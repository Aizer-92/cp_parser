// CalculationResultsV3.js - Детальный экран с итогами расчета и маршрутами
window.CalculationResultsV3 = {
    props: {
        result: {
            type: Object,
            default: null
        },
        initialRequestData: {
            type: Object,
            default: null
        }
    },
    
    data() {
        return {
            expandedRoutes: {},
            needsCustomParams: false,
            lastRequestData: null,
            showQuickEdit: false,  // Показывать модалку быстрого редактирования
            showCategoryChange: false  // ✅ NEW: Показывать модалку изменения категории
        };
    },
    
    computed: {
        sortedRoutes() {
            if (!this.result?.routes) return [];
            return Object.entries(this.result.routes).map(([key, data]) => ({
                key,
                ...data
            })).sort((a, b) => (a.per_unit || 0) - (b.per_unit || 0));
        }
    },
    
    methods: {
        formatPrice(value) {
            if (value === null || value === undefined) return '0';
            return Number(value).toFixed(2);
        },
        
        toggleRoute(routeKey) {
            this.expandedRoutes[routeKey] = !this.expandedRoutes[routeKey];
        },
        
        // ✅ NEW: Обработчик обновления маршрута из RouteEditorV3
        async handleUpdateRoute(data) {
            console.log('🔄 Пересчет маршрута:', data);
            
            try {
                // Пересчет с кастомными параметрами через PUT API
                const response = await axios.put(
                    `/api/v3/calculations/${this.result.calculation_id}`,
                    {
                        custom_logistics: data.customLogistics
                    }
                );
                
                console.log('✅ Пересчет маршрута выполнен');
                
                // Обновить результаты
                this.$emit('recalculate', response.data);
                
            } catch (error) {
                console.error('❌ Ошибка пересчета маршрута:', error);
                alert('Ошибка пересчета: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        // ✅ NEW: Открыть модалку быстрого редактирования
        openQuickEdit() {
            console.log('⚡ Открытие быстрого редактирования');
            this.showQuickEdit = true;
        },
        
        closeQuickEdit() {
            this.showQuickEdit = false;
        },
        
        handleQuickEditRecalculated(newResult) {
            console.log('✅ Результаты быстрого редактирования получены');
            this.$emit('recalculate', newResult);
        },
        
        // ✅ NEW: Открыть модалку изменения категории
        openCategoryChange() {
            console.log('🏷 Открытие изменения категории');
            this.showCategoryChange = true;
        },
        
        closeCategoryChange() {
            this.showCategoryChange = false;
        },
        
        handleCategoryChangeRecalculated(newResult) {
            console.log('✅ Результаты изменения категории получены');
            this.$emit('recalculate', newResult);
        },
        
        openCustomParams() {
            console.log('🔧 Открытие формы редактирования ставок');
            this.needsCustomParams = true;
            this.lastRequestData = this.initialRequestData;
        },
        
        async applyCustomLogistics(customLogistics) {
            try {
                const v3 = window.useCalculationV3();
                
                const requestData = {
                    ...this.lastRequestData,
                    custom_logistics: customLogistics
                };
                
                console.log('📤 Повторный расчет с кастомными параметрами:', requestData);
                
                const newResult = await v3.calculate(requestData);
                
                this.needsCustomParams = false;
                this.$emit('recalculate', newResult);
                
                console.log('✅ Результат с кастомными параметрами:', newResult);
                
            } catch (error) {
                console.error('❌ Ошибка расчёта с кастомными параметрами:', error);
                alert('Ошибка: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        cancelCustomParams() {
            this.needsCustomParams = false;
        },
        
        newCalculation() {
            this.$emit('new-calculation');
        }
    },
    
    template: `
    <div class="calculation-results">
        <!-- Модалка быстрого редактирования -->
        <QuickEditModalV3
            v-if="showQuickEdit && result && result.calculation_id"
            :calculation-id="result.calculation_id"
            :initial-quantity="result.quantity"
            :initial-markup="result.markup"
            @close="closeQuickEdit"
            @recalculated="handleQuickEditRecalculated"
        />
        
        <!-- Модалка изменения категории -->
        <CategoryChangeModalV3
            v-if="showCategoryChange && result && result.calculation_id"
            :calculation-id="result.calculation_id"
            :current-category="result.category"
            :product-name="result.product_name || result.name || 'Товар'"
            @close="closeCategoryChange"
            @recalculated="handleCategoryChangeRecalculated"
        />
        
        <!-- Пустое состояние (нет результатов) -->
        <div v-if="!result" class="card">
            <div class="empty-state" style="padding: 60px 20px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                <h3 style="font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 8px;">
                    Нет результатов расчета
                </h3>
                <p style="color: #6b7280; margin-bottom: 24px;">
                    Выполните расчет в разделе "Быстрый расчёт" или создайте позицию
                </p>
                <button @click="newCalculation" class="btn-primary">
                    Перейти к расчету
                </button>
            </div>
        </div>
        
        <!-- Форма кастомных параметров -->
        <CustomLogisticsFormV3
            v-else-if="needsCustomParams"
            :category="result.category"
            :routes="result.routes || {}"
            @apply="applyCustomLogistics"
            @cancel="cancelCustomParams"
        />
        
        <!-- Результаты -->
        <div v-else class="card">
            <!-- Заголовок с действиями -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 class="card-title">Результаты расчёта</h2>
                <div style="display: flex; gap: 12px;">
                    <button @click="openQuickEdit" class="btn-secondary">
                        Быстрое редактирование
                    </button>
                    <button @click="newCalculation" class="btn-text">
                        Новый расчёт
                    </button>
                </div>
            </div>
            
            <!-- Информация о товаре -->
            <div class="result-summary">
                <div class="summary-row">
                    <span>Товар:</span>
                    <strong>{{ result.product_name || '—' }}</strong>
                </div>
                <div class="summary-row">
                    <span>Категория:</span>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <strong>{{ result.category || '—' }}</strong>
                        <button
                            v-if="result.calculation_id"
                            @click="openCategoryChange"
                            class="btn-icon"
                            title="Изменить категорию"
                            style="font-size: 12px;"
                        >
                            ✏
                        </button>
                    </div>
                </div>
                <div class="summary-row">
                    <span>Количество:</span>
                    <strong>{{ result.quantity || 0 }} шт</strong>
                </div>
                <div class="summary-row">
                    <span>Цена за единицу:</span>
                    <strong>{{ formatPrice(result.price_yuan) }} ¥</strong>
                </div>
                <div class="summary-row">
                    <span>Наценка:</span>
                    <strong>×{{ result.markup || 1.7 }}</strong>
                </div>
            </div>
            
            <!-- Маршруты с редакторами -->
            <div style="margin-top: 24px;">
                <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #111827;">
                    Варианты доставки ({{ sortedRoutes.length }})
                </h3>
                
                <!-- ✅ NEW: Используем RouteEditorV3 для каждого маршрута -->
                <div v-for="route in sortedRoutes" :key="route.key" style="margin-bottom: 16px;">
                    <RouteEditorV3
                        :route-key="route.key"
                        :route="route"
                        :calculation-id="result.calculation_id"
                        :category="result.category"
                        @update-route="handleUpdateRoute"
                    />
                </div>
                
                <!-- СТАРАЯ ВЕРСИЯ (закомментирована для reference) -->
                <!--
                <div v-for="route in sortedRoutes" :key="route.key" class="route-card">
                    <!-- Заголовок маршрута (кликабельный) -->
                    <div @click="toggleRoute(route.key)" class="route-header">
                        <div>
                            <h4 class="route-name">{{ route.name || route.key }}</h4>
                            <div class="route-delivery-time">
                                {{ route.delivery_time || '—' }}
                            </div>
                        </div>
                        
                        <!-- Быстрая информация -->
                        <div class="route-quick-info">
                            <div class="route-prices">
                                <div class="route-label">Себестоимость</div>
                                <div class="route-value">{{ formatPrice(route.cost_per_unit_rub || route.per_unit) }} ₽</div>
                            </div>
                            <div class="route-divider"></div>
                            <div class="route-prices">
                                <div class="route-label">Продажа</div>
                                <div class="route-value">{{ formatPrice(route.sale_per_unit_rub || (route.sale_rub / result.quantity)) }} ₽</div>
                            </div>
                            <div class="route-divider"></div>
                            <div class="route-prices">
                                <div class="route-label">Прибыль</div>
                                <div class="route-value">{{ formatPrice((route.sale_per_unit_rub || (route.sale_rub / result.quantity)) - (route.cost_per_unit_rub || route.per_unit)) }} ₽</div>
                            </div>
                            <div class="route-arrow" :class="{ 'route-expanded': expandedRoutes[route.key] }">
                                ▼
                            </div>
                        </div>
                    </div>
                    
                    <!-- Детальная разбивка (раскрывается) -->
                    <div v-if="expandedRoutes[route.key]" class="route-details">
                        <!-- Итоговые цены -->
                        <div class="route-totals">
                            <div class="total-row">
                                <span>На весь тираж ({{ result.quantity }} шт):</span>
                                <div style="display: flex; gap: 16px;">
                                    <div>
                                        <span style="color: #6b7280;">Себестоимость:</span>
                                        <strong>{{ formatPrice(route.cost_rub || (route.per_unit * result.quantity)) }} ₽</strong>
                                    </div>
                                    <div>
                                        <span style="color: #6b7280;">Продажа:</span>
                                        <strong>{{ formatPrice(route.sale_rub) }} ₽</strong>
                                    </div>
                                    <div>
                                        <span style="color: #6b7280;">Прибыль:</span>
                                        <strong style="color: #059669;">{{ formatPrice(route.profit_rub) }} ₽</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Структура затрат -->
                        <div class="cost-breakdown">
                            <h5 style="font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #111827;">
                                Структура затрат (на единицу)
                            </h5>
                            
                            <!-- Оплата в Китае -->
                            <div class="cost-section">
                                <div class="cost-section-header">
                                    <span>Оплата в Китае</span>
                                    <span>
                                        {{ formatPrice(route.china_cost_per_unit_rub || 0) }} ₽
                                        <span style="color: #6b7280; font-size: 13px;">({{ route.china_cost_percentage || 0 }}%)</span>
                                    </span>
                                </div>
                                <div class="cost-item">
                                    <span>Цена товара</span>
                                    <span>{{ formatPrice(route.price_rub_per_unit || 0) }} ₽</span>
                                </div>
                                <div class="cost-item">
                                    <span>Комиссия за выкуп</span>
                                    <span>{{ formatPrice(route.sourcing_fee_per_unit || 0) }} ₽</span>
                                </div>
                                <div class="cost-item">
                                    <span>Доставка внутри Китая</span>
                                    <span>{{ formatPrice(route.local_delivery_per_unit || 0) }} ₽</span>
                                </div>
                            </div>
                            
                            <!-- Логистика -->
                            <div class="cost-section">
                                <div class="cost-section-header">
                                    <span>Логистика</span>
                                    <span>
                                        {{ formatPrice(route.logistics_per_unit_rub || 0) }} ₽
                                        <span style="color: #6b7280; font-size: 13px;">({{ route.logistics_percentage || 0 }}%)</span>
                                    </span>
                                </div>
                                <div class="cost-item">
                                    <span>Доставка {{ route.logistics_type_display || '' }}</span>
                                    <span>{{ route.weight_display || '—' }}</span>
                                </div>
                            </div>
                            
                            <!-- Таможня -->
                            <div class="cost-section">
                                <div class="cost-section-header">
                                    <span>Таможня</span>
                                    <span>
                                        {{ formatPrice((route.duty_per_unit || 0) + (route.vat_per_unit || 0)) }} ₽
                                    </span>
                                </div>
                                <div class="cost-item">
                                    <span>Пошлины</span>
                                    <span>{{ route.duty_rate_display || '9.6%' }}</span>
                                    <span>{{ formatPrice(route.duty_per_unit || 0) }} ₽</span>
                                </div>
                                <div class="cost-item">
                                    <span>НДС</span>
                                    <span>{{ route.vat_rate_display || '20%' }}</span>
                                    <span>{{ formatPrice(route.vat_per_unit || 0) }} ₽</span>
                                </div>
                            </div>
                            
                            <!-- Прочие расходы -->
                            <div class="cost-section">
                                <div class="cost-section-header">
                                    <span>Прочие расходы</span>
                                    <span>
                                        {{ formatPrice(route.other_costs_per_unit || 0) }} ₽
                                        <span style="color: #6b7280; font-size: 13px;">({{ route.other_costs_percentage || 0 }}%)</span>
                                    </span>
                                </div>
                                <div class="cost-item">
                                    <span>Доставка по Москве</span>
                                    <span>{{ formatPrice(route.moscow_pickup_per_unit || 0) }} ₽</span>
                                </div>
                                <div class="cost-item">
                                    <span>Переменные расходы (2.5%)</span>
                                    <span>{{ formatPrice(route.misc_costs_per_unit || 0) }} ₽</span>
                                </div>
                                <div class="cost-item">
                                    <span>Фиксированные расходы</span>
                                    <span>{{ formatPrice(route.fixed_costs_per_unit || 0) }} ₽</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                -->
                
                <!-- Пустое состояние -->
                <div v-if="sortedRoutes.length === 0" class="empty-state">
                    Маршруты не найдены
                </div>
            </div>
        </div>
    </div>
    `
};



// QuickModeV3.js - Быстрый режим расчёта (без создания позиций)
window.QuickModeV3 = {
    template: `
    <div class="quick-mode">
        <!-- Форма ввода -->
        <div class="card">
            <h2 class="card-title">Быстрый расчёт</h2>
            
            <form @submit.prevent="calculate" class="form">
                <!-- Товар -->
                <div class="form-group">
                    <label for="product-name">Товар</label>
                    <input
                        id="product-name"
                        v-model="form.product_name"
                        type="text"
                        placeholder="Например: Футболка хлопковая"
                        required
                        class="form-input"
                    />
                </div>
                
                <!-- Категория -->
                <div class="form-group">
                    <label for="category">Категория</label>
                    <input
                        id="category"
                        v-model="form.category"
                        type="text"
                        list="categories-list"
                        placeholder="Автоопределяется"
                        class="form-input"
                        @input="onCategoryInput"
                    />
                    <datalist id="categories-list">
                        <option v-for="cat in filteredCategories" :key="cat" :value="cat">
                    </datalist>
                </div>
                
                <!-- Параметры в одну строку -->
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label for="price">Цена (¥)</label>
                        <input
                            id="price"
                            v-model.number="form.price_yuan"
                            type="number"
                            step="0.01"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="quantity">Кол-во</label>
                        <input
                            id="quantity"
                            v-model.number="form.quantity"
                            type="number"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="weight">Вес (кг)</label>
                        <input
                            id="weight"
                            v-model.number="form.weight_kg"
                            type="number"
                            step="0.01"
                            required
                            class="form-input"
                        />
                    </div>
                </div>
                
                <!-- Наценка и фабрика -->
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label for="markup">Наценка</label>
                        <input
                            id="markup"
                            v-model.number="form.markup"
                            type="number"
                            step="0.1"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group flex-2">
                        <label for="factory">Фабрика/WeChat (опционально)</label>
                        <div class="input-with-button">
                            <input
                                id="factory"
                                v-model="form.product_url"
                                type="text"
                                placeholder="https://wechat.com/..."
                                class="form-input"
                            />
                            <button
                                type="button"
                                @click="selectFactory"
                                class="btn-secondary btn-sm"
                                title="Выбрать из списка"
                            >
                                Из списка
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Кнопки -->
                <div class="form-actions">
                    <button
                        type="submit"
                        :disabled="isCalculating"
                        class="btn-primary"
                    >
                        {{ isCalculating ? 'Расчёт...' : 'Рассчитать' }}
                    </button>
                    
                    <button
                        v-if="result"
                        type="button"
                        @click="saveAsPosition"
                        class="btn-secondary"
                    >
                        Сохранить в Позиции
                    </button>
                </div>
            </form>
        </div>
        
        <!-- Результаты -->
        <div v-if="result" class="results">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Результаты</h2>
                    <button @click="reset" class="btn-text">Новый расчёт</button>
                </div>
                
                <!-- Маршруты -->
                <div class="routes-list">
                    <div
                        v-for="(route, key) in result.routes"
                        :key="key"
                        class="route-card"
                        :class="{ 'route-best': isBestRoute(key) }"
                    >
                        <div class="route-header">
                            <h3 class="route-name">{{ formatRouteName(key) }}</h3>
                            <span v-if="isBestRoute(key)" class="badge-best">ЛУЧШИЙ</span>
                        </div>
                        
                        <div class="route-prices">
                            <div class="price-row">
                                <span class="price-label">Себестоимость:</span>
                                <span class="price-value">{{ formatPrice(route.cost_per_unit_rub) }} ₽</span>
                            </div>
                            <div class="price-row">
                                <span class="price-label">Продажа:</span>
                                <span class="price-value primary">{{ formatPrice(route.sale_per_unit_rub) }} ₽</span>
                            </div>
                            <div class="price-row">
                                <span class="price-label">Прибыль:</span>
                                <span class="price-value success">{{ formatPrice(route.profit_rub) }} ₽</span>
                            </div>
                        </div>
                        
                        <div class="route-total">
                            Всего: {{ formatPrice(route.cost_price_rub) }} ₽ → {{ formatPrice(route.sale_price_rub) }} ₽
                        </div>
                        
                        <div class="route-actions">
                            <button @click="showRouteDetails(key)" class="btn-text">Детали</button>
                            <button @click="editRoute(key)" class="btn-text">Кастомная ставка</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Модалка с деталями маршрута -->
        <div v-if="selectedRoute" class="modal" @click.self="selectedRoute = null">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>{{ formatRouteName(selectedRoute) }}</h3>
                    <button @click="selectedRoute = null" class="btn-close">×</button>
                </div>
                <div class="modal-body">
                    <pre>{{ JSON.stringify(result.routes[selectedRoute], null, 2) }}</pre>
                </div>
            </div>
        </div>
    </div>
    `,
    
    data() {
        return {
            form: {
                product_name: '',
                category: '',
                price_yuan: 0,
                quantity: 1000,
                weight_kg: 0,
                markup: 1.7,
                product_url: '',
                is_precise_calculation: false
            },
            
            availableCategories: [],
            filteredCategories: [],
            
            isCalculating: false,
            result: null,
            selectedRoute: null
        };
    },
    
    async mounted() {
        await this.loadCategories();
    },
    
    methods: {
        async loadCategories() {
            try {
                const v3 = window.useCalculationV3();
                const categories = await v3.getCategories();
                this.availableCategories = categories.map(c => c.category || c.name || c);
            } catch (error) {
                console.error('Ошибка загрузки категорий:', error);
            }
        },
        
        onCategoryInput() {
            const query = this.form.category.toLowerCase();
            this.filteredCategories = this.availableCategories
                .filter(cat => cat.toLowerCase().includes(query))
                .slice(0, 10);
        },
        
        async calculate() {
            this.isCalculating = true;
            this.result = null;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Подготавливаем данные
                const requestData = {
                    ...this.form,
                    forced_category: this.form.category || undefined
                };
                
                // Выполняем расчёт
                const result = await v3.calculate(requestData);
                this.result = result;
                
            } catch (error) {
                console.error('Ошибка расчёта:', error);
                alert(`Ошибка: ${error.message || 'Не удалось выполнить расчёт'}`);
            } finally {
                this.isCalculating = false;
            }
        },
        
        reset() {
            this.result = null;
            this.form.product_name = '';
            this.form.category = '';
        },
        
        selectFactory() {
            // TODO: Открыть модалку выбора фабрики
            alert('Функция выбора фабрики будет реализована в следующем этапе');
        },
        
        saveAsPosition() {
            // TODO: Создать позицию и перейти к ней
            this.$emit('save-as-position', {
                form: this.form,
                result: this.result
            });
        },
        
        showRouteDetails(routeKey) {
            this.selectedRoute = routeKey;
        },
        
        editRoute(routeKey) {
            // TODO: Открыть редактор кастомных ставок
            alert(`Редактирование ${routeKey} будет реализовано позже`);
        },
        
        isBestRoute(routeKey) {
            if (!this.result || !this.result.routes) return false;
            
            const routes = Object.values(this.result.routes);
            const currentRoute = this.result.routes[routeKey];
            
            if (!currentRoute || !currentRoute.profit_rub) return false;
            
            const maxProfit = Math.max(...routes.map(r => r.profit_rub || 0));
            return currentRoute.profit_rub === maxProfit;
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


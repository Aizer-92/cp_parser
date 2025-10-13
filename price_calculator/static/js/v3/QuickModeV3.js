// QuickModeV3.js - Быстрый режим расчёта (без создания позиций)
window.QuickModeV3 = {
    template: `
    <div class="quick-mode">
        <!-- Форма ввода -->
        <div class="card">
            <h2 class="card-title">Данные товара</h2>
            
            <form @submit.prevent="calculate" class="form">
                <!-- Название товара -->
                <div class="form-group">
                    <label for="product-name">Название товара *</label>
                    <input
                        id="product-name"
                        v-model="form.product_name"
                        type="text"
                        placeholder="Например: Футболка хлопковая"
                        required
                        class="form-input"
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
                        v-model="form.category"
                        type="text"
                        list="categories-list"
                        placeholder="Определится автоматически"
                        class="form-input"
                        readonly
                        style="background: #f9fafb; cursor: not-allowed;"
                    />
                    <datalist id="categories-list">
                        <option v-for="cat in availableCategories" :key="cat" :value="cat">
                    </datalist>
                </div>
                
                <!-- WeChat/URL -->
                <div class="form-group">
                    <label for="factory">WeChat / Ссылка на товар</label>
                    <div class="input-with-button">
                        <input
                            id="factory"
                            v-model="form.product_url"
                            type="text"
                            placeholder="https://... или WeChat ID"
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
                
                <!-- Цена, количество, наценка -->
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label for="price">Цена за ед. (¥) *</label>
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
                        <label for="quantity">Количество (шт) *</label>
                        <input
                            id="quantity"
                            v-model.number="form.quantity"
                            type="number"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="markup">Наценка *</label>
                        <input
                            id="markup"
                            v-model.number="form.markup"
                            type="number"
                            step="0.1"
                            required
                            class="form-input"
                        />
                    </div>
                </div>
                
                <!-- Переключатель режимов упаковки -->
                <div class="mode-toggle">
                    <label class="toggle-label">
                        <input
                            type="radio"
                            :value="false"
                            v-model="detailedMode"
                            class="toggle-radio"
                        />
                        <span>Быстрый расчёт (по весу)</span>
                    </label>
                    <label class="toggle-label">
                        <input
                            type="radio"
                            :value="true"
                            v-model="detailedMode"
                            class="toggle-radio"
                        />
                        <span>Детальный расчёт (упаковка)</span>
                    </label>
                </div>
                
                <!-- Вес (быстрый режим, по умолчанию) -->
                <div v-if="!detailedMode" class="weight-section">
                    <div class="form-group">
                        <label for="weight">Вес 1 единицы (кг) *</label>
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
                
                <!-- Паккинг (детальный режим) -->
                <div v-else class="packing-section">
                    <h3 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">Упаковка *</h3>
                    
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="units-per-box">Штук в коробке</label>
                            <input
                                id="units-per-box"
                                v-model.number="form.packing_units_per_box"
                                type="number"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="box-weight">Вес коробки (кг)</label>
                            <input
                                id="box-weight"
                                v-model.number="form.packing_box_weight"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="box-length">Длина (м)</label>
                            <input
                                id="box-length"
                                v-model.number="form.packing_box_length"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="box-width">Ширина (м)</label>
                            <input
                                id="box-width"
                                v-model.number="form.packing_box_width"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="box-height">Высота (м)</label>
                            <input
                                id="box-height"
                                v-model.number="form.packing_box_height"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                    </div>
                    
                    <!-- Расчётные значения -->
                    <div v-if="calculatedWeightPerUnit" class="calculated-values">
                        <div class="calc-item">
                            <span class="calc-label">Вес 1 шт:</span>
                            <span class="calc-value">{{ calculatedWeightPerUnit }} кг</span>
                        </div>
                        <div class="calc-item">
                            <span class="calc-label">Объём коробки:</span>
                            <span class="calc-value">{{ calculatedBoxVolume }} м³</span>
                        </div>
                        <div v-if="calculatedDensity" class="calc-item">
                            <span class="calc-label">Плотность:</span>
                            <span class="calc-value">{{ calculatedDensity }} кг/м³</span>
                        </div>
                    </div>
                    
                    <!-- Дополнительные поля детального режима -->
                    <h3 style="font-size: 15px; font-weight: 600; margin: 16px 0 12px;">Дополнительная информация</h3>
                    
                    <!-- Фотографии -->
                    <div class="form-group">
                        <label>Фотографии товара</label>
                        <div class="photo-dropzone" @click="$refs.photoInput.click()" @drop.prevent="handlePhotoDrop" @dragover.prevent>
                            <input
                                ref="photoInput"
                                type="file"
                                accept="image/*"
                                multiple
                                style="display: none;"
                                @change="handlePhotoSelect"
                            />
                            <div v-if="photos.length === 0" class="dropzone-placeholder">
                                <span>Перетащите фото сюда или нажмите для выбора</span>
                            </div>
                            <div v-else class="photos-preview">
                                <div v-for="(photo, index) in photos" :key="index" class="photo-item">
                                    <img :src="photo.preview" :alt="photo.name" />
                                    <span v-if="index === 0" class="main-badge">основная</span>
                                    <button type="button" @click.stop="removePhoto(index)" class="remove-photo">×</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Кастомизация -->
                    <div class="form-group">
                        <label for="customization">Кастомизация товара</label>
                        <textarea
                            id="customization"
                            v-model="form.customization"
                            rows="3"
                            placeholder="Опишите требования к кастомизации (печать, гравировка и т.д.)"
                            class="form-input"
                        ></textarea>
                    </div>
                    
                    <!-- Сроки и цены -->
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="production-time">Срок производства (дни)</label>
                            <input
                                id="production-time"
                                v-model.number="form.production_time_days"
                                type="number"
                                min="0"
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="sample-time">Срок образца (дни)</label>
                            <input
                                id="sample-time"
                                v-model.number="form.sample_time_days"
                                type="number"
                                min="0"
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="sample-price">Цена образца (¥)</label>
                            <input
                                id="sample-price"
                                v-model.number="form.sample_price_yuan"
                                type="number"
                                step="0.01"
                                min="0"
                                class="form-input"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- Кнопки -->
                <div class="form-actions">
                    <button
                        type="submit"
                        :disabled="isCalculating || !isFormValid"
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
            detailedMode: false, // false = быстрый (вес), true = детальный (паккинг)
            
            form: {
                product_name: '',
                category: '',
                price_yuan: 0,
                quantity: 1000,
                markup: 1.7,
                product_url: '',
                
                // Режим по весу (по умолчанию)
                weight_kg: 0.2,
                
                // Режим паккинга (детальный)
                packing_units_per_box: 0,
                packing_box_weight: 0,
                packing_box_length: 0,
                packing_box_width: 0,
                packing_box_height: 0,
                
                // Дополнительные поля для детального режима
                customization: '',           // Кастомизация
                production_time_days: 0,     // Срок производства (дни)
                sample_time_days: 0,         // Срок образца (дни)
                sample_price_yuan: 0,        // Цена образца (¥)
                
                is_precise_calculation: false
            },
            
            // Фотографии загружаются отдельно
            photos: [],
            
            availableCategories: [],
            filteredCategories: [],
            
            isCalculating: false,
            result: null,
            selectedRoute: null
        };
    },
    
    computed: {
        calculatedWeightPerUnit() {
            if (!this.detailedMode) return null;
            
            if (!this.form.packing_units_per_box || !this.form.packing_box_weight) {
                return null;
            }
            
            return (this.form.packing_box_weight / this.form.packing_units_per_box).toFixed(4);
        },
        
        calculatedBoxVolume() {
            if (!this.detailedMode) return null;
            
            const l = this.form.packing_box_length;
            const w = this.form.packing_box_width;
            const h = this.form.packing_box_height;
            
            if (!l || !w || !h) return null;
            
            return (l * w * h).toFixed(4);
        },
        
        calculatedDensity() {
            if (!this.detailedMode) return null;
            
            const volume = this.calculatedBoxVolume;
            const weight = this.form.packing_box_weight;
            
            if (!volume || !weight) return null;
            
            return (weight / parseFloat(volume)).toFixed(1);
        },
        
        isFormValid() {
            if (!this.form.product_name || !this.form.price_yuan || !this.form.quantity) {
                return false;
            }
            
            if (this.detailedMode) {
                return this.form.packing_units_per_box > 0 &&
                       this.form.packing_box_weight > 0 &&
                       this.form.packing_box_length > 0 &&
                       this.form.packing_box_width > 0 &&
                       this.form.packing_box_height > 0;
            } else {
                return this.form.weight_kg > 0;
            }
        }
    },
    
    watch: {
        // Автоопределение категории при изменении названия товара
        'form.product_name'(newName) {
            if (newName && newName.length > 2) {
                clearTimeout(this._categoryDetectTimer);
                this._categoryDetectTimer = setTimeout(() => {
                    this.detectCategory(newName);
                }, 500);
            }
        }
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
                console.log('Загружено категорий:', this.availableCategories.length);
            } catch (error) {
                console.error('Ошибка загрузки категорий:', error);
            }
        },
        
        detectCategory(productName) {
            if (!productName || !this.availableCategories.length) return;
            
            const nameLower = productName.toLowerCase();
            
            // Ищем категорию по вхождению названия
            const detected = this.availableCategories.find(cat => 
                nameLower.includes(cat.toLowerCase())
            );
            
            if (detected && detected !== this.form.category) {
                this.form.category = detected;
                console.log('Автоопределена категория:', detected);
            } else if (!detected && !this.form.category) {
                this.form.category = 'Новая категория';
                console.log('Категория не определена, установлена "Новая категория"');
            }
        },
        
        async calculate() {
            this.isCalculating = true;
            this.result = null;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Подготавливаем данные для API
                const requestData = {
                    product_name: this.form.product_name,
                    product_url: this.form.product_url || '',
                    price_yuan: this.form.price_yuan,
                    quantity: this.form.quantity,
                    markup: this.form.markup,
                    forced_category: this.form.category || undefined,
                    is_precise_calculation: this.detailedMode
                };
                
                // Добавляем данные упаковки или веса
                if (this.detailedMode) {
                    requestData.packing_units_per_box = this.form.packing_units_per_box;
                    requestData.packing_box_weight = this.form.packing_box_weight;
                    requestData.packing_box_length = this.form.packing_box_length;
                    requestData.packing_box_width = this.form.packing_box_width;
                    requestData.packing_box_height = this.form.packing_box_height;
                } else {
                    requestData.weight_kg = this.form.weight_kg;
                }
                
                console.log('Отправка данных на расчёт:', requestData);
                
                // Выполняем расчёт
                const result = await v3.calculate(requestData);
                this.result = result;
                
                console.log('Результат расчёта:', result);
                
            } catch (error) {
                console.error('Ошибка расчёта:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось выполнить расчёт';
                alert(`Ошибка: ${errorMsg}`);
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
        },
        
        // Методы работы с фотографиями
        handlePhotoSelect(event) {
            const files = Array.from(event.target.files);
            this.addPhotos(files);
        },
        
        handlePhotoDrop(event) {
            const files = Array.from(event.dataTransfer.files).filter(f => f.type.startsWith('image/'));
            this.addPhotos(files);
        },
        
        addPhotos(files) {
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.photos.push({
                        file: file,
                        name: file.name,
                        preview: e.target.result
                    });
                };
                reader.readAsDataURL(file);
            });
        },
        
        removePhoto(index) {
            this.photos.splice(index, 1);
        }
    }
};


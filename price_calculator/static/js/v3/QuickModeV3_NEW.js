// QuickModeV3.js - Быстрый режим расчёта (Position + Calculation)
window.QuickModeV3 = {
    template: `
    <div class="quick-mode">
        <div class="card">
            <h2 class="card-title">Быстрый расчёт</h2>
            
            <form @submit.prevent="calculate" class="form">
                
                <!-- ========================================== -->
                <!-- СЕКЦИЯ 1: ТОВАР (Position)                -->
                <!-- ========================================== -->
                <div class="form-section">
                    <h3 class="section-title">📦 Товар</h3>
                    
                    <!-- Название товара -->
                    <div class="form-group">
                        <label for="product-name">Название товара *</label>
                        <input
                            id="product-name"
                            v-model="position.name"
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
                            v-model="position.category"
                            type="text"
                            list="categories-list"
                            placeholder="Определится автоматически"
                            class="form-input"
                        />
                        <datalist id="categories-list">
                            <option v-for="cat in availableCategories" :key="cat" :value="cat">
                        </datalist>
                    </div>
                    
                    <!-- Описание товара -->
                    <div class="form-group">
                        <label for="description">Описание товара</label>
                        <textarea
                            id="description"
                            v-model="position.description"
                            rows="2"
                            placeholder="Описание товара, характеристики..."
                            class="form-input"
                        ></textarea>
                    </div>
                    
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
                            <div v-if="position.photos.length === 0" class="dropzone-placeholder">
                                <span>Перетащите фото сюда или нажмите для выбора</span>
                            </div>
                            <div v-else class="photos-preview">
                                <div v-for="(photo, index) in position.photos" :key="index" class="photo-item">
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
                            v-model="position.customization"
                            rows="2"
                            placeholder="Опишите требования к кастомизации (печать, гравировка и т.д.)"
                            class="form-input"
                        ></textarea>
                    </div>
                </div>
                
                <!-- ========================================== -->
                <!-- СЕКЦИЯ 2: РАСЧЁТ (Calculation)            -->
                <!-- ========================================== -->
                <div class="form-section">
                    <h3 class="section-title">💰 Расчёт</h3>
                    
                    <!-- Фабрика -->
                    <div class="form-group">
                        <label for="factory">🏭 Фабрика (WeChat / URL)</label>
                        <div class="input-with-button">
                            <input
                                id="factory"
                                v-model="calculation.factory_url"
                                type="text"
                                placeholder="https://... или WeChat ID"
                                class="form-input"
                            />
                            <button type="button" @click="selectFactory" class="btn-secondary btn-sm">
                                Из списка
                            </button>
                        </div>
                    </div>
                    
                    <!-- Основные параметры: Цена, Количество, Срок производства -->
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="price">Цена (¥) *</label>
                            <input
                                id="price"
                                v-model.number="calculation.price_yuan"
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
                                v-model.number="calculation.quantity"
                                type="number"
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="production-time">Срок производства (дни)</label>
                            <input
                                id="production-time"
                                v-model.number="calculation.production_time_days"
                                type="number"
                                min="0"
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
                                v-model="calculation.detailedMode"
                                class="toggle-radio"
                            />
                            <span>Быстрый расчёт (по весу)</span>
                        </label>
                        <label class="toggle-label">
                            <input
                                type="radio"
                                :value="true"
                                v-model="calculation.detailedMode"
                                class="toggle-radio"
                            />
                            <span>Детальный расчёт (упаковка)</span>
                        </label>
                    </div>
                    
                    <!-- Вес (быстрый режим) -->
                    <div v-if="!calculation.detailedMode" class="weight-section">
                        <div class="form-group">
                            <label for="weight">Вес 1 единицы (кг) *</label>
                            <input
                                id="weight"
                                v-model.number="calculation.weight_kg"
                                type="number"
                                step="0.01"
                                required
                                class="form-input"
                            />
                        </div>
                    </div>
                    
                    <!-- Паккинг (детальный режим) -->
                    <div v-else class="packing-section">
                        <h4 style="font-size: 15px; font-weight: 600; margin-bottom: 12px;">📦 Упаковка *</h4>
                        
                        <div class="form-row">
                            <div class="form-group flex-1">
                                <label for="units-per-box">Штук в коробке</label>
                                <input
                                    id="units-per-box"
                                    v-model.number="calculation.packing_units_per_box"
                                    type="number"
                                    required
                                    class="form-input"
                                />
                            </div>
                            
                            <div class="form-group flex-1">
                                <label for="box-weight">Вес коробки (кг)</label>
                                <input
                                    id="box-weight"
                                    v-model.number="calculation.packing_box_weight"
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
                                    v-model.number="calculation.packing_box_length"
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
                                    v-model.number="calculation.packing_box_width"
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
                                    v-model.number="calculation.packing_box_height"
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
                    </div>
                    
                    <!-- Образец (отдельный блок) -->
                    <div class="sample-section">
                        <h4 style="font-size: 15px; font-weight: 600; margin: 16px 0 12px;">🎨 Образец</h4>
                        <div class="form-row">
                            <div class="form-group flex-1">
                                <label for="sample-time">Срок образца (дни)</label>
                                <input
                                    id="sample-time"
                                    v-model.number="calculation.sample_time_days"
                                    type="number"
                                    min="0"
                                    class="form-input"
                                />
                            </div>
                            
                            <div class="form-group flex-1">
                                <label for="sample-price">Цена образца (¥)</label>
                                <input
                                    id="sample-price"
                                    v-model.number="calculation.sample_price_yuan"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    class="form-input"
                                />
                            </div>
                        </div>
                    </div>
                    
                    <!-- Наценка (в самом конце) -->
                    <div class="markup-section">
                        <h4 style="font-size: 15px; font-weight: 600; margin: 16px 0 12px;">💵 Наценка</h4>
                        <div class="form-group">
                            <label for="markup">Наценка *</label>
                            <input
                                id="markup"
                                v-model.number="calculation.markup"
                                type="number"
                                step="0.1"
                                required
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
        
        <!-- Результаты - компактный вид -->
        <div v-if="result" class="results-compact">
            <div class="card-header">
                <h2 class="card-title">Результаты</h2>
                <button @click="reset" class="btn-text">Новый расчёт</button>
            </div>
            
            <!-- Компактный список маршрутов -->
            <div v-for="(route, key) in result.routes" :key="key" class="result-row">
                <span class="route-name">{{ formatRouteName(key) }}:</span>
                <span class="route-prices">
                    {{ formatPrice(route.cost_per_unit_rub) }}₽
                    <span class="route-arrow">→</span>
                    {{ formatPrice(route.sale_per_unit_rub) }}₽
                </span>
                <span class="route-profit" :class="{ negative: route.profit_rub < 0 }">
                    (прибыль {{ formatPrice(route.profit_rub) }}₽)
                </span>
            </div>
            
            <!-- Кнопки действий -->
            <div class="form-actions" style="margin-top: 16px;">
                <button @click="saveCalculation" class="btn-secondary">Сохранить расчёт</button>
                <button @click="saveAsPosition" class="btn-secondary">Сохранить в Позиции</button>
            </div>
        </div>
    </div>
    `,
    
    data() {
        return {
            // ПОЗИЦИЯ (Position) - ЧТО мы продаем
            position: {
                name: '',
                category: '',
                description: '',
                customization: '',
                photos: []
            },
            
            // РАСЧЁТ (Calculation) - весь расчёт от фабрики
            calculation: {
                // Фабрика
                factory_url: '',
                
                // Основной расчёт
                price_yuan: 0,
                quantity: 1000,
                production_time_days: 0,
                
                // Режим расчёта
                detailedMode: false,
                weight_kg: 0.2,
                
                // Паккинг (если детальный)
                packing_units_per_box: 0,
                packing_box_weight: 0,
                packing_box_length: 0,
                packing_box_width: 0,
                packing_box_height: 0,
                
                // Образец (отдельный блок)
                sample_time_days: 0,
                sample_price_yuan: 0,
                
                // Наценка (в конце)
                markup: 1.7
            },
            
            availableCategories: [],
            isCalculating: false,
            result: null
        };
    },
    
    computed: {
        calculatedWeightPerUnit() {
            if (!this.calculation.detailedMode) return null;
            
            if (!this.calculation.packing_units_per_box || !this.calculation.packing_box_weight) {
                return null;
            }
            
            return (this.calculation.packing_box_weight / this.calculation.packing_units_per_box).toFixed(4);
        },
        
        calculatedBoxVolume() {
            if (!this.calculation.detailedMode) return null;
            
            const l = this.calculation.packing_box_length;
            const w = this.calculation.packing_box_width;
            const h = this.calculation.packing_box_height;
            
            if (!l || !w || !h) return null;
            
            return (l * w * h).toFixed(4);
        },
        
        calculatedDensity() {
            if (!this.calculation.detailedMode) return null;
            
            const volume = this.calculatedBoxVolume;
            const weight = this.calculation.packing_box_weight;
            
            if (!volume || !weight) return null;
            
            return (weight / parseFloat(volume)).toFixed(1);
        },
        
        isFormValid() {
            // Проверка позиции
            if (!this.position.name || !this.calculation.price_yuan || !this.calculation.quantity) {
                return false;
            }
            
            // Проверка расчёта по режиму
            if (this.calculation.detailedMode) {
                return this.calculation.packing_units_per_box > 0 &&
                       this.calculation.packing_box_weight > 0 &&
                       this.calculation.packing_box_length > 0 &&
                       this.calculation.packing_box_width > 0 &&
                       this.calculation.packing_box_height > 0;
            } else {
                return this.calculation.weight_kg > 0;
            }
        }
    },
    
    watch: {
        // Автоопределение категории при изменении названия товара
        'position.name'(newName) {
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
                console.log('✅ Загружено категорий:', this.availableCategories.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        detectCategory(productName) {
            if (!productName || !this.availableCategories.length) return;
            
            const nameLower = productName.toLowerCase();
            
            // Ищем категорию по вхождению названия
            const detected = this.availableCategories.find(cat => 
                nameLower.includes(cat.toLowerCase())
            );
            
            if (detected && detected !== this.position.category) {
                this.position.category = detected;
                console.log('✅ Автоопределена категория:', detected);
            } else if (!detected && !this.position.category) {
                this.position.category = 'Новая категория';
                console.log('⚠️ Категория не определена, установлена "Новая категория"');
            }
        },
        
        async calculate() {
            this.isCalculating = true;
            this.result = null;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Подготавливаем данные для API
                const requestData = {
                    product_name: this.position.name,
                    product_url: this.calculation.factory_url || '',
                    price_yuan: this.calculation.price_yuan,
                    quantity: this.calculation.quantity,
                    markup: this.calculation.markup,
                    forced_category: this.position.category || undefined,
                    is_precise_calculation: this.calculation.detailedMode
                };
                
                // Добавляем данные упаковки или веса
                if (this.calculation.detailedMode) {
                    requestData.packing_units_per_box = this.calculation.packing_units_per_box;
                    requestData.packing_box_weight = this.calculation.packing_box_weight;
                    requestData.packing_box_length = this.calculation.packing_box_length;
                    requestData.packing_box_width = this.calculation.packing_box_width;
                    requestData.packing_box_height = this.calculation.packing_box_height;
                } else {
                    requestData.weight_kg = this.calculation.weight_kg;
                }
                
                console.log('📤 Отправка данных на расчет:', requestData);
                
                // Выполняем расчёт
                const result = await v3.calculate(requestData);
                this.result = result;
                
                console.log('✅ Результат расчёта:', result);
                
            } catch (error) {
                console.error('❌ Ошибка расчёта:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось выполнить расчёт';
                alert(`Ошибка: ${errorMsg}`);
            } finally {
                this.isCalculating = false;
            }
        },
        
        reset() {
            this.result = null;
            this.position.name = '';
            this.position.category = '';
            this.position.description = '';
            this.position.customization = '';
            this.position.photos = [];
        },
        
        selectFactory() {
            alert('Функция выбора фабрики будет реализована в следующем этапе');
        },
        
        saveCalculation() {
            alert('Функция сохранения расчёта будет реализована');
        },
        
        saveAsPosition() {
            this.$emit('save-as-position', {
                position: this.position,
                calculation: this.calculation,
                result: this.result
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
                    this.position.photos.push({
                        file: file,
                        name: file.name,
                        preview: e.target.result
                    });
                };
                reader.readAsDataURL(file);
            });
        },
        
        removePhoto(index) {
            this.position.photos.splice(index, 1);
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



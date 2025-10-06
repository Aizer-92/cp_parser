/**
 * 🧮 CALCULATION FORM COMPONENT
 * ФАЗА 2: Модульный Vue компонент формы расчетов
 */

const CalculationForm = {
    name: 'CalculationForm',
    
    props: {
        form: {
            type: Object,
            required: true
        },
        detectedCategory: {
            type: Object,
            default: null
        },
        categories: {
            type: Array,
            default: () => []
        },
        selectedCategoryIndex: {
            type: [String, Number],
            default: ""
        },
        isCalculating: {
            type: Boolean,
            default: false
        },
        isFormValid: {
            type: Boolean,
            default: false
        },
        suggestedRate: {
            type: Number,
            default: 0
        },
        editingCalculationId: {
            type: [Number, String],
            default: null
        }
    },

    emits: [
        'submit',
        'product-name-change', 
        'category-change',
        'delivery-change',
        'markup-change'
    ],

    template: `
        <div class="card">
            <h2 class="card-title">Расчет стоимости товара</h2>
            <p class="card-subtitle">Введите данные о товаре для расчета себестоимости и цены продажи</p>
            
            <form @submit.prevent="$emit('submit')">
                
                <!-- Product Name -->
                <div class="form-group">
                    <label class="form-label">Название товара</label>
                    <input v-model="form.product_name" 
                           @input="$emit('product-name-change')"
                           type="text" 
                           placeholder="Введите название товара для автоопределения категории"
                           class="form-input"
                           required>
                </div>
                
                <!-- Category Selection -->
                <div class="form-group">
                    <label class="form-label">Категория товара</label>
                    <select v-model="selectedCategoryIndex" 
                            @change="$emit('category-change')"
                            class="form-select">
                        <option value="" disabled>Выберите категорию или введите название товара выше</option>
                        <option v-for="(category, index) in categories" :key="index" :value="index">
                            {{ formatCategoryName(category.category) }} ({{ category.material }})
                        </option>
                    </select>
                    <div v-if="detectedCategory" style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                        Плотность: {{ detectedCategory.density.toFixed(0) }} кг/м³
                        • Ставка ЖД: ${{ detectedCategory.rates.rail_base }}
                        • Авиа: ${{ detectedCategory.rates.air_base }}
                    </div>
                    
                    <!-- ТН ВЭД код -->
                    <div v-if="detectedCategory && detectedCategory.tnved_code" style="font-size: 12px; color: #6b7280; margin-top: 8px;">
                        ТН ВЭД: {{ detectedCategory.tnved_code }}
                    </div>
                </div>
                
                <div class="grid grid-2">
                    <!-- Product URL -->
                    <div class="form-group">
                        <label class="form-label">Ссылка или wechat</label>
                        <input v-model="form.product_url" 
                               type="text" 
                               placeholder="https://example.com/product или wechat ID или любой текст"
                               class="form-input">
                    </div>
                    
                    <!-- Price Yuan -->
                    <div class="form-group">
                        <label class="form-label">Цена за единицу (юань)</label>
                        <input v-model.number="form.price_yuan" 
                               type="number" 
                               step="0.01"
                               placeholder="0.00"
                               class="form-input"
                               required>
                        <!-- Рекомендации по цене -->
                        <div v-if="detectedCategory && detectedCategory.recommendations && detectedCategory.recommendations.price_yuan_min" 
                             style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Рекомендуемая цена: {{ detectedCategory.recommendations.price_yuan_min.toFixed(1) }} - {{ detectedCategory.recommendations.price_yuan_max.toFixed(1) }} ¥
                        </div>
                    </div>
                    
                    <!-- Weight -->
                    <div class="form-group">
                        <label class="form-label">Вес единицы товара (кг)</label>
                        <input v-model.number="form.weight_kg" 
                               type="number" 
                               step="0.001"
                               placeholder="0.000"
                               class="form-input"
                               required>
                    </div>
                    
                    <!-- Quantity -->
                    <div class="form-group">
                        <label class="form-label">Количество (тираж)</label>
                        <input v-model.number="form.quantity" 
                               type="number"
                               min="1"
                               placeholder="1"
                               class="form-input"
                               required>
                        <!-- Рекомендации по количеству -->
                        <div v-if="detectedCategory && detectedCategory.recommendations && detectedCategory.recommendations.quantity_min" 
                             style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Рекомендуемый тираж: {{ Math.round(detectedCategory.recommendations.quantity_min).toLocaleString() }} - {{ Math.round(detectedCategory.recommendations.quantity_max).toLocaleString() }} шт
                        </div>
                    </div>
                </div>
                
                <div class="grid grid-2">
                    <!-- Delivery Type -->
                    <div class="form-group">
                        <label class="form-label">Тип доставки</label>
                        <select v-model="form.delivery_type" 
                                @change="$emit('delivery-change')"
                                class="form-select">
                            <option value="rail">Ж/Д (железная дорога)</option>
                            <option value="air">Авиа</option>
                        </select>
                    </div>
                    
                    <!-- Logistics Rate -->
                    <div class="form-group">
                        <label class="form-label">Логистическая ставка ($/кг)</label>
                        <input v-model.number="form.custom_rate" 
                               type="number" 
                               step="0.1"
                               placeholder="0.0"
                               class="form-input">
                        <div v-if="suggestedRate > 0" style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Предлагаемая ставка: ${{ suggestedRate.toFixed(1) }}/кг
                        </div>
                    </div>
                </div>
                
                <!-- Markup -->
                <div class="form-group">
                    <label class="form-label">Наценка (множитель)</label>
                    <input v-model.number="form.markup" 
                           type="number" 
                           step="0.1"
                           min="1"
                           class="form-input">
                    <div class="markup-buttons">
                        <button type="button" @click="$emit('markup-change', 1.3)" 
                                :class="['markup-button', { active: form.markup === 1.3 }]">1.3</button>
                        <button type="button" @click="$emit('markup-change', 1.5)" 
                                :class="['markup-button', { active: form.markup === 1.5 }]">1.5</button>
                        <button type="button" @click="$emit('markup-change', 1.7)" 
                                :class="['markup-button', { active: form.markup === 1.7 }]">1.7</button>
                        <button type="button" @click="$emit('markup-change', 2.0)" 
                                :class="['markup-button', { active: form.markup === 2.0 }]">2.0</button>
                    </div>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 8px;">
                        Наценка {{ ((form.markup - 1) * 100).toFixed(0) }}% • Цена будет в {{ form.markup }} раз больше себестоимости
                    </div>
                </div>
                
                <!-- Submit Button -->
                <button type="submit" 
                        :disabled="isCalculating || !isFormValid"
                        class="submit-button">
                    <span v-if="isCalculating">
                        <span class="loading"></span>
                        Рассчитываю...
                    </span>
                    <span v-else>
                        {{ editingCalculationId ? 'Обновить расчет' : 'Рассчитать стоимость' }}
                    </span>
                </button>
            </form>
        </div>
    `,

    methods: {
        formatCategoryName(categoryName) {
            return window.Formatters?.cleanCategoryName(categoryName) || categoryName;
        }
    }
};

// Делаем компонент глобально доступным
window.CalculationForm = CalculationForm;

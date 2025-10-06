/**
 * 📝 PRODUCT FORM COMPONENT - FIXED VERSION
 * Исправленная версия без синтаксических ошибок
 */

const ProductForm = {
    name: 'ProductForm',
    
    props: {
        form: {
            type: Object,
            required: true
        },
        detectedCategory: {
            type: Object,
            default: null
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
        categories: {
            type: Array,
            default: function() { return []; }
        },
        selectedCategoryIndex: {
            type: Number,
            default: null
        }
    },
    
    emits: ['update:form', 'product-name-change', 'calculate', 'reset-form', 'category-change'],
    
    computed: {
        formData: {
            get() {
                return this.form;
            },
            set(value) {
                this.$emit('update:form', value);
            }
        },
        
        recommendations() {
            return (this.detectedCategory && this.detectedCategory.recommendations) || {};
        }
    },
    
    methods: {
        updateField: function(field, value) {
            var updatedForm = Object.assign({}, this.form);
            
            // Обработка запятой как десятичного разделителя для числовых полей
            if (field === 'price_yuan' || field === 'weight_kg' || field === 'custom_rate') {
                if (typeof value === 'string') {
                    value = value.replace(',', '.');
                }
            }
            
            updatedForm[field] = value;
            this.$emit('update:form', updatedForm);
        },
        
        onProductNameInput: function() {
            this.$emit('product-name-change', this.form.product_name);
        },
        
        onCalculate: function() {
            if (this.isFormValid) {
                this.$emit('calculate');
            }
        },
        
        onReset: function() {
            this.$emit('reset-form');
        },
        
        onCategoryChange: function(event) {
            this.$emit('category-change', {
                category: this.categories[event.target.value],
                index: parseInt(event.target.value)
            });
        },
        
        getCleanCategoryName: function(categoryName) {
            if (!categoryName) return '';
            return categoryName.replace(/\n/g, ' ').trim();
        }
    },
    
    template: '<div class="product-form">' +
        '<div class="form-group">' +
            '<label for="product_name" class="form-label">Название товара</label>' +
            '<input type="text" id="product_name" :value="form.product_name" @input="updateField(\'product_name\', $event.target.value)" @input="onProductNameInput" class="form-input" placeholder="Введите название товара" required>' +
        '</div>' +
        
        '<!-- Category Selection -->' +
        '<div v-if="detectedCategory || categories.length > 0" class="form-group">' +
            '<label class="form-label">Категория товара</label>' +
            '<div v-if="detectedCategory" style="font-size: 13px; color: #1f2937; font-weight: 500; margin-bottom: 6px;">' +
                'Определена категория: {{ getCleanCategoryName(detectedCategory.category) }}' +
            '</div>' +
            '<select v-model="selectedCategoryIndex" @change="onCategoryChange" class="form-select" size="6" style="height: auto; padding: 10px;">' +
                '<option value="" disabled>Выберите категорию</option>' +
                '<option v-for="(category, index) in categories" :key="index" :value="index" style="padding: 6px 0; line-height: 1.4;">' +
                    '{{ getCleanCategoryName(category.category) + " (" + category.material + ")" }}' +
                '</option>' +
            '</select>' +
            '<div v-if="detectedCategory" style="font-size: 12px; color: #6b7280; margin-top: 4px;">' +
                'Плотность: {{ detectedCategory.density ? detectedCategory.density.toFixed(0) : "N/A" }} кг/м³ • ' +
                'Ставка ЖД: ${{ detectedCategory.rates ? detectedCategory.rates.rail_base : "N/A" }} • ' +
                'Авиа: ${{ detectedCategory.rates ? detectedCategory.rates.air_base : "N/A" }}' +
            '</div>' +
        '</div>' +
        '<div class="form-group">' +
            '<label for="product_url" class="form-label">Ссылка на товар или WeChat</label>' +
            '<input type="text" id="product_url" :value="form.product_url" @input="updateField(\'product_url\', $event.target.value)" class="form-input" placeholder="Ссылка или контакт WeChat">' +
        '</div>' +
        '<div class="grid grid-2">' +
            '<div class="form-group">' +
                '<label for="price_yuan" class="form-label">Цена за единицу (юани)</label>' +
                '<input type="text" id="price_yuan" :value="form.price_yuan" @input="updateField(\'price_yuan\', $event.target.value)" class="form-input" placeholder="0.00" required>' +
                '<div v-if="recommendations.price_yuan_min && recommendations.price_yuan_max" style="font-size: 12px; color: #6b7280; margin-top: 4px;">' +
                    'Рекомендуемый диапазон: {{ recommendations.price_yuan_min.toFixed(1) }} - {{ recommendations.price_yuan_max.toFixed(1) }} ¥' +
                '</div>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="weight_kg" class="form-label">Вес единицы товара (кг)</label>' +
                '<input type="text" id="weight_kg" :value="form.weight_kg" @input="updateField(\'weight_kg\', $event.target.value)" class="form-input" placeholder="0.000" required>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="quantity" class="form-label">Количество (тираж)</label>' +
                '<input type="number" id="quantity" :value="form.quantity" @input="updateField(\'quantity\', parseInt($event.target.value) || 1)" class="form-input" placeholder="1" min="1" required>' +
                '<div v-if="recommendations.quantity_min && recommendations.quantity_max" style="font-size: 12px; color: #6b7280; margin-top: 4px;">' +
                    'Рекомендуемый тираж: {{ Math.round(recommendations.quantity_min).toLocaleString() }} - {{ Math.round(recommendations.quantity_max).toLocaleString() }} шт' +
                '</div>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="delivery_type" class="form-label">Тип доставки</label>' +
                '<select id="delivery_type" :value="form.delivery_type" @change="updateField(\'delivery_type\', $event.target.value)" class="form-select">' +
                    '<option value="rail">ЖД (железная дорога)</option>' +
                    '<option value="air">Авиа</option>' +
                '</select>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="custom_rate" class="form-label">Логистическая ставка ($/кг)</label>' +
                '<input type="text" id="custom_rate" :value="form.custom_rate" @input="updateField(\'custom_rate\', $event.target.value)" class="form-input" :placeholder="suggestedRate ? suggestedRate.toString() : \'0.00\'">' +
                '<div v-if="suggestedRate" style="font-size: 12px; color: #2563eb; margin-top: 4px;">Предлагаемая ставка: ${{ suggestedRate }}/кг</div>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="markup" class="form-label">Наценка (множитель)</label>' +
                '<input type="number" id="markup" :value="form.markup" @input="updateField(\'markup\', parseFloat($event.target.value) || 1.7)" class="form-input" placeholder="1.7" step="0.1" min="1" required>' +
            '</div>' +
        '</div>' +
    '</div>'
};

// Регистрируем компонент глобально
if (typeof window !== 'undefined') {
    window.ProductForm = ProductForm;
}
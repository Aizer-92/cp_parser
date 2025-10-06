/**
 * 📦 PRODUCT FORM PRECISE COMPONENT
 * Точная форма расчета с блоком пакинга вместо веса единицы товара
 */

const ProductFormPrecise = {
    name: 'ProductFormPrecise',
    
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
        },
        densityWarning: {
            type: Object,
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
        },
        
        // Вычисляем вес единицы товара из пакинговых данных
        calculatedUnitWeight() {
            if (!this.form.packing_units_per_box || !this.form.packing_box_weight) {
                return 0;
            }
            return this.form.packing_box_weight / this.form.packing_units_per_box;
        },
        
        // Вычисляем объем коробки в кубометрах
        calculatedBoxVolume() {
            if (!this.form.packing_box_length || !this.form.packing_box_width || !this.form.packing_box_height) {
                return 0;
            }
            return this.form.packing_box_length * this.form.packing_box_width * this.form.packing_box_height;
        },
        
        // Плотность товара (кг/м³)
        calculatedDensity() {
            if (!this.calculatedBoxVolume || !this.form.packing_box_weight) {
                return 0;
            }
            return this.form.packing_box_weight / this.calculatedBoxVolume;
        },
        
        // Предупреждение о плотности (вычисляется в реальном времени)
        densityWarningComputed: function() {
            if (!this.detectedCategory || !this.detectedCategory.density || !this.calculatedDensity) {
                return null;
            }
            
            var categoryDensity = this.detectedCategory.density;
            var calculatedDensity = this.calculatedDensity;
            var densityDiffPercent = Math.abs(calculatedDensity - categoryDensity) / categoryDensity * 100;
            
            if (densityDiffPercent > 30) {
                return {
                    message: 'Плотность отличается от категории на ' + densityDiffPercent.toFixed(1) + '%',
                    calculated_density: Math.round(calculatedDensity * 10) / 10,
                    category_density: Math.round(categoryDensity * 10) / 10,
                    difference_percent: Math.round(densityDiffPercent * 10) / 10
                };
            }
            
            return null;
        }
    },
    
    methods: {
        updateField: function(field, value) {
            var updatedForm = Object.assign({}, this.form);
            
            // Обработка запятой как десятичного разделителя для числовых полей
            if (field === 'price_yuan' || field === 'custom_rate' || 
                field === 'packing_box_weight' || field === 'packing_box_length' || 
                field === 'packing_box_width' || field === 'packing_box_height') {
                if (typeof value === 'string') {
                    value = value.replace(',', '.');
                }
            }
            
            updatedForm[field] = value;
            
            // Автоматически обновляем weight_kg для использования в существующей логике
            if (field.startsWith('packing_')) {
                updatedForm.weight_kg = this.getUpdatedUnitWeight(updatedForm);
            }
            
            this.$emit('update:form', updatedForm);
        },
        
        // Вспомогательная функция для вычисления веса с обновленными данными
        getUpdatedUnitWeight: function(updatedForm) {
            if (!updatedForm.packing_units_per_box || !updatedForm.packing_box_weight) {
                return 0;
            }
            return updatedForm.packing_box_weight / updatedForm.packing_units_per_box;
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
    
    template: '<div class="product-form-precise">' +
        '<div class="form-group">' +
            '<label for="product_name_precise" class="form-label">Название товара</label>' +
            '<input type="text" id="product_name_precise" :value="form.product_name" @input="updateField(\'product_name\', $event.target.value); onProductNameInput()" class="form-input" placeholder="Введите название товара" required>' +
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
            '<label for="product_url_precise" class="form-label">Ссылка на товар или WeChat</label>' +
            '<input type="text" id="product_url_precise" :value="form.product_url" @input="updateField(\'product_url\', $event.target.value)" class="form-input" placeholder="Ссылка или контакт WeChat">' +
        '</div>' +
        
        '<div class="grid grid-2">' +
            '<div class="form-group">' +
                '<label for="price_yuan_precise" class="form-label">Цена за единицу (юани)</label>' +
                '<input type="text" id="price_yuan_precise" :value="form.price_yuan" @input="updateField(\'price_yuan\', $event.target.value)" class="form-input" placeholder="0.00" required>' +
                '<div v-if="recommendations.price_yuan_min && recommendations.price_yuan_max" style="font-size: 12px; color: #6b7280; margin-top: 4px;">' +
                    'Рекомендуемый диапазон: {{ recommendations.price_yuan_min.toFixed(1) }} - {{ recommendations.price_yuan_max.toFixed(1) }} ¥' +
                '</div>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="quantity_precise" class="form-label">Количество (тираж)</label>' +
                '<input type="number" id="quantity_precise" :value="form.quantity" @input="updateField(\'quantity\', parseInt($event.target.value) || 1)" class="form-input" placeholder="1" min="1" required>' +
                '<div v-if="recommendations.quantity_min && recommendations.quantity_max" style="font-size: 12px; color: #6b7280; margin-top: 4px;">' +
                    'Рекомендуемый тираж: {{ Math.round(recommendations.quantity_min).toLocaleString() }} - {{ Math.round(recommendations.quantity_max).toLocaleString() }} шт' +
                '</div>' +
            '</div>' +
        '</div>' +
        
        '<!-- PACKING BLOCK -->' +
        '<div class="packing-block" style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 20px 0;">' +
            '<h3 style="font-size: 16px; font-weight: 600; color: #1f2937; margin-bottom: 16px;">Пакинг товара</h3>' +
            
            '<div class="grid grid-2">' +
                '<div class="form-group">' +
                    '<label for="packing_units_per_box" class="form-label">Количество штук в коробке</label>' +
                    '<input type="number" id="packing_units_per_box" :value="form.packing_units_per_box" @input="updateField(\'packing_units_per_box\', parseInt($event.target.value) || 0)" class="form-input" placeholder="100" min="1" required>' +
                '</div>' +
                '<div class="form-group">' +
                    '<label for="packing_box_weight" class="form-label">Вес коробки (кг)</label>' +
                    '<input type="text" id="packing_box_weight" :value="form.packing_box_weight" @input="updateField(\'packing_box_weight\', $event.target.value)" class="form-input" placeholder="0.000" required>' +
                '</div>' +
            '</div>' +
            
            '<div style="margin: 16px 0; padding: 12px; background: #f3f4f6; border-radius: 6px; font-size: 13px; color: #374151;">' +
                '<strong>Размеры коробки (в метрах):</strong>' +
            '</div>' +
            
            '<div class="grid" style="grid-template-columns: repeat(3, 1fr); gap: 16px;">' +
                '<div class="form-group">' +
                    '<label for="packing_box_length" class="form-label">Длина (м)</label>' +
                    '<input type="text" id="packing_box_length" :value="form.packing_box_length" @input="updateField(\'packing_box_length\', $event.target.value)" class="form-input" placeholder="0.000" step="0.001" required>' +
                '</div>' +
                '<div class="form-group">' +
                    '<label for="packing_box_width" class="form-label">Ширина (м)</label>' +
                    '<input type="text" id="packing_box_width" :value="form.packing_box_width" @input="updateField(\'packing_box_width\', $event.target.value)" class="form-input" placeholder="0.000" step="0.001" required>' +
                '</div>' +
                '<div class="form-group">' +
                    '<label for="packing_box_height" class="form-label">Высота (м)</label>' +
                    '<input type="text" id="packing_box_height" :value="form.packing_box_height" @input="updateField(\'packing_box_height\', $event.target.value)" class="form-input" placeholder="0.000" step="0.001" required>' +
                '</div>' +
            '</div>' +
            
            '<!-- Расчетные данные -->' +
            '<div v-if="calculatedUnitWeight > 0" style="margin-top: 16px; padding: 12px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px;">' +
                '<div style="font-size: 13px; color: #4b5563; margin-bottom: 4px;"><strong>Расчетные данные:</strong></div>' +
                '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; font-size: 12px; color: #6b7280;">' +
                    '<div><strong>Вес 1 шт:</strong> {{ calculatedUnitWeight.toFixed(3) }} кг</div>' +
                    '<div><strong>Объем коробки:</strong> {{ calculatedBoxVolume.toFixed(3) }} м³</div>' +
                    '<div><strong>Плотность:</strong> {{ calculatedDensity.toFixed(0) }} кг/м³</div>' +
                '</div>' +
                '<!-- Предупреждение о плотности -->' +
                '<div v-if="densityWarningComputed" style="margin-top: 8px; padding: 8px; background: #fef3c7; border: 1px solid #f59e0b; border-radius: 4px; font-size: 12px; color: #92400e;">' +
                    '<span style="font-weight: 500;">⚠️ {{ densityWarningComputed.message }}</span>' +
                    '<div style="margin-top: 4px; font-size: 11px;">' +
                        'Расчетная: {{ densityWarningComputed.calculated_density }} кг/м³ | ' +
                        'Категория: {{ densityWarningComputed.category_density }} кг/м³' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>' +
        
        '<div class="grid grid-2">' +
            '<div class="form-group">' +
                '<label for="delivery_type_precise" class="form-label">Тип доставки</label>' +
                '<select id="delivery_type_precise" :value="form.delivery_type" @change="updateField(\'delivery_type\', $event.target.value)" class="form-select">' +
                    '<option value="rail">ЖД (железная дорога)</option>' +
                    '<option value="air">Авиа</option>' +
                '</select>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="custom_rate_precise" class="form-label">Логистическая ставка ($/кг)</label>' +
                '<input type="text" id="custom_rate_precise" :value="form.custom_rate" @input="updateField(\'custom_rate\', $event.target.value)" class="form-input" :placeholder="suggestedRate ? suggestedRate.toString() : \'0.00\'">' +
                '<div v-if="suggestedRate" style="font-size: 12px; color: #2563eb; margin-top: 4px;">Предлагаемая ставка: ${{ suggestedRate }}/кг</div>' +
            '</div>' +
            '<div class="form-group">' +
                '<label for="markup_precise" class="form-label">Наценка (множитель)</label>' +
                '<input type="number" id="markup_precise" :value="form.markup" @input="updateField(\'markup\', parseFloat($event.target.value) || 1.7)" class="form-input" placeholder="1.7" step="0.1" min="1" required>' +
            '</div>' +
        '</div>' +
    '</div>'
};

// Регистрируем компонент глобально
if (typeof window !== 'undefined') {
    window.ProductFormPrecise = ProductFormPrecise;
}

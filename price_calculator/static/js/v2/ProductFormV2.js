// ProductFormV2.js - Форма данных товара с переключателем режимов
window.ProductFormV2 = {
    props: {
        modelValue: Object,
        calculationMode: {
            type: String,
            default: 'precise'  // 'quick' или 'precise'
        },
        isCalculating: Boolean
    },
    
    data() {
        return {
            quickMode: false,  // false = полный расчет (по умолчанию)
            localData: {
                name: '',
                product_url: '',  // Ссылка на товар или WeChat поставщика
                price_yuan: 0,
                quantity: 0,
                markup: 1.4,
                // Быстрый режим
                weight_kg: 0,
                // Полный режим
                packing_units_per_box: 0,
                packing_box_weight: 0,
                packing_box_length: 0,
                packing_box_width: 0,
                packing_box_height: 0
            }
        };
    },
    
    computed: {
        // Рассчитываем вес 1 штуки для полного режима
        calculatedWeightPerUnit() {
            if (this.quickMode) return null;
            
            if (!this.localData.packing_units_per_box || !this.localData.packing_box_weight) {
                return null;
            }
            
            return (this.localData.packing_box_weight / this.localData.packing_units_per_box).toFixed(4);
        },
        
        // Объем коробки
        calculatedBoxVolume() {
            if (this.quickMode) return null;
            
            const l = this.localData.packing_box_length;
            const w = this.localData.packing_box_width;
            const h = this.localData.packing_box_height;
            
            if (!l || !w || !h) return null;
            
            return (l * w * h).toFixed(4);
        },
        
        // Плотность груза
        calculatedDensity() {
            if (this.quickMode) return null;
            
            const volume = this.calculatedBoxVolume;
            const weight = this.localData.packing_box_weight;
            
            if (!volume || !weight) return null;
            
            return (weight / parseFloat(volume)).toFixed(1);
        },
        
        // Проверка валидности формы
        isFormValid() {
            if (!this.localData.name || !this.localData.price_yuan || !this.localData.quantity) {
                return false;
            }
            
            if (this.quickMode) {
                return this.localData.weight_kg > 0;
            } else {
                return this.localData.packing_units_per_box > 0 &&
                       this.localData.packing_box_weight > 0 &&
                       this.localData.packing_box_length > 0 &&
                       this.localData.packing_box_width > 0 &&
                       this.localData.packing_box_height > 0;
            }
        }
    },
    
    watch: {
        // Двунаправленная синхронизация: localData → modelValue
        localData: {
            handler(newVal) {
                this.$emit('update:modelValue', newVal);
            },
            deep: true
        },
        
        // ВАЖНО: Синхронизация modelValue → localData (для копирования из истории)
        modelValue: {
            handler(newVal) {
                if (newVal && JSON.stringify(newVal) !== JSON.stringify(this.localData)) {
                    console.log('🔄 ProductFormV2: обновление localData из modelValue', newVal);
                    this.localData = { ...newVal };
                }
            },
            deep: true,
            immediate: true
        },
        
        // Синхронизация calculationMode (родитель) → quickMode (локальный)
        calculationMode: {
            handler(newVal) {
                const newQuickMode = newVal === 'quick';
                if (this.quickMode !== newQuickMode) {
                    console.log('🔄 ProductFormV2: синхронизация режима', newVal, '→', newQuickMode);
                    this.quickMode = newQuickMode;
                }
            },
            immediate: true
        },
        
        // Синхронизация quickMode (локальный) → calculationMode (родитель)
        quickMode(newVal) {
            // Сообщаем родителю о смене режима
            this.$emit('mode-changed', newVal ? 'quick' : 'precise');
        }
    },
    
    methods: {
        handleSubmit() {
            if (!this.isFormValid) return;
            this.$emit('submit');
        }
    },
    
    template: `
        <div class="product-form-v2">
            <div class="form-header">
                <h2 style="font-size: 18px; font-weight: 600; margin: 0 0 16px 0; color: #111827;">
                    Данные товара
                </h2>
                
                <div style="display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: #f3f4f6; border-radius: 6px; margin-bottom: 20px;">
                    <input 
                        type="checkbox" 
                        id="quickModeToggle" 
                        v-model="quickMode"
                        style="width: 16px; height: 16px; cursor: pointer;"
                    />
                    <label for="quickModeToggle" style="cursor: pointer; font-size: 14px; color: #374151; user-select: none;">
                        Быстрый расчет (без данных упаковки)
                    </label>
                </div>
            </div>
            
            <div class="form-grid" style="display: grid; gap: 16px;">
                <!-- Основные данные -->
                <div class="form-group">
                    <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                        Название товара
                    </label>
                    <input 
                        type="text" 
                        v-model="localData.name"
                        placeholder="Введите название"
                        style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                    />
                </div>
                
                <div class="form-group">
                    <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                        Ссылка или WeChat
                    </label>
                    <input 
                        type="text" 
                        v-model="localData.product_url"
                        placeholder="Ссылка на товар или WeChat поставщика"
                        style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                    />
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                    <div class="form-group">
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                            Цена за штуку, юань
                        </label>
                        <input 
                            type="number" 
                            v-model.number="localData.price_yuan"
                            step="0.01"
                            min="0"
                            placeholder="0.00"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                            Количество, шт
                        </label>
                        <input 
                            type="number" 
                            v-model.number="localData.quantity"
                            min="1"
                            placeholder="0"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                </div>
                
                <div class="form-group">
                    <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                        Наценка
                    </label>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <input 
                            type="number" 
                            v-model.number="localData.markup"
                            step="0.1"
                            min="1"
                            style="width: 120px; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                        <span style="font-size: 14px; color: #6b7280;">
                            ({{ ((localData.markup - 1) * 100).toFixed(0) }}%)
                        </span>
                    </div>
                </div>
                
                <!-- Быстрый режим: просто вес -->
                <div v-if="quickMode" class="form-group">
                    <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                        Вес 1 штуки, кг
                    </label>
                    <input 
                        type="number" 
                        v-model.number="localData.weight_kg"
                        step="0.001"
                        min="0"
                        placeholder="0.000"
                        style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                    />
                </div>
                
                <!-- Полный режим: данные упаковки -->
                <div v-if="!quickMode" class="packing-section" style="background: #f9fafb; padding: 16px; border-radius: 8px; border: 1px solid #e5e7eb;">
                    <h3 style="font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">
                        Данные упаковки
                    </h3>
                    
                    <div style="display: grid; gap: 12px;">
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                            <div class="form-group">
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Единиц в коробке, шт
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="localData.packing_units_per_box"
                                    min="1"
                                    placeholder="0"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                            
                            <div class="form-group">
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Вес коробки, кг
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="localData.packing_box_weight"
                                    step="0.01"
                                    min="0"
                                    placeholder="0.00"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                        </div>
                        
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 8px;">
                                Размеры коробки, метры
                            </label>
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                                <div>
                                    <input 
                                        type="number" 
                                        v-model.number="localData.packing_box_length"
                                        step="0.01"
                                        min="0"
                                        placeholder="Длина"
                                        style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                    />
                                </div>
                                <div>
                                    <input 
                                        type="number" 
                                        v-model.number="localData.packing_box_width"
                                        step="0.01"
                                        min="0"
                                        placeholder="Ширина"
                                        style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                    />
                                </div>
                                <div>
                                    <input 
                                        type="number" 
                                        v-model.number="localData.packing_box_height"
                                        step="0.01"
                                        min="0"
                                        placeholder="Высота"
                                        style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                    />
                                </div>
                            </div>
                        </div>
                        
                        <!-- Рассчитанные значения -->
                        <div v-if="calculatedWeightPerUnit || calculatedBoxVolume || calculatedDensity" 
                             style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #e5e7eb; margin-top: 8px;">
                            <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                                <div v-if="calculatedWeightPerUnit">
                                    Вес 1 шт: <strong style="color: #111827;">{{ calculatedWeightPerUnit }} кг</strong>
                                </div>
                                <div v-if="calculatedBoxVolume">
                                    Объем коробки: <strong style="color: #111827;">{{ calculatedBoxVolume }} м³</strong>
                                </div>
                                <div v-if="calculatedDensity">
                                    Плотность: <strong style="color: #111827;">{{ calculatedDensity }} кг/м³</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Кнопка отправки -->
                <div style="margin-top: 8px;">
                    <button 
                        @click="handleSubmit"
                        :disabled="!isFormValid || isCalculating"
                        style="width: 100%; padding: 12px; background: #111827; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 600; cursor: pointer; transition: background 0.2s;"
                        :style="!isFormValid || isCalculating ? 'opacity: 0.5; cursor: not-allowed;' : 'opacity: 1;'"
                    >
                        {{ isCalculating ? 'Рассчитываем...' : 'Рассчитать маршруты' }}
                    </button>
                </div>
            </div>
        </div>
    `
};



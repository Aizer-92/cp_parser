/**
 * SETTINGS PANEL V2 COMPONENT
 * Компонент настроек для V2 интерфейса (переработанный из V1)
 */

window.SettingsPanelV2 = {
    name: 'SettingsPanelV2',
    
    props: {
        modelValue: {
            type: Object,
            required: true
        }
    },
    
    emits: ['update:modelValue', 'save'],
    
    data() {
        return {
            activeTab: 'general',  // 'general', 'categories'
            localSettings: {
                currencies: {
                    yuan_to_usd: 0.139,
                    usd_to_rub: 84.0,
                    yuan_to_rub: 11.67,
                    eur_to_rub: 100.0
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
            },
            hasUnsavedChanges: false,
            isSaving: false,
            isInitialLoad: true  // Флаг для игнорирования первого изменения
        };
    },
    
    computed: {
        computedYuanToRub() {
            if (!this.localSettings) return '0.00';
            const yuanToUsd = parseFloat(this.localSettings.currencies?.yuan_to_usd) || 0;
            const usdToRub = parseFloat(this.localSettings.currencies?.usd_to_rub) || 0;
            return (yuanToUsd * usdToRub).toFixed(2);
        }
    },
    
    watch: {
        modelValue: {
            immediate: true,
            deep: true,
            handler(newVal) {
                if (newVal) {
                    // Всегда обновляем localSettings из modelValue при изменении
                    this.localSettings = JSON.parse(JSON.stringify(newVal));
                    console.log('🔄 SettingsPanelV2: настройки загружены', this.localSettings);
                    
                    // Сбрасываем флаг при загрузке из modelValue
                    this.$nextTick(() => {
                        this.isInitialLoad = false;
                        this.hasUnsavedChanges = false;
                    });
                }
            }
        },
        
        localSettings: {
            deep: true,
            handler() {
                // Игнорируем первое изменение при загрузке
                if (!this.isInitialLoad) {
                    this.hasUnsavedChanges = true;
                }
            }
        }
    },
    
    methods: {
        saveSettings() {
            this.isSaving = true;
            this.$emit('update:modelValue', JSON.parse(JSON.stringify(this.localSettings)));
            this.$emit('save', this.localSettings);
            this.hasUnsavedChanges = false;
            
            setTimeout(() => {
                this.isSaving = false;
            }, 500);
        },
        
        resetForm() {
            this.localSettings = JSON.parse(JSON.stringify(this.modelValue));
            this.hasUnsavedChanges = false;
        }
    },
    
    template: `
        <div v-if="localSettings">
            <!-- Tabs -->
            <div style="display: flex; gap: 8px; margin-bottom: 24px; border-bottom: 2px solid #e5e7eb;">
                <button 
                    @click="activeTab = 'general'" 
                    :style="{
                        padding: '12px 24px',
                        background: activeTab === 'general' ? 'white' : 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'general' ? '2px solid #3b82f6' : 'none',
                        cursor: 'pointer',
                        fontWeight: activeTab === 'general' ? '600' : '400',
                        color: activeTab === 'general' ? '#3b82f6' : '#6b7280',
                        marginBottom: '-2px'
                    }"
                >
                    Общие настройки
                </button>
                <button 
                    @click="activeTab = 'categories'" 
                    :style="{
                        padding: '12px 24px',
                        background: activeTab === 'categories' ? 'white' : 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'categories' ? '2px solid #3b82f6' : 'none',
                        cursor: 'pointer',
                        fontWeight: activeTab === 'categories' ? '600' : '400',
                        color: activeTab === 'categories' ? '#3b82f6' : '#6b7280',
                        marginBottom: '-2px'
                    }"
                >
                    Управление категориями
                </button>
            </div>
            
            <!-- General Settings Tab -->
            <div v-if="activeTab === 'general'">
                <!-- Курсы валют -->
            <div style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                    Курсы валют
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Курс юань → доллар
                            <span style="font-size: 12px; color: #6b7280;">(1 ¥ = $ X)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.currencies.yuan_to_usd"
                            type="number"
                            step="0.001"
                            min="0.001"
                            max="1"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="0.139"
                        />
                    </div>
                    
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Курс доллар → рубль
                            <span style="font-size: 12px; color: #6b7280;">(1 $ = X ₽)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.currencies.usd_to_rub"
                            type="number"
                            step="0.1"
                            min="1"
                            max="200"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="84"
                        />
                    </div>
                    
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Курс евро → рубль
                            <span style="font-size: 12px; color: #6b7280;">(1 € = X ₽)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.currencies.eur_to_rub"
                            type="number"
                            step="0.1"
                            min="1"
                            max="200"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="100"
                        />
                    </div>
                </div>
                
                <div style="padding: 12px; background: #f9fafb; border-radius: 6px; border-left: 4px solid #111827;">
                    <span style="font-size: 14px; font-weight: 500; color: #374151;">Расчетный курс юань → рубль:</span>
                    <span style="font-size: 16px; font-weight: 700; color: #111827; margin-left: 8px;">1 ¥ = {{ computedYuanToRub }} ₽</span>
                </div>
            </div>
            
            <!-- Параметры формулы расчета -->
            <div style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                    Параметры расчета
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Комиссия за выкуп (Тони)
                            <span style="font-size: 12px; color: #6b7280;">(%)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.toni_commission_percent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="50"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="5.0"
                        />
                    </div>
                    
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Комиссия за перевод
                            <span style="font-size: 12px; color: #6b7280;">(%)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.transfer_percent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="100"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="18.0"
                        />
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Локальная доставка
                            <span style="font-size: 12px; color: #6b7280;">(¥ за кг)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.local_delivery_rate_yuan_per_kg"
                            type="number"
                            step="0.1"
                            min="0"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="2.0"
                        />
                    </div>
                    
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Доставка по Москве
                            <span style="font-size: 12px; color: #6b7280;">(₽ за тираж)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.msk_pickup_total_rub"
                            type="number"
                            step="50"
                            min="0"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="1000"
                        />
                    </div>
                    
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Дополнительные расходы
                            <span style="font-size: 12px; color: #6b7280;">(%)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.other_costs_percent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="50"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            placeholder="2.5"
                        />
                    </div>
                </div>
            </div>
            
            <!-- Настройки по умолчанию -->
            <div style="background: white; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                    Значения по умолчанию
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Наценка по умолчанию
                        </label>
                        <input 
                            v-model.number="localSettings.defaultMarkup"
                            type="number"
                            step="0.1"
                            min="1"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Будет подставляться автоматически при новом расчете
                        </div>
                    </div>
                    
                    <div>
                        <label style="display: block; font-size: 14px; font-weight: 500; color: #374151; margin-bottom: 8px;">
                            Количество по умолчанию
                        </label>
                        <input 
                            v-model.number="localSettings.defaultQuantity"
                            type="number"
                            min="1"
                            style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Будет подставляться автоматически при новом расчете
                        </div>
                    </div>
                </div>
                
                <div>
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                        <input 
                            v-model="localSettings.autoSaveCalculations"
                            type="checkbox"
                            style="width: 18px; height: 18px; cursor: pointer;"
                        />
                        <span style="font-size: 14px; font-weight: 500; color: #374151;">
                            Автоматически сохранять расчеты в историю
                        </span>
                    </label>
                    <div style="font-size: 12px; color: #6b7280; margin-top: 4px; margin-left: 30px;">
                        Расчеты будут сохраняться автоматически после завершения
                    </div>
                </div>
            </div>
            
                <!-- Кнопки действий -->
                <div style="display: flex; gap: 12px; justify-content: flex-end; padding: 16px; background: #f9fafb; border-radius: 8px;">
                    <button 
                        @click="resetForm"
                        :disabled="!hasUnsavedChanges || isSaving"
                        style="padding: 10px 20px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; color: #374151;"
                        :style="{ opacity: (!hasUnsavedChanges || isSaving) ? '0.5' : '1', cursor: (!hasUnsavedChanges || isSaving) ? 'not-allowed' : 'pointer' }"
                    >
                        Отменить изменения
                    </button>
                    
                    <button 
                        @click="saveSettings"
                        :disabled="!hasUnsavedChanges || isSaving"
                        style="padding: 10px 24px; background: #111827; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;"
                        :style="{ opacity: (!hasUnsavedChanges || isSaving) ? '0.5' : '1', cursor: (!hasUnsavedChanges || isSaving) ? 'not-allowed' : 'pointer' }"
                    >
                        {{ isSaving ? 'Сохраняю...' : 'Сохранить настройки' }}
                    </button>
                </div>
                
                <!-- Предупреждение о несохраненных изменениях -->
                <div v-if="hasUnsavedChanges && !isSaving" style="margin-top: 12px; padding: 12px; background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px;">
                    <span style="font-size: 14px; color: #92400e;">
                        У вас есть несохраненные изменения
                    </span>
                </div>
            </div>
            
            <!-- Categories Tab -->
            <div v-if="activeTab === 'categories'">
                <CategoriesPanelV2 />
            </div>
        </div>
    `
};


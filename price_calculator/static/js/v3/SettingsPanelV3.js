/**
 * SETTINGS PANEL V3 COMPONENT
 * Компонент настроек для V3 интерфейса
 */

window.SettingsPanelV3 = {
    name: 'SettingsPanelV3',
    
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
            isInitialLoad: true
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
                    this.localSettings = JSON.parse(JSON.stringify(newVal));
                    console.log('🔄 SettingsPanelV3: настройки загружены', this.localSettings);
                    
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
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'general' ? '2px solid #111827' : '2px solid transparent',
                        cursor: 'pointer',
                        fontWeight: activeTab === 'general' ? '600' : '400',
                        color: activeTab === 'general' ? '#111827' : '#6b7280',
                        marginBottom: '-2px',
                        transition: 'all 0.2s'
                    }"
                >
                    Общие настройки
                </button>
                <button 
                    @click="activeTab = 'categories'" 
                    :style="{
                        padding: '12px 24px',
                        background: 'transparent',
                        border: 'none',
                        borderBottom: activeTab === 'categories' ? '2px solid #111827' : '2px solid transparent',
                        cursor: 'pointer',
                        fontWeight: activeTab === 'categories' ? '600' : '400',
                        color: activeTab === 'categories' ? '#111827' : '#6b7280',
                        marginBottom: '-2px',
                        transition: 'all 0.2s'
                    }"
                >
                    Управление категориями
                </button>
            </div>
            
            <!-- General Settings Tab -->
            <div v-if="activeTab === 'general'">
                <!-- Курсы валют -->
            <div class="card" style="margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                    Курсы валют
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label class="form-label">
                            Курс юань → доллар
                            <span style="font-size: 12px; color: #6b7280;">(1 ¥ = $ X)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.currencies.yuan_to_usd"
                            type="number"
                            step="0.001"
                            min="0.001"
                            max="1"
                            class="form-input"
                            placeholder="0.139"
                        />
                    </div>
                    
                    <div>
                        <label class="form-label">
                            Курс доллар → рубль
                            <span style="font-size: 12px; color: #6b7280;">(1 $ = X ₽)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.currencies.usd_to_rub"
                            type="number"
                            step="0.1"
                            min="1"
                            max="200"
                            class="form-input"
                            placeholder="84"
                        />
                    </div>
                    
                    <div>
                        <label class="form-label">
                            Курс евро → рубль
                            <span style="font-size: 12px; color: #6b7280;">(1 € = X ₽)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.currencies.eur_to_rub"
                            type="number"
                            step="0.1"
                            min="1"
                            max="200"
                            class="form-input"
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
            <div class="card" style="margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                    Параметры расчета
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label class="form-label">
                            Комиссия за выкуп (Тони)
                            <span style="font-size: 12px; color: #6b7280;">(%)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.toni_commission_percent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="50"
                            class="form-input"
                            placeholder="5.0"
                        />
                    </div>
                    
                    <div>
                        <label class="form-label">
                            Комиссия за перевод
                            <span style="font-size: 12px; color: #6b7280;">(%)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.transfer_percent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="100"
                            class="form-input"
                            placeholder="18.0"
                        />
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label class="form-label">
                            Локальная доставка
                            <span style="font-size: 12px; color: #6b7280;">(¥ за кг)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.local_delivery_rate_yuan_per_kg"
                            type="number"
                            step="0.1"
                            min="0"
                            class="form-input"
                            placeholder="2.0"
                        />
                    </div>
                    
                    <div>
                        <label class="form-label">
                            Доставка по Москве
                            <span style="font-size: 12px; color: #6b7280;">(₽ за тираж)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.msk_pickup_total_rub"
                            type="number"
                            step="50"
                            min="0"
                            class="form-input"
                            placeholder="1000"
                        />
                    </div>
                    
                    <div>
                        <label class="form-label">
                            Дополнительные расходы
                            <span style="font-size: 12px; color: #6b7280;">(%)</span>
                        </label>
                        <input 
                            v-model.number="localSettings.formula.other_costs_percent"
                            type="number"
                            step="0.1"
                            min="0"
                            max="50"
                            class="form-input"
                            placeholder="2.5"
                        />
                    </div>
                </div>
            </div>
            
            <!-- Настройки по умолчанию -->
            <div class="card" style="margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                    Значения по умолчанию
                </h3>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label class="form-label">
                            Наценка по умолчанию
                        </label>
                        <input 
                            v-model.number="localSettings.defaultMarkup"
                            type="number"
                            step="0.1"
                            min="1"
                            class="form-input"
                        />
                        <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                            Будет подставляться автоматически при новом расчете
                        </div>
                    </div>
                    
                    <div>
                        <label class="form-label">
                            Количество по умолчанию
                        </label>
                        <input 
                            v-model.number="localSettings.defaultQuantity"
                            type="number"
                            min="1"
                            class="form-input"
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
                            Автоматически сохранять расчеты
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
                        class="btn-secondary"
                        :style="{ opacity: (!hasUnsavedChanges || isSaving) ? '0.5' : '1', cursor: (!hasUnsavedChanges || isSaving) ? 'not-allowed' : 'pointer' }"
                    >
                        Отменить изменения
                    </button>
                    
                    <button 
                        @click="saveSettings"
                        :disabled="!hasUnsavedChanges || isSaving"
                        class="btn-primary"
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
                <CategoriesPanelV3 />
            </div>
        </div>
    `
};


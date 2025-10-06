/**
 * 🛠️ SETTINGS PANEL COMPONENT
 * Компонент для управления настройками приложения
 */

const SettingsPanel = {
    name: 'SettingsPanel',
    
    props: {
        settings: {
            type: Object,
            default: function() {
                return {
                    currencies: {
                        yuan_to_usd: 0.139,
                        usd_to_rub: 84.0,
                        yuan_to_rub: 11.67
                    },
                    formula: {
                        toni_commission_percent: 5.0,
                        transfer_percent: 18.0,
                        local_delivery_rate_yuan_per_kg: 2.0,
                        msk_pickup_total_rub: 1000.0,
                        other_costs_percent: 2.5
                    }
                };
            }
        },
        isSaving: {
            type: Boolean,
            default: false
        }
    },
    
    data: function() {
        return {
            localSettings: {
                currencies: {
                    yuan_to_usd: 0.139,
                    usd_to_rub: 84.0
                },
                formula: {
                    toni_commission_percent: 5.0,
                    transfer_percent: 18.0,
                    local_delivery_rate_yuan_per_kg: 2.0,
                    msk_pickup_total_rub: 1000.0,
                    other_costs_percent: 2.5
                }
            },
            validationErrors: {},
            hasUnsavedChanges: false
        };
    },
    
    computed: {
        computedYuanToRub: function() {
            var yuanToUsd = parseFloat(this.localSettings.currencies.yuan_to_usd) || 0;
            var usdToRub = parseFloat(this.localSettings.currencies.usd_to_rub) || 0;
            return (yuanToUsd * usdToRub).toFixed(2);
        },
        
        isFormValid: function() {
            return Object.keys(this.validationErrors).length === 0;
        }
    },
    
    watch: {
        settings: {
            handler: function(newSettings) {
                if (newSettings && Object.keys(newSettings).length > 0) {
                    this.localSettings = JSON.parse(JSON.stringify(newSettings));
                    this.hasUnsavedChanges = false;
                }
            },
            immediate: true,
            deep: true
        },
        
        localSettings: {
            handler: function() {
                this.validateForm();
                this.hasUnsavedChanges = true;
            },
            deep: true
        }
    },
    
    methods: {
        validateForm: function() {
            var errors = {};
            
            // Валидация курсов валют
            var yuanToUsd = parseFloat(this.localSettings.currencies.yuan_to_usd);
            var usdToRub = parseFloat(this.localSettings.currencies.usd_to_rub);
            
            if (!yuanToUsd || yuanToUsd <= 0 || yuanToUsd > 1) {
                errors.yuan_to_usd = 'Курс юань/доллар должен быть между 0 и 1';
            }
            
            if (!usdToRub || usdToRub <= 0 || usdToRub > 200) {
                errors.usd_to_rub = 'Курс доллар/рубль должен быть между 0 и 200';
            }
            
            // Валидация настроек формулы
            var formula = this.localSettings.formula;
            
            if (!formula.toni_commission_percent || formula.toni_commission_percent < 0 || formula.toni_commission_percent > 50) {
                errors.toni_commission_percent = 'Комиссия за выкуп должна быть между 0% и 50%';
            }
            
            if (!formula.transfer_percent || formula.transfer_percent < 0 || formula.transfer_percent > 100) {
                errors.transfer_percent = 'Комиссия за перевод должна быть между 0% и 100%';
            }
            
            if (!formula.local_delivery_rate_yuan_per_kg || formula.local_delivery_rate_yuan_per_kg < 0) {
                errors.local_delivery_rate_yuan_per_kg = 'Стоимость локальной доставки должна быть положительной';
            }
            
            if (!formula.msk_pickup_total_rub || formula.msk_pickup_total_rub < 0) {
                errors.msk_pickup_total_rub = 'Стоимость доставки по Москве должна быть положительной';
            }
            
            if (!formula.other_costs_percent || formula.other_costs_percent < 0 || formula.other_costs_percent > 50) {
                errors.other_costs_percent = 'Дополнительные расходы должны быть между 0% и 50%';
            }
            
            this.validationErrors = errors;
        },
        
        resetForm: function() {
            this.localSettings = JSON.parse(JSON.stringify(this.settings));
            this.hasUnsavedChanges = false;
            this.validationErrors = {};
        },
        
        saveSettings: function() {
            if (!this.isFormValid) {
                alert('Пожалуйста, исправьте ошибки в форме');
                return;
            }
            
            this.$emit('save-settings', this.localSettings);
        },
        
        getFieldError: function(fieldName) {
            return this.validationErrors[fieldName] || '';
        },
        
        hasFieldError: function(fieldName) {
            return !!this.validationErrors[fieldName];
        }
    },
    
    template: `
        <div class="settings-panel">
            <div class="card">
                <h2 class="card-title">⚙️ Настройки системы</h2>
                <p class="card-subtitle">Управление курсами валют и параметрами расчета</p>
                
                <form @submit.prevent="saveSettings">
                    <!-- Курсы валют -->
                    <div class="form-section">
                        <h3 class="section-title">💱 Курсы валют</h3>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">
                                    Курс юань → доллар
                                    <span class="text-muted">(1 ¥ = $ X)</span>
                                </label>
                                <input 
                                    v-model.number="localSettings.currencies.yuan_to_usd"
                                    type="number"
                                    step="0.001"
                                    min="0.001"
                                    max="1"
                                    :class="['form-input', { 'error': hasFieldError('yuan_to_usd') }]"
                                    placeholder="0.139">
                                <div v-if="hasFieldError('yuan_to_usd')" class="error-message">
                                    {{ getFieldError('yuan_to_usd') }}
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Курс доллар → рубль
                                    <span class="text-muted">(1 $ = X ₽)</span>
                                </label>
                                <input 
                                    v-model.number="localSettings.currencies.usd_to_rub"
                                    type="number"
                                    step="0.1"
                                    min="1"
                                    max="200"
                                    :class="['form-input', { 'error': hasFieldError('usd_to_rub') }]"
                                    placeholder="84">
                                <div v-if="hasFieldError('usd_to_rub')" class="error-message">
                                    {{ getFieldError('usd_to_rub') }}
                                </div>
                            </div>
                        </div>
                        
                        <div class="computed-rate">
                            <span class="computed-label">Расчетный курс юань → рубль:</span>
                            <span class="computed-value">1 ¥ = {{ computedYuanToRub }} ₽</span>
                        </div>
                    </div>
                    
                    <!-- Настройки формулы расчета -->
                    <div class="form-section">
                        <h3 class="section-title">🧮 Параметры расчета</h3>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">
                                    Комиссия за выкуп (Тони)
                                    <span class="text-muted">(%)</span>
                                </label>
                                <input 
                                    v-model.number="localSettings.formula.toni_commission_percent"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="50"
                                    :class="['form-input', { 'error': hasFieldError('toni_commission_percent') }]"
                                    placeholder="5.0">
                                <div v-if="hasFieldError('toni_commission_percent')" class="error-message">
                                    {{ getFieldError('toni_commission_percent') }}
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Комиссия за перевод
                                    <span class="text-muted">(%)</span>
                                </label>
                                <input 
                                    v-model.number="localSettings.formula.transfer_percent"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="100"
                                    :class="['form-input', { 'error': hasFieldError('transfer_percent') }]"
                                    placeholder="18.0">
                                <div v-if="hasFieldError('transfer_percent')" class="error-message">
                                    {{ getFieldError('transfer_percent') }}
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label class="form-label">
                                    Локальная доставка
                                    <span class="text-muted">(¥ за кг)</span>
                                </label>
                                <input 
                                    v-model.number="localSettings.formula.local_delivery_rate_yuan_per_kg"
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    :class="['form-input', { 'error': hasFieldError('local_delivery_rate_yuan_per_kg') }]"
                                    placeholder="2.0">
                                <div v-if="hasFieldError('local_delivery_rate_yuan_per_kg')" class="error-message">
                                    {{ getFieldError('local_delivery_rate_yuan_per_kg') }}
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label class="form-label">
                                    Доставка по Москве
                                    <span class="text-muted">(₽ за тираж)</span>
                                </label>
                                <input 
                                    v-model.number="localSettings.formula.msk_pickup_total_rub"
                                    type="number"
                                    step="50"
                                    min="0"
                                    :class="['form-input', { 'error': hasFieldError('msk_pickup_total_rub') }]"
                                    placeholder="1000">
                                <div v-if="hasFieldError('msk_pickup_total_rub')" class="error-message">
                                    {{ getFieldError('msk_pickup_total_rub') }}
                                </div>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                Дополнительные расходы
                                <span class="text-muted">(%)</span>
                            </label>
                            <input 
                                v-model.number="localSettings.formula.other_costs_percent"
                                type="number"
                                step="0.1"
                                min="0"
                                max="50"
                                :class="['form-input', { 'error': hasFieldError('other_costs_percent') }]"
                                placeholder="2.5">
                            <div v-if="hasFieldError('other_costs_percent')" class="error-message">
                                {{ getFieldError('other_costs_percent') }}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Кнопки действий -->
                    <div class="form-actions">
                        <button 
                            type="button" 
                            @click="resetForm"
                            :disabled="!hasUnsavedChanges || isSaving"
                            class="btn btn-secondary">
                            Отменить изменения
                        </button>
                        
                        <button 
                            type="submit" 
                            :disabled="!isFormValid || !hasUnsavedChanges || isSaving"
                            class="btn btn-primary">
                            <span v-if="isSaving">
                                <span class="loading"></span>
                                Сохраняю...
                            </span>
                            <span v-else>
                                Сохранить настройки
                            </span>
                        </button>
                    </div>
                    
                    <!-- Предупреждение о несохраненных изменениях -->
                    <div v-if="hasUnsavedChanges && !isSaving" class="warning-message">
                        ⚠️ У вас есть несохраненные изменения
                    </div>
                </form>
            </div>
        </div>
    `
};

// Регистрируем компонент глобально
if (typeof window !== 'undefined') {
    window.SettingsPanel = SettingsPanel;
}

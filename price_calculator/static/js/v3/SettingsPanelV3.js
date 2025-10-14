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
    

// Импорт template (ES module)
import { SETTINGS_PANEL_TEMPLATE } from './templates/settings-panel.template.js';

window.SettingsPanelV3 = {
    template: SETTINGS_PANEL_TEMPLATE,

};


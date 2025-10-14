// PriceCalculatorAppV3.js - Главный компонент приложения V3
window.PriceCalculatorAppV3 = {
    template: `
    <div class="app-v3">
        <!-- Навигация -->
        <nav class="tabs-nav">
            <button
                v-for="tab in tabs"
                :key="tab.id"
                @click="activeTab = tab.id"
                :class="['tab', { 'tab-active': activeTab === tab.id }]"
            >
                {{ tab.label }}
            </button>
        </nav>
        
        <!-- Контент -->
        <div class="tab-content">
            <component
                :is="currentTabComponent"
                :position="positionForCalculation"
                :result="calculationResult"
                :initialRequestData="calculationRequestData"
                v-model="settings"
                @save-as-position="handleSaveAsPosition"
                @switch-tab="activeTab = $event"
                @switch-to-quick-calc="handleSwitchToQuickCalc"
                @calculation-complete="handleCalculationComplete"
                @recalculate="handleRecalculate"
                @new-calculation="handleNewCalculation"
                @save="saveSettings"
            />
        </div>
    </div>
    `,
    
    data() {
        return {
            activeTab: 'positions',
            tabs: [
                { id: 'positions', label: 'Позиции', component: 'PositionsListV3' },
                { id: 'quick', label: 'Быстрый расчёт', component: 'QuickModeV3' },
                { id: 'results', label: 'Результаты', component: 'CalculationResultsV3' },
                { id: 'factories', label: 'Фабрики', component: 'FactoriesManagerV3' },
                { id: 'settings', label: 'Настройки', component: 'SettingsPanelV3' }
            ],
            positionForCalculation: null,
            calculationResult: null,
            calculationRequestData: null,
            settings: {
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
            }
        };
    },
    
    mounted() {
        this.loadSettings();
    },
    
    computed: {
        currentTabComponent() {
            const tab = this.tabs.find(t => t.id === this.activeTab);
            return tab ? tab.component : 'QuickModeV3';
        }
    },
    
    methods: {
        loadSettings() {
            const saved = localStorage.getItem('price_calculator_settings_v3');
            if (saved) {
                try {
                    this.settings = JSON.parse(saved);
                    console.log('✅ Настройки загружены из localStorage (V3)');
                } catch (e) {
                    console.error('❌ Ошибка загрузки настроек:', e);
                }
            }
        },
        
        saveSettings(settings) {
            this.settings = settings;
            localStorage.setItem('price_calculator_settings_v3', JSON.stringify(settings));
            console.log('✅ Настройки сохранены (V3)');
            alert('Настройки успешно сохранены!');
        },
        
        handleSaveAsPosition(data) {
            console.log('Сохранение как позиция:', data);
            // TODO: Создать позицию и переключиться на неё
            // this.$emit('create-position', data);
            // this.activeTab = 'positions';
            alert('Создание позиции будет реализовано в следующем этапе');
        },
        
        handleSwitchToQuickCalc(position) {
            console.log('🚀 Переключение на QuickMode с позицией:', position);
            this.positionForCalculation = position;
            this.activeTab = 'quick';
            
            // Очищаем данные позиции через 100мс, чтобы QuickMode успел их принять
            setTimeout(() => {
                this.positionForCalculation = null;
            }, 100);
        },
        
        handleCalculationComplete(data) {
            console.log('✅ Расчет завершен, переход на вкладку Результаты');
            this.calculationResult = data.result;
            this.calculationRequestData = data.requestData;
            this.activeTab = 'results';
        },
        
        handleRecalculate(newResult) {
            console.log('🔄 Пересчет с новыми параметрами');
            this.calculationResult = newResult;
        },
        
        handleNewCalculation() {
            console.log('🆕 Новый расчет');
            this.calculationResult = null;
            this.calculationRequestData = null;
            this.activeTab = 'quick';
        }
    }
};



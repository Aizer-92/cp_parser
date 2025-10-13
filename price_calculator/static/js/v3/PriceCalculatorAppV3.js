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
                @save-as-position="handleSaveAsPosition"
                @switch-tab="activeTab = $event"
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
                { id: 'factories', label: 'Фабрики', component: 'FactoriesManagerV3' }
            ]
        };
    },
    
    computed: {
        currentTabComponent() {
            const tab = this.tabs.find(t => t.id === this.activeTab);
            return tab ? tab.component : 'QuickModeV3';
        }
    },
    
    methods: {
        handleSaveAsPosition(data) {
            console.log('Сохранение как позиция:', data);
            // TODO: Создать позицию и переключиться на неё
            // this.$emit('create-position', data);
            // this.activeTab = 'positions';
            alert('Создание позиции будет реализовано в следующем этапе');
        }
    }
};



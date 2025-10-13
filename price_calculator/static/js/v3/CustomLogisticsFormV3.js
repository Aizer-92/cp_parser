// CustomLogisticsFormV3.js - Форма ввода кастомных ставок логистики
window.CustomLogisticsFormV3 = {
    template: `
    <div class="card" style="margin-top: 24px; border: 2px solid #f59e0b;">
        <div style="background: #fef3c7; padding: 16px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px;">
            <h3 style="margin: 0 0 8px 0; color: #92400e;">
                ⚠️ Требуются кастомные параметры логистики
            </h3>
            <p style="margin: 0; color: #78350f; font-size: 14px;">
                Для категории "{{ category }}" необходимо указать параметры логистики вручную
            </p>
        </div>
        
        <form @submit.prevent="apply" class="form">
            <div v-for="(route, key) in routes" :key="key" class="custom-route-section">
                <h4 style="font-size: 16px; font-weight: 600; margin-bottom: 12px;">
                    {{ formatRouteName(key) }}
                </h4>
                
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label :for="'rate-' + key">Ставка логистики ($/кг) *</label>
                        <input
                            :id="'rate-' + key"
                            v-model.number="customParams[key].rate"
                            type="number"
                            step="0.01"
                            min="0"
                            required
                            class="form-input"
                            placeholder="Например: 3.5"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label :for="'duty-' + key">Пошлина (%)</label>
                        <input
                            :id="'duty-' + key"
                            v-model.number="customParams[key].duty_rate"
                            type="number"
                            step="0.1"
                            min="0"
                            max="100"
                            class="form-input"
                            placeholder="Например: 15"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label :for="'vat-' + key">НДС (%)</label>
                        <input
                            :id="'vat-' + key"
                            v-model.number="customParams[key].vat_rate"
                            type="number"
                            step="0.1"
                            min="0"
                            max="100"
                            class="form-input"
                            placeholder="Например: 20"
                        />
                    </div>
                </div>
            </div>
            
            <div class="form-actions" style="margin-top: 24px;">
                <button type="button" @click="cancel" class="btn-secondary">
                    Отмена
                </button>
                <button type="submit" :disabled="isApplying" class="btn-primary">
                    {{ isApplying ? 'Применение...' : 'Применить и рассчитать' }}
                </button>
            </div>
        </form>
    </div>
    `,
    
    props: {
        category: {
            type: String,
            required: true
        },
        routes: {
            type: Object,
            required: true
        }
    },
    
    data() {
        return {
            customParams: {},
            isApplying: false
        };
    },
    
    mounted() {
        // Инициализируем параметры для каждого маршрута
        Object.keys(this.routes).forEach(key => {
            this.customParams[key] = {
                rate: null,
                duty_rate: null,
                vat_rate: null
            };
        });
    },
    
    methods: {
        apply() {
            // Валидация: проверяем что хотя бы одна ставка указана
            const hasAnyRate = Object.values(this.customParams).some(p => p.rate > 0);
            
            if (!hasAnyRate) {
                alert('Укажите хотя бы одну ставку логистики');
                return;
            }
            
            // Формируем объект для API
            const logistics = {};
            Object.keys(this.customParams).forEach(key => {
                const params = this.customParams[key];
                if (params.rate > 0) {
                    logistics[key] = {
                        rate_usd_per_kg: params.rate
                    };
                    
                    if (params.duty_rate > 0) {
                        logistics[key].duty_rate = params.duty_rate;
                    }
                    if (params.vat_rate > 0) {
                        logistics[key].vat_rate = params.vat_rate;
                    }
                }
            });
            
            console.log('📤 Применяем кастомные параметры:', logistics);
            this.$emit('apply', logistics);
        },
        
        cancel() {
            this.$emit('cancel');
        },
        
        formatRouteName(key) {
            const names = {
                highway_rail: 'Highway ЖД',
                highway_air: 'Highway Авиа',
                highway_contract: 'Highway Контракт',
                prologix: 'Prologix',
                sea_container: 'Sea Container'
            };
            return names[key] || key;
        }
    }
};


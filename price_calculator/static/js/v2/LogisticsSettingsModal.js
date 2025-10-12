// LogisticsSettingsModal.js - Модальное окно настроек логистики
window.LogisticsSettingsModal = {
    props: {
        show: Boolean,
        currentResult: Object
    },
    
    data() {
        return {
            settings: {
                // Категория и пошлины
                category: '',
                tnved_code: '',
                duty_rate: 0,
                vat_rate: 20,
                
                // Highway ставки
                highway_rail_rate: 7.5,
                highway_air_rate: null,  // null = авто (ЖД + 2.1)
                highway_contract_rate: 3.4,
                highway_fixed_cost: 25000,
                
                // Prologix тарифы
                prologix_rates: [
                    { min: 2, max: 8, rate: 41000 },
                    { min: 8, max: 20, rate: 20000 },
                    { min: 20, max: 30, rate: 15000 },
                    { min: 30, max: 999, rate: 13000 }
                ],
                prologix_delivery_days: 30,
                prologix_fixed_cost: 25000,
                
                // Дополнительные расходы
                local_delivery_yuan: 3.5,
                msk_pickup_rub: 1000,
                other_costs_rub: 0
            }
        };
    },
    
    watch: {
        currentResult: {
            handler(result) {
                if (result) {
                    // Инициализируем настройки из результата расчета
                    this.settings.category = result.category || '';
                    
                    if (result.customs_info) {
                        this.settings.tnved_code = result.customs_info.tnved_code || '';
                        this.settings.duty_rate = parseFloat(result.customs_info.duty_rate) || 0;
                        this.settings.vat_rate = parseFloat(result.customs_info.vat_rate) || 20;
                    }
                }
            },
            immediate: true
        }
    },
    
    computed: {
        calculatedAirRate() {
            if (this.settings.highway_air_rate !== null) {
                return this.settings.highway_air_rate;
            }
            return this.settings.highway_rail_rate + 2.1;
        }
    },
    
    methods: {
        close() {
            this.$emit('close');
        },
        
        reset() {
            // Сброс к дефолтным значениям
            this.settings = {
                category: this.currentResult?.category || '',
                tnved_code: this.currentResult?.customs_info?.tnved_code || '',
                duty_rate: 0,
                vat_rate: 20,
                highway_rail_rate: 7.5,
                highway_air_rate: null,
                highway_contract_rate: 3.4,
                highway_fixed_cost: 25000,
                prologix_rates: [
                    { min: 2, max: 8, rate: 41000 },
                    { min: 8, max: 20, rate: 20000 },
                    { min: 20, max: 30, rate: 15000 },
                    { min: 30, max: 999, rate: 13000 }
                ],
                prologix_delivery_days: 30,
                prologix_fixed_cost: 25000,
                local_delivery_yuan: 3.5,
                msk_pickup_rub: 1000,
                other_costs_rub: 0
            };
        },
        
        apply() {
            this.$emit('apply', JSON.parse(JSON.stringify(this.settings)));
        }
    },
    
    template: `
        <div v-if="show" 
             @click.self="close"
             style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px;">
            <div style="background: white; border-radius: 12px; padding: 24px; max-width: 700px; width: 100%; max-height: 85vh; overflow-y: auto; box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);">
                <h2 style="font-size: 18px; font-weight: 600; color: #111827; margin: 0 0 20px 0;">
                    Настройка параметров расчета
                </h2>
                
                <!-- Категория и пошлины -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">
                        Категория и пошлины
                    </h3>
                    
                    <div style="display: grid; gap: 12px;">
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                Категория
                            </label>
                            <input 
                                type="text" 
                                v-model="settings.category"
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                disabled
                            />
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 12px;">
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Код ТН ВЭД
                                </label>
                                <input 
                                    type="text" 
                                    v-model="settings.tnved_code"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                            
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Пошлина, %
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="settings.duty_rate"
                                    step="0.1"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                            
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    НДС, %
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="settings.vat_rate"
                                    step="1"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="border-top: 1px solid #e5e7eb; margin: 24px 0;"></div>
                
                <!-- Highway Company -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">
                        Highway Company
                    </h3>
                    
                    <div style="display: grid; gap: 12px;">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    ЖД ставка, долл/кг
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="settings.highway_rail_rate"
                                    step="0.1"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                            
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Авиа ставка, долл/кг
                                </label>
                                <div style="display: flex; align-items: center; gap: 8px;">
                                    <input 
                                        type="number" 
                                        v-model.number="settings.highway_air_rate"
                                        :placeholder="calculatedAirRate.toFixed(1)"
                                        step="0.1"
                                        style="flex: 1; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                    />
                                    <span style="font-size: 12px; color: #6b7280; white-space: nowrap;">
                                        ({{ calculatedAirRate.toFixed(1) }})
                                    </span>
                                </div>
                            </div>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Контракт (фикс), долл/кг
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="settings.highway_contract_rate"
                                    step="0.1"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                            
                            <div>
                                <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                    Фиксированные расходы, руб
                                </label>
                                <input 
                                    type="number" 
                                    v-model.number="settings.highway_fixed_cost"
                                    step="1000"
                                    style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                                />
                            </div>
                        </div>
                    </div>
                </div>
                
                <div style="border-top: 1px solid #e5e7eb; margin: 24px 0;"></div>
                
                <!-- Prologix -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">
                        Prologix
                    </h3>
                    
                    <div style="display: grid; gap: 8px; margin-bottom: 12px;">
                        <div v-for="(tier, index) in settings.prologix_rates" :key="index" style="display: grid; grid-template-columns: 1fr 1fr 1.5fr; gap: 8px; align-items: center;">
                            <input 
                                type="number" 
                                v-model.number="tier.min"
                                placeholder="От, м³"
                                style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;"
                            />
                            <input 
                                type="number" 
                                v-model.number="tier.max"
                                placeholder="До, м³"
                                style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;"
                            />
                            <input 
                                type="number" 
                                v-model.number="tier.rate"
                                placeholder="Тариф, руб/м³"
                                style="padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 13px;"
                            />
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;">
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                Срок доставки, дней
                            </label>
                            <input 
                                type="number" 
                                v-model.number="settings.prologix_delivery_days"
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            />
                        </div>
                        
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                Фиксированные расходы, руб
                            </label>
                            <input 
                                type="number" 
                                v-model.number="settings.prologix_fixed_cost"
                                step="1000"
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            />
                        </div>
                    </div>
                </div>
                
                <div style="border-top: 1px solid #e5e7eb; margin: 24px 0;"></div>
                
                <!-- Дополнительные расходы -->
                <div style="margin-bottom: 24px;">
                    <h3 style="font-size: 15px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">
                        Дополнительные расходы
                    </h3>
                    
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                Локальная доставка, юань/шт
                            </label>
                            <input 
                                type="number" 
                                v-model.number="settings.local_delivery_yuan"
                                step="0.1"
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            />
                        </div>
                        
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                Забор МСК, руб
                            </label>
                            <input 
                                type="number" 
                                v-model.number="settings.msk_pickup_rub"
                                step="100"
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            />
                        </div>
                        
                        <div>
                            <label style="display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px;">
                                Прочие расходы, руб
                            </label>
                            <input 
                                type="number" 
                                v-model.number="settings.other_costs_rub"
                                step="100"
                                style="width: 100%; padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- Кнопки -->
                <div style="display: flex; gap: 12px; justify-content: flex-end; margin-top: 24px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <button 
                        @click="close"
                        style="padding: 10px 20px; background: white; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; color: #374151; cursor: pointer;"
                    >
                        Отмена
                    </button>
                    <button 
                        @click="reset"
                        style="padding: 10px 20px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; font-weight: 500; color: #374151; cursor: pointer;"
                    >
                        Сбросить
                    </button>
                    <button 
                        @click="apply"
                        style="padding: 10px 20px; background: #111827; color: white; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer;"
                    >
                        Применить
                    </button>
                </div>
            </div>
        </div>
    `
};










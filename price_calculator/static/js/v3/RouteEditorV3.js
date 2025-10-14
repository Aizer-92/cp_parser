// RouteEditorV3.js - Редактор параметров маршрута (аналог V2)
window.RouteEditorV3 = {
    props: {
        routeKey: String,      // highway_rail, highway_air, highway_contract, prologix, sea_container
        route: Object,         // Данные маршрута
        calculationId: Number, // ID текущего расчета
        category: String       // Категория (для отображения текущих ставок)
    },
    
    data() {
        return {
            isEditing: false,
            editParams: {
                custom_rate: null,       // Логистическая ставка ($/кг или ₽/м³)
                duty_type: 'percent',    // percent, specific, combined
                duty_rate: null,         // Пошлина (%)
                specific_rate: null,     // Специфическая ставка ($/кг)
                vat_rate: null          // НДС (%)
            }
        };
    },
    
    computed: {
        routeTitle() {
            const titles = {
                'highway_rail': 'Highway ЖД',
                'highway_air': 'Highway Авиа',
                'highway_contract': 'Highway под контракт',
                'prologix': 'Prologix',
                'sea_container': 'Море контейнером'
            };
            return titles[this.routeKey] || this.routeKey;
        },
        
        routeType() {
            return {
                isHighway: this.routeKey === 'highway_rail' || this.routeKey === 'highway_air',
                isContract: this.routeKey === 'highway_contract' || this.routeKey === 'prologix' || this.routeKey === 'sea_container',
                isPrologix: this.routeKey === 'prologix',
                isSeaContainer: this.routeKey === 'sea_container'
            };
        },
        
        canEditLogistics() {
            // Все маршруты кроме sea_container имеют логистическую ставку
            return this.routeKey !== 'sea_container';
        },
        
        canEditDuty() {
            // Только контрактные маршруты имеют пошлины
            return this.routeType.isContract;
        },
        
        logisticsUnit() {
            // Определить единицу измерения для логистики
            if (this.routeKey === 'prologix') {
                return '₽/м³';
            }
            return '$/кг';
        },
        
        currentLogisticsRate() {
            // Извлечь текущую ставку из breakdown
            if (!this.route || !this.route.breakdown) return null;
            
            const bd = this.route.breakdown;
            
            if (this.routeKey === 'prologix') {
                // Для Prologix - ставка в рублях за м³
                return bd.prologix_rate_per_m3 || bd.logistics_rate_rub_per_m3;
            } else {
                // Для остальных - ставка в долларах за кг
                return bd.logistics_rate || bd.logistics_rate_usd_per_kg;
            }
        },
        
        currentDutyInfo() {
            // Извлечь текущие пошлины из route
            if (!this.route) return null;
            
            const customs = this.route.customs_info || {};
            
            return {
                duty_type: customs.duty_type || 'percent',
                duty_rate: customs.duty_rate,
                specific_rate: customs.specific_rate,
                vat_rate: customs.vat_rate
            };
        }
    },
    
    methods: {
        openEdit() {
            this.isEditing = true;
            
            // Загрузить текущие значения
            if (this.canEditLogistics && this.currentLogisticsRate) {
                this.editParams.custom_rate = this.currentLogisticsRate;
            }
            
            if (this.canEditDuty && this.currentDutyInfo) {
                this.editParams.duty_type = this.currentDutyInfo.duty_type;
                this.editParams.duty_rate = this.currentDutyInfo.duty_rate;
                this.editParams.specific_rate = this.currentDutyInfo.specific_rate;
                this.editParams.vat_rate = this.currentDutyInfo.vat_rate;
            }
            
            console.log('✏️ Открыто редактирование:', this.routeKey, this.editParams);
        },
        
        cancelEdit() {
            this.isEditing = false;
        },
        
        async applyEdit() {
            console.log('💾 Применение изменений для', this.routeKey, this.editParams);
            
            // Подготовить custom_logistics для этого маршрута
            const customLogistics = {};
            customLogistics[this.routeKey] = {};
            
            // Логистическая ставка
            if (this.canEditLogistics && this.editParams.custom_rate) {
                customLogistics[this.routeKey].custom_rate = parseFloat(this.editParams.custom_rate);
            }
            
            // Пошлины и НДС
            if (this.canEditDuty) {
                customLogistics[this.routeKey].duty_type = this.editParams.duty_type;
                
                if (this.editParams.duty_rate) {
                    customLogistics[this.routeKey].duty_rate = parseFloat(this.editParams.duty_rate);
                }
                
                if (this.editParams.specific_rate) {
                    customLogistics[this.routeKey].specific_rate = parseFloat(this.editParams.specific_rate);
                }
                
                if (this.editParams.vat_rate) {
                    customLogistics[this.routeKey].vat_rate = parseFloat(this.editParams.vat_rate);
                }
            }
            
            console.log('📤 Custom logistics:', customLogistics);
            
            // Эмитим событие для пересчета
            this.$emit('update-route', {
                routeKey: this.routeKey,
                customLogistics: customLogistics
            });
            
            this.isEditing = false;
        },
        
        formatPrice(value) {
            if (!value) return '0';
            return value.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
        }
    },
    
    template: `
    <div class="route-editor-card">
        <!-- Заголовок маршрута -->
        <div class="route-editor-header">
            <div>
                <h4 class="route-name">{{ routeTitle }}</h4>
                <div class="route-delivery-time" style="font-size: 12px; color: #6b7280; margin-top: 4px;">
                    {{ route.delivery_time || '—' }}
                </div>
            </div>
            <button 
                @click="openEdit" 
                v-if="!isEditing"
                class="btn-icon"
                title="Редактировать параметры маршрута"
            >
                ✏
            </button>
        </div>
        
        <!-- Отображение результатов (когда НЕ редактируем) -->
        <div v-if="!isEditing" class="route-results">
            <div class="route-row">
                <span class="route-label">Себестоимость:</span>
                <span class="route-value">{{ formatPrice(route.cost_per_unit_rub) }} ₽/шт</span>
            </div>
            <div class="route-row">
                <span class="route-label">Продажная цена:</span>
                <span class="route-value">{{ formatPrice(route.sale_per_unit_rub) }} ₽/шт</span>
            </div>
            <div class="route-row">
                <span class="route-label">Прибыль:</span>
                <span class="route-value text-success">{{ formatPrice(route.profit_per_unit_rub) }} ₽/шт</span>
            </div>
            
            <!-- Текущие параметры логистики -->
            <div v-if="canEditLogistics && currentLogisticsRate" class="route-row" style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e5e7eb;">
                <span class="route-label">Логистика:</span>
                <span class="route-value" style="font-size: 12px; color: #6b7280;">
                    {{ currentLogisticsRate.toFixed(2) }} {{ logisticsUnit }}
                </span>
            </div>
            
            <!-- Текущие пошлины -->
            <div v-if="canEditDuty && currentDutyInfo" style="margin-top: 4px;">
                <div v-if="currentDutyInfo.duty_rate" class="route-row">
                    <span class="route-label">Пошлина:</span>
                    <span class="route-value" style="font-size: 12px; color: #6b7280;">
                        {{ currentDutyInfo.duty_rate }}%
                    </span>
                </div>
                <div v-if="currentDutyInfo.vat_rate" class="route-row">
                    <span class="route-label">НДС:</span>
                    <span class="route-value" style="font-size: 12px; color: #6b7280;">
                        {{ currentDutyInfo.vat_rate }}%
                    </span>
                </div>
            </div>
        </div>
        
        <!-- Форма редактирования (когда редактируем) -->
        <div v-if="isEditing" class="route-edit-form">
            <!-- Логистическая ставка (для Highway и Prologix) -->
            <div v-if="canEditLogistics" class="form-group">
                <label>Логистическая ставка ({{ logisticsUnit }})</label>
                <input
                    v-model.number="editParams.custom_rate"
                    type="number"
                    step="0.01"
                    min="0"
                    :placeholder="currentLogisticsRate ? currentLogisticsRate.toFixed(2) : 'Например: 3.5'"
                    class="form-input"
                />
                <div class="form-hint">
                    Текущая: {{ currentLogisticsRate ? currentLogisticsRate.toFixed(2) : '—' }} {{ logisticsUnit }}
                </div>
            </div>
            
            <!-- Пошлины и НДС (для контрактных маршрутов) -->
            <div v-if="canEditDuty">
                <div class="form-group">
                    <label>Тип пошлины</label>
                    <select v-model="editParams.duty_type" class="form-input">
                        <option value="percent">Адвалорная (%)</option>
                        <option value="specific">Специфическая ($/кг)</option>
                        <option value="combined">Комбинированная (% + $/кг)</option>
                    </select>
                </div>
                
                <div v-if="editParams.duty_type === 'percent' || editParams.duty_type === 'combined'" class="form-group">
                    <label>Пошлина (%)</label>
                    <input
                        v-model.number="editParams.duty_rate"
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        :placeholder="currentDutyInfo && currentDutyInfo.duty_rate ? currentDutyInfo.duty_rate : 'Например: 15'"
                        class="form-input"
                    />
                    <div class="form-hint">
                        Текущая: {{ currentDutyInfo && currentDutyInfo.duty_rate ? currentDutyInfo.duty_rate + '%' : '—' }}
                    </div>
                </div>
                
                <div v-if="editParams.duty_type === 'specific' || editParams.duty_type === 'combined'" class="form-group">
                    <label>Специфическая ставка ($/кг)</label>
                    <input
                        v-model.number="editParams.specific_rate"
                        type="number"
                        step="0.01"
                        min="0"
                        :placeholder="currentDutyInfo && currentDutyInfo.specific_rate ? currentDutyInfo.specific_rate : 'Например: 2.5'"
                        class="form-input"
                    />
                    <div class="form-hint">
                        Текущая: {{ currentDutyInfo && currentDutyInfo.specific_rate ? currentDutyInfo.specific_rate + ' $/кг' : '—' }}
                    </div>
                </div>
                
                <div class="form-group">
                    <label>НДС (%)</label>
                    <input
                        v-model.number="editParams.vat_rate"
                        type="number"
                        step="0.1"
                        min="0"
                        max="100"
                        :placeholder="currentDutyInfo && currentDutyInfo.vat_rate ? currentDutyInfo.vat_rate : 'Например: 20'"
                        class="form-input"
                    />
                    <div class="form-hint">
                        Текущий: {{ currentDutyInfo && currentDutyInfo.vat_rate ? currentDutyInfo.vat_rate + '%' : '—' }}
                    </div>
                </div>
            </div>
            
            <!-- Кнопки -->
            <div class="form-actions" style="display: flex; gap: 8px; margin-top: 16px;">
                <button @click="applyEdit" class="btn-primary">
                    Применить
                </button>
                <button @click="cancelEdit" class="btn-secondary">
                    Отмена
                </button>
            </div>
        </div>
    </div>
    `
};


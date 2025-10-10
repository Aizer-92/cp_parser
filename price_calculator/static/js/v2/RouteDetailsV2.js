// RouteDetailsV2.js - Детальный расчет выбранного маршрута
window.RouteDetailsV2 = {
    props: {
        route: Object,
        routeType: String,
        result: Object
    },
    
    computed: {
        routeTitle() {
            const titles = {
                'highway_rail': 'Highway ЖД',
                'highway_air': 'Highway Авиа',
                'highway_contract': 'Highway Контракт',
                'prologix': 'Prologix',
                'sea_container': 'Море контейнером'
            };
            return titles[this.routeType] || this.routeType;
        },
        
        isHighway() {
            return this.routeType === 'highway_rail' || this.routeType === 'highway_air';
        },
        
        isContract() {
            return this.routeType === 'highway_contract';
        },
        
        isPrologix() {
            return this.routeType === 'prologix';
        },
        
        isSeaContainer() {
            return this.routeType === 'sea_container';
        },
        
        breakdown() {
            return this.route?.breakdown || {};
        },
        
        // Общая стоимость в Китае (базовая цена + комиссии + локальная доставка)
        chinaTotal() {
            const base = this.breakdown.base_price_rub || 0;
            const toni = this.breakdown.toni_commission_rub || 0;
            const transfer = this.breakdown.transfer_commission_rub || 0;
            const local = this.breakdown.local_delivery || 0;
            return base + toni + transfer + local;
        },
        
        // Общая стоимость логистики
        logisticsTotal() {
            if (this.isSeaContainer) {
                // Для sea_container: контейнеры USD + фикс. стоимость RUB
                return (this.breakdown.containers_cost || 0) + (this.breakdown.containers_fixed_cost || 0);
            }
            return (this.breakdown.logistics || 0) + (this.breakdown.logistics_delivery || 0);
        },
        
        // Прочие расходы
        otherTotal() {
            const msk = this.breakdown.msk_pickup || 0;
            const other = this.breakdown.other_costs || 0;
            const fixed = this.breakdown.fixed_costs || 0;
            return msk + other + fixed;
        },
        
        // Общая себестоимость
        totalCost() {
            return this.route?.per_unit || 0;
        }
    },
    
    methods: {
        fmt(num) {
            if (!num || num === 0) return null;
            return new Intl.NumberFormat('ru-RU', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(num);
        },
        
        fmtInt(num) {
            if (!num || num === 0) return null;
            return new Intl.NumberFormat('ru-RU', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(num);
        },
        
        // Процент от себестоимости
        pct(value) {
            if (!value || !this.totalCost) return '';
            const percent = (value / this.totalCost) * 100;
            return ` (${percent.toFixed(1)}%)`;
        }
    },
    
    template: `
        <div v-if="route" style="margin-top: 16px;">
            <!-- Заголовок -->
            <div style="margin-bottom: 16px;">
                <h3 style="font-size: 15px; font-weight: 600; color: #111827; margin: 0;">
                    {{ routeTitle }}
                </h3>
            </div>
            
            <!-- Основные показатели -->
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
                <div style="background: #f9fafb; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">Себестоимость 1 шт</div>
                    <div style="font-size: 18px; font-weight: 700; color: #111827;">
                        {{ fmt(route.per_unit) }} ₽
                    </div>
                </div>
                
                <div style="background: #f9fafb; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">Цена продажи 1 шт</div>
                    <div style="font-size: 18px; font-weight: 700; color: #10b981;">
                        {{ fmt(route.sale_per_unit) }} ₽
                    </div>
                </div>
                
                <div style="background: #f9fafb; border-radius: 6px; padding: 12px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">Прибыль 1 шт</div>
                    <div style="font-size: 18px; font-weight: 700; color: #f59e0b;">
                        {{ fmt(route.sale_per_unit - route.per_unit) }} ₽
                    </div>
                </div>
            </div>
            
            <!-- Структура затрат -->
            <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h4 style="font-size: 13px; font-weight: 600; color: #111827; margin: 0 0 12px 0;">
                    Структура затрат (за 1 шт)
                </h4>
                
                <div style="display: grid; gap: 1px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                    <!-- БЛОК: Стоимость в Китае -->
                    <div style="background: #f9fafb; padding: 10px 12px; border-left: 2px solid #111827;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #111827; font-size: 13px; font-weight: 700;">Стоимость в Китае</span>
                            <span style="color: #111827; font-weight: 700; font-size: 14px;">
                                {{ fmt(chinaTotal) }} ₽<span style="font-size: 11px; font-weight: 600; color: #6b7280;">{{ pct(chinaTotal) }}</span>
                            </span>
                        </div>
                    </div>
                    
                    <!-- Цена в юанях -->
                    <div v-if="fmt(breakdown.base_price_rub)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Цена в юанях</span>
                            <span v-if="breakdown.base_price_yuan" style="font-size: 11px; color: #9ca3af;">
                                {{ breakdown.base_price_yuan.toFixed(2) }} ¥
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.base_price_rub) }} ₽
                        </span>
                    </div>
                    
                    <!-- Пошлина за выкуп (5%) -->
                    <div v-if="fmt(breakdown.toni_commission_rub)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <span style="color: #6b7280; font-size: 13px;">Пошлина за выкуп ({{ breakdown.toni_commission_pct }}%)</span>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.toni_commission_rub) }} ₽
                        </span>
                    </div>
                    
                    <!-- Комиссия за перевод (только для Highway ЖД/Авиа) -->
                    <div v-if="isHighway && fmt(breakdown.transfer_commission_rub)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <span style="color: #6b7280; font-size: 13px;">Комиссия за перевод ({{ breakdown.transfer_commission_pct }}%)</span>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.transfer_commission_rub) }} ₽
                        </span>
                    </div>
                    
                    <!-- Локальная доставка -->
                    <div v-if="fmt(breakdown.local_delivery)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <span style="color: #6b7280; font-size: 13px;">Локальная доставка</span>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.local_delivery) }} ₽
                        </span>
                    </div>
                    
                    <!-- БЛОК: Логистика -->
                    <div style="background: #f9fafb; padding: 10px 12px; border-left: 2px solid #111827;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #111827; font-size: 13px; font-weight: 700;">Логистика</span>
                            <span style="color: #111827; font-weight: 700; font-size: 14px;">
                                {{ fmt(logisticsTotal) }} ₽<span style="font-size: 11px; font-weight: 600; color: #6b7280;">{{ pct(logisticsTotal) }}</span>
                            </span>
                        </div>
                    </div>
                    
                    <!-- Highway ЖД/Авиа: вес × (ставка + надбавка) -->
                    <div v-if="isHighway && fmt(breakdown.logistics)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Доставка Highway</span>
                            <span v-if="breakdown.total_weight_kg && breakdown.logistics_rate" style="font-size: 11px; color: #9ca3af;">
                                {{ breakdown.total_weight_kg.toFixed(1) }} кг × {{ breakdown.logistics_rate.toFixed(2) }} $/кг
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.logistics) }} ₽
                        </span>
                    </div>
                    
                    <!-- Contract: вес × (ставка + надбавка) -->
                    <div v-if="isContract && fmt(breakdown.logistics_delivery)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Доставка под контракт</span>
                            <span v-if="breakdown.total_weight_kg && breakdown.logistics_rate" style="font-size: 11px; color: #9ca3af;">
                                {{ breakdown.total_weight_kg.toFixed(1) }} кг × {{ breakdown.logistics_rate.toFixed(2) }} $/кг
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.logistics_delivery) }} ₽
                        </span>
                    </div>
                    
                    <!-- Prologix: объем × ставка -->
                    <div v-if="isPrologix && fmt(breakdown.logistics)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Доставка Prologix</span>
                            <span v-if="breakdown.prologix_volume && breakdown.prologix_rate" style="font-size: 11px; color: #9ca3af;">
                                {{ breakdown.prologix_volume.toFixed(1) }} м³ × {{ fmtInt(breakdown.prologix_rate) }} ₽/м³
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.logistics) }} ₽
                        </span>
                    </div>
                    
                    <!-- Море контейнером: Контейнеры -->
                    <div v-if="isSeaContainer && fmt(breakdown.containers_cost)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Контейнеры (USD)</span>
                            <span style="font-size: 11px; color: #9ca3af;">
                                <template v-if="breakdown.containers_count_40ft > 0">
                                    {{ breakdown.containers_count_40ft }}×40ft
                                </template>
                                <template v-if="breakdown.containers_count_40ft > 0 && breakdown.containers_count_20ft > 0">
                                    +
                                </template>
                                <template v-if="breakdown.containers_count_20ft > 0">
                                    {{ breakdown.containers_count_20ft }}×20ft
                                </template>
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.containers_cost) }} ₽
                        </span>
                    </div>
                    
                    <!-- Море контейнером: Фиксированная стоимость контейнеров (RUB) -->
                    <div v-if="isSeaContainer && fmt(breakdown.containers_fixed_cost)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Фикс. стоимость контейнеров</span>
                            <span v-if="route.remaining_capacity_m3" style="font-size: 11px; color: #10b981;">
                                Остается {{ route.remaining_capacity_m3.toFixed(1) }} м³
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.containers_fixed_cost) }} ₽
                        </span>
                    </div>
                    
                    <!-- Пошлины (только для Contract/Prologix/SeaContainer) -->
                    <div v-if="(isContract || isPrologix || isSeaContainer) && (fmt(breakdown.duty_cost_rub) || fmt(breakdown.duty_cost))" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">Пошлины</span>
                            <span style="font-size: 11px; color: #9ca3af;">
                                <!-- Комбинированные пошлины -->
                                <template v-if="breakdown.duty_type === 'combined'">
                                    Комбинированные: {{ breakdown.duty_ad_valorem_rate }}% ИЛИ {{ breakdown.duty_specific_rate_eur }} EUR/кг
                                    <br>
                                    <span style="color: #059669; font-weight: 600;">
                                        Применена: {{ breakdown.duty_chosen_type === 'ad_valorem' ? 'процентная' : 'весовая' }}
                                    </span>
                                </template>
                                <!-- Весовые пошлины (только EUR/кг) -->
                                <template v-else-if="breakdown.duty_type === 'specific'">
                                    Весовые: {{ breakdown.duty_specific_rate_eur }} EUR/кг 
                                    ({{ breakdown.duty_specific_rate_rub ? breakdown.duty_specific_rate_rub.toFixed(2) : '0.00' }} ₽/кг)
                                </template>
                                <!-- Обычные процентные пошлины -->
                                <template v-else>
                                    {{ isSeaContainer ? (breakdown.duty_rate * 100).toFixed(1) : breakdown.duty_rate_pct }}%
                                    <template v-if="isSeaContainer && breakdown.duty_on_goods">
                                        (товар+логистика + доп. на контейнеры)
                                    </template>
                                </template>
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.duty_cost_rub || breakdown.duty_cost) }} ₽
                        </span>
                    </div>
                    
                    <!-- Детализация комбинированных пошлин (если применимо) -->
                    <div v-if="breakdown.duty_type === 'combined' && breakdown.duty_ad_valorem_amount" style="background: #f0fdf4; padding: 8px 12px 8px 36px; font-size: 11px; color: #047857;">
                        <div style="margin-bottom: 4px;">
                            <strong>Процентная пошлина:</strong> {{ breakdown.duty_ad_valorem_rate }}% = {{ fmt(breakdown.duty_ad_valorem_amount) }} ₽
                        </div>
                        <div>
                            <strong>Весовая пошлина:</strong> {{ breakdown.duty_specific_rate_eur }} EUR/кг 
                            ({{ breakdown.duty_specific_rate_rub.toFixed(2) }} ₽/кг) = {{ fmt(breakdown.duty_specific_amount) }} ₽
                        </div>
                        <div style="margin-top: 4px; font-weight: 600;">
                            Применяется большая: {{ breakdown.duty_chosen_type === 'ad_valorem' ? 'процентная' : 'весовая' }}
                        </div>
                    </div>
                    
                    <!-- Детализация весовых пошлин (если применимо) -->
                    <div v-if="breakdown.duty_type === 'specific' && breakdown.duty_specific_rate_eur" style="background: #f0f9ff; padding: 8px 12px 8px 36px; font-size: 11px; color: #0369a1;">
                        <div>
                            <strong>Весовая пошлина:</strong> {{ breakdown.duty_specific_rate_eur }} EUR/кг 
                            ({{ breakdown.duty_specific_rate_rub ? breakdown.duty_specific_rate_rub.toFixed(2) : '0.00' }} ₽/кг)
                        </div>
                        <div style="margin-top: 4px;">
                            Применяется только весовая ставка (без процентов)
                        </div>
                    </div>
                    
                    <!-- НДС (только для Contract/Prologix/SeaContainer) -->
                    <div v-if="(isContract || isPrologix || isSeaContainer) && (fmt(breakdown.vat_cost_rub) || fmt(breakdown.vat_cost))" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <div style="display: flex; flex-direction: column;">
                            <span style="color: #6b7280; font-size: 13px;">НДС</span>
                            <span style="font-size: 11px; color: #9ca3af;">
                                {{ isSeaContainer ? (breakdown.vat_rate * 100).toFixed(1) : breakdown.vat_rate_pct }}%
                            </span>
                        </div>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.vat_cost_rub || breakdown.vat_cost) }} ₽
                        </span>
                    </div>
                    
                    <!-- БЛОК: Прочие расходы -->
                    <div v-if="otherTotal > 0" style="background: #f9fafb; padding: 10px 12px; border-left: 2px solid #111827;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: #111827; font-size: 13px; font-weight: 700;">Прочие расходы</span>
                            <span style="color: #111827; font-weight: 700; font-size: 14px;">
                                {{ fmt(otherTotal) }} ₽<span style="font-size: 11px; font-weight: 600; color: #6b7280;">{{ pct(otherTotal) }}</span>
                            </span>
                        </div>
                    </div>
                    
                    <!-- Забор МСК -->
                    <div v-if="fmt(breakdown.msk_pickup)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <span style="color: #6b7280; font-size: 13px;">Забор МСК</span>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.msk_pickup) }} ₽
                        </span>
                    </div>
                    
                    <!-- Прочие расходы -->
                    <div v-if="fmt(breakdown.other_costs)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <span style="color: #6b7280; font-size: 13px;">Прочие (2.5%)</span>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.other_costs) }} ₽
                        </span>
                    </div>
                    
                    <!-- Фиксированные расходы (Контракт/Prologix) -->
                    <div v-if="fmt(breakdown.fixed_costs)" style="display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 10px 24px; background: white;">
                        <span style="color: #6b7280; font-size: 13px;">Фиксированные расходы</span>
                        <span style="color: #111827; font-weight: 600; font-size: 13px;">
                            {{ fmt(breakdown.fixed_costs) }} ₽
                        </span>
                    </div>
                </div>
            </div>
            
            <!-- Итоговая сводка -->
            <div style="border-top: 2px solid #e5e7eb; padding-top: 16px;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">
                    <div>
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 8px;">Общая себестоимость</div>
                        <div style="font-size: 20px; font-weight: 700; color: #111827;">
                            {{ fmtInt(route.cost_rub) }} ₽
                        </div>
                    </div>
                    
                    <div>
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 8px;">Цена продажи</div>
                        <div style="font-size: 20px; font-weight: 700; color: #10b981;">
                            {{ fmtInt(route.sale_rub) }} ₽
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

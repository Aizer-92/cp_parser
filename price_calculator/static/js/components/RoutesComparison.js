// Компонент: Таблица сравнения маршрутов
(function() {
    'use strict';
    
    console.log('🔄 Загрузка компонента RoutesComparison...');
    
    window.RoutesComparison = {
        name: 'RoutesComparison',
        props: {
            routes: {
                type: Object,
                required: true
            },
            selectedRoute: {
                type: String,
                default: null
            }
        },
        emits: ['select-route'],
        computed: {
            sortedRoutes() {
                const routesArray = Object.entries(this.routes).map(([key, route]) => ({
                    key: key,
                    ...route
                }));
                return routesArray.sort((a, b) => a.total_cost_rub - b.total_cost_rub);
            }
        },
        methods: {
            selectRoute(routeKey) {
                console.log('🔘 Выбран маршрут:', routeKey);
                this.$emit('select-route', routeKey);
            },
            formatNumber(num) {
                if (!num) return '0';
                return new Intl.NumberFormat('ru-RU').format(Math.round(num));
            },
            isSelected(routeKey) {
                return this.selectedRoute === routeKey;
            }
        },
        template: '<div v-if="routes && Object.keys(routes).length > 0" class="routes-comparison">' +
            '<h3 style="font-size:18px;margin-bottom:8px;font-weight:600">Сравнение маршрутов</h3>' +
            '<p style="font-size:14px;color:#6b7280;margin-bottom:16px">Выберите оптимальный вариант доставки</p>' +
            '<div style="display:flex;flex-direction:column;gap:8px">' +
                '<div v-for="(route, index) in sortedRoutes" :key="route.key" @click="selectRoute(route.key)" ' +
                'style="display:flex;align-items:center;gap:12px;padding:12px;border:1px solid #e5e7eb;border-radius:6px;cursor:pointer;transition:all 0.2s" ' +
                ':style="{borderColor: isSelected(route.key) ? \'#3b82f6\' : \'#e5e7eb\', background: isSelected(route.key) ? \'#f0f9ff\' : \'white\'}">' +
                    '<div style="flex:1">' +
                        '<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">' +
                            '<span style="font-size:15px;font-weight:600">{{ route.name }}</span>' +
                            '<span v-if="index === 0" style="font-size:11px;padding:2px 6px;background:#d1fae5;color:#065f46;border-radius:8px;font-weight:600">ВЫГОДНО</span>' +
                            '<span v-if="route.delivery_days <= 15" style="font-size:11px;padding:2px 6px;background:#dbeafe;color:#1e40af;border-radius:8px;font-weight:600">БЫСТРО</span>' +
                        '</div>' +
                        '<div style="font-size:13px;color:#6b7280">' +
                            '<template v-if="route.logistics_rate_usd">${{ route.logistics_rate_usd }}/кг</template>' +
                            '<template v-else-if="route.rate_rub_per_m3">{{ formatNumber(route.rate_rub_per_m3) }}₽/м³</template>' +
                            ' • {{ route.delivery_days }} дн' +
                        '</div>' +
                    '</div>' +
                    '<div style="text-align:right;min-width:180px">' +
                        '<div style="font-size:11px;color:#9ca3af;margin-bottom:4px">Себестоимость</div>' +
                        '<div style="font-size:17px;font-weight:600;margin-bottom:2px">{{ formatNumber(route.total_cost_rub) }} ₽</div>' +
                        '<div style="font-size:13px;color:#6b7280;font-weight:500">{{ formatNumber(route.cost_per_unit_rub) }} ₽/шт</div>' +
                    '</div>' +
                    '<div style="text-align:right;min-width:180px">' +
                        '<div style="font-size:11px;color:#9ca3af;margin-bottom:4px">Цена продажи</div>' +
                        '<div style="font-size:17px;font-weight:700;color:#10b981;margin-bottom:2px">{{ formatNumber(route.sale_total_rub) }} ₽</div>' +
                        '<div style="font-size:13px;color:#059669;font-weight:600">{{ formatNumber(route.sale_per_unit_rub) }} ₽/шт</div>' +
                    '</div>' +
                    '<button :style="{padding:\'8px 16px\',border:\'1px solid\',borderColor:isSelected(route.key)?\'#3b82f6\':\'#d1d5db\',borderRadius:\'6px\',background:isSelected(route.key)?\'#3b82f6\':\'white\',color:isSelected(route.key)?\'white\':\'#374151\',fontSize:\'14px\',fontWeight:\'500\',cursor:\'pointer\',minWidth:\'90px\'}">' +
                        '<span v-if="isSelected(route.key)">Выбрано</span>' +
                        '<span v-else>Выбрать</span>' +
                    '</button>' +
                '</div>' +
            '</div>' +
            '<div style="margin-top:12px;padding:10px;background:#f9fafb;border-radius:6px;font-size:13px;color:#6b7280;text-align:center">' +
                'Нажмите на маршрут, чтобы увидеть детальный расчет' +
            '</div>' +
        '</div>'
    };
    
    console.log('✅ Компонент RoutesComparison загружен успешно!');
})();
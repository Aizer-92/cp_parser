/**
 * 📚 HISTORY PANEL V2 COMPONENT
 * Компонент истории расчетов для V2 интерфейса
 */

window.HistoryPanelV2 = {
    name: 'HistoryPanelV2',
    
    props: {
        history: {
            type: Array,
            default: () => []
        }
    },
    
    emits: ['copy', 'edit', 'refresh', 'close'],
    
    data() {
        return {
            expandedItems: []
        };
    },
    
    methods: {
        toggleDetails(itemId) {
            const index = this.expandedItems.indexOf(itemId);
            if (index > -1) {
                this.expandedItems.splice(index, 1);
            } else {
                this.expandedItems.push(itemId);
            }
        },
        
        shareCalculation(calculationId) {
            // Формируем ссылку на расчет
            const baseUrl = window.location.origin;
            const url = `${baseUrl}/v2?calculation=${calculationId}`;
            
            // Копируем в буфер обмена БЕЗ поп-апа
            navigator.clipboard.writeText(url).then(() => {
                console.log('✅ Ссылка скопирована:', url);
                // Уведомляем пользователя визуально (без alert)
                this.showCopyNotification();
            }).catch(err => {
                console.error('❌ Ошибка копирования:', err);
                // Fallback: показываем ссылку в консоли
                console.log('📋 Скопируйте ссылку вручную:', url);
            });
        },
        
        showCopyNotification() {
            // Показываем временное уведомление без блокировки UI
            const button = event.target;
            const originalText = button.textContent;
            button.textContent = '✓ Скопировано';
            button.style.backgroundColor = '#10b981';
            button.style.color = 'white';
            
            setTimeout(() => {
                button.textContent = originalText;
                button.style.backgroundColor = '';
                button.style.color = '';
            }, 2000);
        },
        
        formatPrice(price) {
            return new Intl.NumberFormat('ru-RU', {
                style: 'currency',
                currency: 'RUB',
                minimumFractionDigits: 2
            }).format(price);
        },
        
        formatNumber(number) {
            return new Intl.NumberFormat('ru-RU').format(number);
        },
        
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return new Intl.DateTimeFormat('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(date);
        },
        
        truncateUrl(url, maxLength = 40) {
            if (!url || url.length <= maxLength) return url;
            return url.substring(0, maxLength) + '...';
        },
        
        getCalculationWord(count) {
            if (count === 1) return 'расчет';
            if (count >= 2 && count <= 4) return 'расчета';
            return 'расчетов';
        },
        
        formatRouteName(routeKey) {
            const names = {
                'highway_rail': 'Highway ЖД',
                'highway_air': 'Highway Авиа',
                'highway_contract': 'Highway Контракт',
                'prologix': 'Prologix',
                'sea_container': 'Морской контейнер'
            };
            return names[routeKey] || routeKey;
        }
    },
    
    template: `
        <div>
            <!-- Header -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <p style="font-size: 14px; color: #6b7280;">{{ history.length }} {{ getCalculationWord(history.length) }}</p>
                <button 
                    @click="$emit('refresh')"
                    style="padding: 8px 16px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; color: #374151;"
                >
                    Обновить
                </button>
            </div>
                
                <!-- History Items -->
                <div v-if="history.length > 0" style="display: flex; flex-direction: column; gap: 12px;">
                    <div v-for="item in history" :key="item.id" style="border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
                        <!-- Summary -->
                        <div 
                            @click="toggleDetails(item.id)"
                            style="padding: 16px; cursor: pointer; background: #f9fafb; display: flex; justify-content: space-between; align-items: center;"
                            onmouseover="this.style.background='#f3f4f6'"
                            onmouseout="this.style.background='#f9fafb'"
                        >
                            <div style="flex: 1;">
                                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 4px;">
                                    {{ item.product_name }}
                                    <span v-if="item.custom_logistics" style="margin-left: 8px; padding: 2px 8px; background: #dbeafe; color: #1e40af; border-radius: 4px; font-size: 11px; font-weight: 500;">
                                        📝 Кастомные ставки
                                    </span>
                                </h3>
                                <p style="font-size: 13px; color: #6b7280; margin-bottom: 4px;">{{ item.category }}</p>
                                <p style="font-size: 12px; color: #9ca3af;">
                                    {{ formatNumber(item.quantity) }} шт • {{ formatDate(item.created_at) }}
                                </p>
                            </div>
                            <div style="display: flex; align-items: center; gap: 24px;">
                                <div style="text-align: right;">
                                    <div style="font-size: 12px; color: #6b7280; margin-bottom: 4px;">{{ item.price_yuan }} ¥ за шт</div>
                                    <div style="font-size: 16px; font-weight: 700; color: #111827;">{{ formatPrice(item.sale_price_rub / item.quantity) }}</div>
                                    <div style="font-size: 12px; color: #059669;">
                                        +{{ formatPrice(item.profit_rub) }}
                                    </div>
                                </div>
                                <span style="color: #9ca3af; transition: transform 0.2s;" :style="{ transform: expandedItems.includes(item.id) ? 'rotate(180deg)' : 'rotate(0deg)' }">▼</span>
                            </div>
                        </div>
                        
                        <!-- Details -->
                        <div v-if="expandedItems.includes(item.id)" style="padding: 16px; background: white; border-top: 1px solid #e5e7eb;">
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 16px;">
                                <!-- Основные параметры -->
                                <div>
                                    <div style="font-weight: 600; color: #374151; margin-bottom: 8px; font-size: 14px;">Основные параметры</div>
                                    <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                                        <div v-if="item.weight_kg"><strong>Вес единицы:</strong> {{ item.weight_kg }} кг</div>
                                        <div v-if="item.weight_kg"><strong>Общий вес:</strong> {{ (item.weight_kg * item.quantity).toFixed(1) }} кг</div>
                                        <div><strong>Наценка:</strong> {{ item.markup }}x</div>
                                        <div v-if="item.calculation_type"><strong>Тип расчета:</strong> {{ item.calculation_type === 'precise' ? 'Точный' : 'Быстрый' }}</div>
                                    </div>
                                </div>
                                
                                <!-- Стоимость -->
                                <div>
                                    <div style="font-weight: 600; color: #374151; margin-bottom: 8px; font-size: 14px;">Расчет стоимости</div>
                                    <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                                        <div><strong>Себестоимость:</strong> {{ formatPrice(item.cost_price_rub) }}</div>
                                        <div><strong>За единицу:</strong> {{ formatPrice(item.cost_price_rub / item.quantity) }}</div>
                                        <div><strong>Цена продажи:</strong> <span style="color: #111827; font-weight: 600;">{{ formatPrice(item.sale_price_rub) }}</span></div>
                                        <div><strong>Прибыль:</strong> <span style="color: #059669; font-weight: 600;">{{ formatPrice(item.profit_rub) }}</span></div>
                                    </div>
                                </div>
                                
                                <!-- Ссылка если есть -->
                                <div v-if="item.product_url">
                                    <div style="font-weight: 600; color: #374151; margin-bottom: 8px; font-size: 14px;">Ссылка</div>
                                    <a :href="item.product_url" target="_blank" style="font-size: 12px; color: #2563eb; text-decoration: none; word-break: break-all;">
                                        {{ truncateUrl(item.product_url, 50) }}
                                    </a>
                                </div>
                            </div>
                            
                            <!-- 📝 Кастомные параметры логистики (если есть) -->
                            <div v-if="item.custom_logistics" style="margin-top: 16px; padding: 12px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 6px;">
                                <div style="font-weight: 600; color: #0c4a6e; margin-bottom: 8px; font-size: 14px;">
                                    📝 Кастомные параметры логистики
                                </div>
                                <div style="font-size: 12px; color: #075985; line-height: 1.8;">
                                    <div v-for="(params, route) in item.custom_logistics" :key="route">
                                        <strong style="color: #0c4a6e;">{{ formatRouteName(route) }}:</strong>
                                        <span v-if="params.custom_rate"> Ставка: {{ params.custom_rate }}$ •</span>
                                        <span v-if="params.duty_rate"> Пошлина: {{ params.duty_rate }}% •</span>
                                        <span v-if="params.vat_rate"> НДС: {{ params.vat_rate }}% •</span>
                                        <span v-if="params.specific_rate"> Весовая: {{ params.specific_rate }}€/кг</span>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Actions -->
                            <div style="display: flex; gap: 12px; justify-content: flex-end; padding-top: 12px; border-top: 1px solid #e5e7eb;">
                                <button 
                                    @click="shareCalculation(item.id)"
                                    style="padding: 8px 16px; background: #f3f4f6; border: 1px solid #d1d5db; color: #374151; border-radius: 6px; cursor: pointer; font-size: 14px;"
                                    title="Скопировать ссылку на расчет"
                                >
                                    Поделиться ссылкой
                                </button>
                                <button 
                                    @click="$emit('copy', item)"
                                    style="padding: 8px 16px; background: white; border: 1px solid #d1d5db; color: #374151; border-radius: 6px; cursor: pointer; font-size: 14px;"
                                    title="Создать новый расчет на основе этих данных"
                                >
                                    Копировать
                                </button>
                                <button 
                                    @click="$emit('edit', item)"
                                    style="padding: 8px 16px; background: #111827; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px;"
                                    title="Изменить этот расчет"
                                >
                                    Редактировать
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Empty State -->
                <div v-else style="text-align: center; padding: 48px 24px; color: #9ca3af;">
                    <div style="width: 80px; height: 80px; margin: 0 auto 16px; background: #f3f4f6; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                        <svg style="width: 40px; height: 40px; color: #9ca3af;" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                    <h3 style="font-size: 18px; color: #6b7280; margin-bottom: 8px;">История расчетов пуста</h3>
                    <p style="font-size: 14px;">Выполните первый расчет, чтобы увидеть его здесь</p>
                </div>
        </div>
    `
};



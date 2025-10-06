/**
 * 📚 CALCULATION HISTORY COMPONENT
 * ФАЗА 2: Модульный Vue компонент истории расчетов
 */

const CalculationHistory = {
    name: 'CalculationHistory',
    
    props: {
        history: {
            type: Array,
            default: () => []
        },
        expandedHistory: {
            type: Array,
            default: () => []
        },
        databaseAvailable: {
            type: Boolean,
            default: true
        }
    },

    emits: [
        'toggle-details',
        'edit', 
        'copy',
        'refresh'
    ],

    template: `
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <div>
                    <h2 class="card-title" style="margin-bottom: 4px;">История расчетов</h2>
                    <p class="card-subtitle" style="margin-bottom: 0;">
                        <span v-if="databaseAvailable">
                            {{ history.length }} {{ getCalculationWord(history.length) }}
                        </span>
                        <span v-else style="color: #dc2626;">
                            ⚠️ База данных недоступна
                        </span>
                    </p>
                </div>
                <button @click="$emit('refresh')" class="refresh-button">
                    🔄 Обновить
                </button>
            </div>

            <!-- Database Warning for History -->
            <div v-if="!databaseAvailable" 
                 style="background: #fef3cd; border: 1px solid #fde68a; color: #92400e; padding: 12px; border-radius: 6px; margin-bottom: 16px; font-size: 14px;">
                ⚠️ База данных недоступна. История расчетов не сохраняется.
            </div>
            
            <!-- History Items -->
            <div v-if="history.length > 0" class="history">
                <div v-for="item in history" :key="item.id" class="history-item">
                    <div class="history-summary" @click="$emit('toggle-details', item.id)">
                        <div class="history-main-info">
                            <h3>{{ item.product_name }}</h3>
                            <p>{{ item.category }}</p>
                            <p>Количество: {{ formatNumber(item.quantity) }} шт • {{ formatDate(item.created_at) }}</p>
                            <p v-if="item.product_url" style="font-size: 12px; color: #9ca3af;">
                                🔗 {{ truncateUrl(item.product_url) }}
                            </p>
                        </div>
                        <div class="history-values">
                            <div class="history-yuan-price">{{ item.price_yuan }} ¥ за шт</div>
                            <div class="history-price">{{ formatPrice(item.sale_price_rub / item.quantity) }} за шт</div>
                            <div class="history-profit">
                                Прибыль: {{ formatPrice(item.profit_rub) }} 
                                ({{ formatPercent(item.profit_rub, item.sale_price_rub) }})
                            </div>
                            <span class="history-expand-icon" :class="{ expanded: expandedHistory.includes(item.id) }">▼</span>
                        </div>
                    </div>
                    
                    <!-- Expanded Details -->
                    <div v-if="expandedHistory.includes(item.id)" class="history-details">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                            <div>
                                <div style="font-weight: 600; color: #374151; margin-bottom: 8px;">Основные параметры</div>
                                <div style="font-size: 14px; color: #6b7280; line-height: 1.5;">
                                    <div><strong>Вес единицы:</strong> {{ item.weight_kg }} кг</div>
                                    <div><strong>Общий вес:</strong> {{ item.estimated_weight }} кг</div>
                                    <div><strong>Наценка:</strong> {{ item.markup }}x ({{ ((item.markup - 1) * 100).toFixed(0) }}%)</div>
                                    <div><strong>Логистика:</strong> \${{ item.custom_rate }}/кг</div>
                                </div>
                            </div>
                            <div>
                                <div style="font-weight: 600; color: #374151; margin-bottom: 8px;">Расчет стоимости</div>
                                <div style="font-size: 14px; color: #6b7280; line-height: 1.5;">
                                    <div><strong>Себестоимость общая:</strong> {{ formatPrice(item.cost_price_rub) }}</div>
                                    <div><strong>Себестоимость за шт:</strong> {{ formatPrice(item.cost_price_rub / item.quantity) }}</div>
                                    <div><strong>Цена продажи общая:</strong> 
                                        <span style="color: #059669; font-weight: 600;">{{ formatPrice(item.sale_price_rub) }}</span>
                                    </div>
                                    <div><strong>Прибыль общая:</strong> 
                                        <span style="color: #dc2626; font-weight: 600;">{{ formatPrice(item.profit_rub) }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Action Buttons -->
                        <div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb; display: flex; gap: 12px; justify-content: flex-end;">
                            <button @click="$emit('edit', item)" 
                                    style="padding: 8px 16px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; color: #374151;">
                                Редактировать
                            </button>
                            <button @click="$emit('copy', item)" 
                                    style="padding: 8px 16px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; color: #374151;">
                                Скопировать
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Empty State -->
            <div v-else class="empty-state">
                <div class="empty-icon">📋</div>
                <h3 style="color: #6b7280; margin-bottom: 8px;">История расчетов пуста</h3>
                <p style="color: #9ca3af;">Выполните первый расчет, чтобы увидеть его здесь</p>
            </div>
        </div>
    `,

    methods: {
        formatPrice(price) {
            return window.Formatters?.formatPrice(price) || \`\${price} ₽\`;
        },
        
        formatNumber(number) {
            return window.Formatters?.formatNumber(number) || number.toString();
        },
        
        formatDate(dateString) {
            return window.Formatters?.formatDate(dateString) || dateString;
        },
        
        formatPercent(value, total) {
            return window.Formatters?.formatPercent(value, total) || '0%';
        },
        
        truncateUrl(url) {
            return window.Formatters?.truncateText(url, 40) || url;
        },
        
        getCalculationWord(count) {
            if (count === 1) return 'расчет';
            if (count >= 2 && count <= 4) return 'расчета';
            return 'расчетов';
        }
    }
};

// Делаем компонент глобально доступным
window.CalculationHistory = CalculationHistory;

/**
 * 📊 CALCULATION RESULTS COMPONENT
 * ФАЗА 2: Модульный Vue компонент результатов расчета
 */

const CalculationResults = {
    name: 'CalculationResults',
    
    props: {
        result: {
            type: Object,
            required: true
        },
        databaseAvailable: {
            type: Boolean,
            default: true
        }
    },

    template: `
        <transition name="slide-up">
            <div class="results">
                <div class="card">
                    <h2 class="card-title">Результат расчета</h2>
                    <p class="card-subtitle">{{ result.product_name }}</p>
                    
                    <!-- Database Warning -->
                    <div v-if="!databaseAvailable" 
                         style="background: #fef3cd; border: 1px solid #fde68a; color: #92400e; padding: 12px; border-radius: 6px; margin: 16px 0; font-size: 14px;">
                        ⚠️ Расчет выполнен, но не сохранен в истории (БД недоступна)
                    </div>
                    
                    <!-- Main Client Price Section -->
                    <div class="per-unit-metrics" 
                         style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 2px solid #e2e8f0;">
                        <h3 style="text-align: center; margin: 0 0 20px 0; color: #374151; font-size: 18px; font-weight: 600;">
                            Цена для клиента (за единицу)
                        </h3>
                        <div class="metrics">
                            <div class="metric-card" style="border: 1px solid #d1d5db;">
                                <div class="metric-title">Цена продажи</div>
                                <div class="metric-value" style="font-weight: 800; color: #111827; font-size: 28px;">
                                    {{ formatPrice(result.sale_price.per_unit.rub) }}
                                </div>
                                <div class="metric-secondary">\${{ result.sale_price.per_unit.usd }}</div>
                                <div class="metric-unit" style="color: #6b7280;">
                                    За {{ formatNumber(result.quantity) }} шт: {{ formatPrice(result.sale_price.total.rub) }}
                                </div>
                            </div>
                            
                            <div class="metric-card" style="border: 1px solid #d1d5db;">
                                <div class="metric-title">Себестоимость</div>
                                <div class="metric-value" style="font-weight: 700; color: #374151;">
                                    {{ formatPrice(result.cost_price.per_unit.rub) }}
                                </div>
                                <div class="metric-secondary">\${{ result.cost_price.per_unit.usd }}</div>
                                <div class="metric-unit" style="color: #6b7280;">
                                    За {{ formatNumber(result.quantity) }} шт: {{ formatPrice(result.cost_price.total.rub) }}
                                </div>
                            </div>
                            
                            <div class="metric-card" style="border: 1px solid #d1d5db;">
                                <div class="metric-title">Прибыль</div>
                                <div class="metric-value" style="font-weight: 700; color: #374151;">
                                    {{ formatPrice(result.profit.per_unit.rub) }}
                                </div>
                                <div class="metric-secondary">\${{ result.profit.per_unit.usd }}</div>
                                <div class="metric-unit" style="color: #6b7280;">
                                    За {{ formatNumber(result.quantity) }} шт: {{ formatPrice(result.profit.total.rub) }}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Total Metrics -->
                    <div class="metrics">
                        <div class="metric-card">
                            <div class="metric-title">Общая стоимость продажи</div>
                            <div class="metric-value" style="font-weight: 700; color: #1f2937;">
                                {{ formatPrice(result.sale_price.total.rub) }}
                            </div>
                            <div class="metric-secondary">\${{ formatNumber(result.sale_price.total.usd) }}</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-title">Общая себестоимость</div>
                            <div class="metric-value" style="font-weight: 700; color: #1f2937;">
                                {{ formatPrice(result.cost_price.total.rub) }}
                            </div>
                            <div class="metric-secondary">\${{ formatNumber(result.cost_price.total.usd) }}</div>
                        </div>
                        
                        <div class="metric-card">
                            <div class="metric-title">Общая прибыль</div>
                            <div class="metric-value" style="font-weight: 700; color: #059669;">
                                {{ formatPrice(result.profit.total.rub) }}
                            </div>
                            <div class="metric-secondary">\${{ formatNumber(result.profit.total.usd) }}</div>
                        </div>
                    </div>

                    <!-- Detailed Breakdown -->
                    <div class="details">
                        <div class="detail-group">
                            <div class="detail-title">Стоимость товара</div>
                            <div class="detail-item">
                                <span class="detail-label">Цена за единицу:</span>
                                <span class="detail-value">{{ result.unit_price_yuan }} ¥</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Количество:</span>
                                <span class="detail-value">{{ formatNumber(result.quantity) }} шт</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Общая стоимость:</span>
                                <span class="detail-value">
                                    {{ formatNumber(result.total_price.yuan) }} ¥ / 
                                    {{ formatPrice(result.total_price.rub) }}
                                </span>
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-title">Логистика</div>
                            <div class="detail-item">
                                <span class="detail-label">Ставка:</span>
                                <span class="detail-value">\${{ result.logistics.rate_usd }}/кг</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Тип доставки:</span>
                                <span class="detail-value">{{ result.logistics.delivery_type === 'rail' ? 'ЖД' : 'Авиа' }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Стоимость:</span>
                                <span class="detail-value">
                                    \${{ formatNumber(result.logistics.cost_usd) }} / 
                                    {{ formatPrice(result.logistics.cost_rub) }}
                                </span>
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-title">Дополнительные расходы</div>
                            <div class="detail-item">
                                <span class="detail-label">Местная доставка:</span>
                                <span class="detail-value">{{ formatPrice(result.additional_costs.local_delivery_rub) }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Самовывоз (Москва):</span>
                                <span class="detail-value">{{ formatPrice(result.additional_costs.msk_pickup_rub) }}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Обработка заказа:</span>
                                <span class="detail-value">{{ formatPrice(result.additional_costs.order_processing_rub) }}</span>
                            </div>
                        </div>
                        
                        <div class="detail-group">
                            <div class="detail-title">Наценка</div>
                            <div class="detail-item">
                                <span class="detail-label">Множитель:</span>
                                <span class="detail-value">{{ result.markup }}x</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Процент:</span>
                                <span class="detail-value">{{ ((result.markup - 1) * 100).toFixed(0) }}%</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">Вес товара:</span>
                                <span class="detail-value">{{ result.weight_kg }} кг (общий: {{ result.estimated_weight }} кг)</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </transition>
    `,

    methods: {
        formatPrice(price) {
            return window.Formatters?.formatPrice(price) || \`\${price} ₽\`;
        },
        
        formatNumber(number) {
            return window.Formatters?.formatNumber(number) || number.toString();
        }
    }
};

// Делаем компонент глобально доступным
window.CalculationResults = CalculationResults;

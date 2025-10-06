/**
 * 📚 HISTORY PANEL COMPONENT - FIXED VERSION
 * Исправленная версия без синтаксических ошибок
 */

const HistoryPanel = {
    name: 'HistoryPanel',
    
    props: {
        history: {
            type: Array,
            default: function() { return []; }
        },
        expandedHistory: {
            type: Array,
            default: function() { return []; }
        }
    },
    
    emits: ['toggle-details', 'edit-calculation', 'copy-calculation', 'delete-calculation', 'export-csv'],
    
    computed: {
        hasHistory() {
            return this.history && this.history.length > 0;
        }
    },
    
    methods: {
        formatDate(dateString) {
            var date = new Date(dateString);
            return date.toLocaleDateString('ru-RU', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        getPercentOfCost(amount, totalCost) {
            if (!totalCost || totalCost === 0) return '0';
            var percent = (amount / totalCost) * 100;
            return percent.toFixed(1);
        },
        
        isExpanded(itemId) {
            return this.expandedHistory.indexOf(itemId) !== -1;
        },
        
        onToggleDetails(item) {
            this.$emit('toggle-details', item);
        },
        
        onEditCalculation(item) {
            this.$emit('edit-calculation', item);
        },
        
        onCopyCalculation(item) {
            this.$emit('copy-calculation', item);
        },
        
        onDeleteCalculation(item) {
            if (confirm('Удалить расчет "' + item.product_name + '"?')) {
                this.$emit('delete-calculation', item);
            }
        },
        
        onExportCSV() {
            this.$emit('export-csv');
        }
    },
    
    template: '<div class="card">' +
        '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">' +
            '<div>' +
                '<h2 class="card-title" style="margin-bottom: 0;">История расчетов</h2>' +
                '<p class="card-subtitle" style="margin-bottom: 0;">Все ваши расчеты сохранены автоматически</p>' +
            '</div>' +
            '<button v-if="hasHistory" @click="onExportCSV" class="btn btn-outline" style="font-size: 12px; padding: 6px 12px;">📥 Экспорт CSV</button>' +
        '</div>' +
        
        '<div v-if="!hasHistory" style="text-align: center; padding: 48px 24px; color: #6b7280;">' +
            '<div style="font-size: 48px; margin-bottom: 16px;">📊</div>' +
            '<h3 style="margin-bottom: 8px; color: #374151;">История пуста</h3>' +
            '<p>Выполните первый расчет, чтобы увидеть его здесь</p>' +
        '</div>' +
        
        '<div v-else class="history">' +
            '<div v-for="item in history" :key="item.id" class="history-item" @click="onToggleDetails(item)">' +
                '<!-- Краткая информация (всегда видна) -->' +
                '<div class="history-summary">' +
                    '<div class="history-main-info">' +
                        '<h3>' +
                            '{{ item.product_name }}' +
                            '<span class="calculation-method-badge" :class="(item.calculation_type === \'precise\' || item.packing_units_per_box) ? \'precise\' : \'quick\'" style="margin-left: 8px; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 500; text-transform: uppercase;">' +
                                '{{ (item.calculation_type === "precise" || item.packing_units_per_box) ? "Точный" : "Быстрый" }}' +
                            '</span>' +
                            '<span class="history-expand-icon" :class="{ expanded: isExpanded(item.id) }">' +
                                '▼' +
                            '</span>' +
                        '</h3>' +
                        '<p>{{ formatDate(item.created_at) }}</p>' +
                        '<p v-if="item.product_url" style="color: #3b82f6;">' +
                            '<a :href="item.product_url" target="_blank" @click.stop style="text-decoration: none; color: inherit;">' +
                                '→ Ссылка на товар' +
                            '</a>' +
                        '</p>' +
                    '</div>' +
                    '<div class="history-prices">' +
                        '<div class="history-yuan-price">{{ item.price_yuan }}¥ × {{ item.quantity }}шт</div>' +
                        '<div class="history-unit-price"><strong>{{ (item.sale_price_rub / item.quantity).toFixed(0) }}</strong> ₽/шт</div>' +
                    '</div>' +
                '</div>' +
                
                '<!-- Детальная информация (раскрывается по клику) -->' +
                '<div v-if="isExpanded(item.id)" class="history-details">' +
                    '<div class="grid" style="grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 16px;">' +
                        '<div>' +
                            '<div style="font-weight: 600; color: #374151; margin-bottom: 8px;">Параметры товара</div>' +
                            '<div style="font-size: 14px; color: #6b7280; line-height: 1.5;">' +
                                '<div><strong>Категория:</strong> {{ item.category }}</div>' +
                                '<div><strong>Вес:</strong> {{ item.weight_kg }} кг</div>' +
                                '<div><strong>Количество:</strong> {{ item.quantity }} шт</div>' +
                                '<div><strong>Наценка:</strong> × {{ item.markup }} ({{ ((item.markup - 1) * 100).toFixed(0) }}%)</div>' +
                                '<div v-if="item.custom_rate"><strong>Логистическая ставка:</strong> ${{ item.custom_rate }}/кг</div>' +
                            '</div>' +
                        '</div>' +
                        '<div>' +
                            '<div style="font-weight: 600; color: #374151; margin-bottom: 8px;">Расчет стоимости</div>' +
                            '<div style="font-size: 14px; color: #6b7280; line-height: 1.5;">' +
                                '<div><strong>Себестоимость общая:</strong> {{ item.cost_price_rub.toFixed(0) }} ₽</div>' +
                                '<div><strong>Себестоимость за шт:</strong> {{ (item.cost_price_rub / item.quantity).toFixed(0) }} ₽</div>' +
                                '<div><strong>Цена продажи общая:</strong> <span style="color: #059669; font-weight: 600;">{{ item.sale_price_rub.toFixed(0) }} ₽</span></div>' +
                                '<div><strong>Прибыль общая:</strong> <span style="color: #dc2626; font-weight: 600;">{{ item.profit_rub.toFixed(0) }} ₽</span></div>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                    
                    '<!-- Блок пакинга (только если есть данные) -->' +
                    '<div v-if="item.packing_units_per_box" class="grid" style="grid-template-columns: 1fr; gap: 16px; margin-bottom: 16px; padding: 16px; background: #f9fafb; border-radius: 8px;">' +
                        '<div>' +
                            '<div style="font-weight: 600; color: #374151; margin-bottom: 8px;">Данные пакинга</div>' +
                            '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px;">' +
                                '<div style="font-size: 14px; color: #6b7280; line-height: 1.5;">' +
                                    '<div><strong>Штук в коробке:</strong> {{ item.packing_units_per_box }}</div>' +
                                    '<div><strong>Вес коробки:</strong> {{ item.packing_box_weight }} кг</div>' +
                                    '<div><strong>Размеры коробки:</strong> {{ item.packing_box_length }}×{{ item.packing_box_width }}×{{ item.packing_box_height }} м</div>' +
                                '</div>' +
                                '<div style="font-size: 14px; color: #6b7280; line-height: 1.5;">' +
                                    '<div><strong>Количество коробок:</strong> {{ item.packing_total_boxes }} шт</div>' +
                                    '<div><strong>Общий объем:</strong> {{ item.packing_total_volume ? item.packing_total_volume.toFixed(3) : "N/A" }} м³</div>' +
                                    '<div><strong>Общий вес коробок:</strong> {{ item.packing_total_weight ? item.packing_total_weight.toFixed(1) : "N/A" }} кг</div>' +
                                '</div>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                    
                    '<!-- Кнопки действий -->' +
                    '<div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb; display: flex; gap: 12px; justify-content: flex-end;">' +
                        '<button @click.stop="onEditCalculation(item)" style="padding: 8px 16px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; color: #374151;">' +
                            'Редактировать' +
                        '</button>' +
                        '<button @click.stop="onCopyCalculation(item)" style="padding: 8px 16px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 14px; color: #374151;">' +
                            'Скопировать' +
                        '</button>' +
                    '</div>' +
                '</div>' +
            '</div>' +
        '</div>' +
    '</div>'
};

// Регистрируем компонент глобально
if (typeof window !== 'undefined') {
    window.HistoryPanel = HistoryPanel;
}
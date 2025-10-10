/**
 * 📊 RESULTS DISPLAY COMPONENT - PRODUCTION VERSION
 * Финальная версия без отладочной информации
 */

// Fallback функция для копирования в старых браузерах
function fallbackCopyTextToClipboard(text) {
    var textArea = document.createElement("textarea");
    textArea.value = text;
    
    // Избегаем прокрутки к элементу
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        var successful = document.execCommand('copy');
        if (successful) {
            console.log('Цена скопирована в буфер обмена (fallback)');
        } else {
            console.error('Не удалось скопировать текст');
        }
    } catch (err) {
        console.error('Ошибка fallback копирования:', err);
    }
    
    document.body.removeChild(textArea);
}

const ResultsDisplay = {
    name: 'ResultsDisplay',
    
    props: {
        result: {
            type: Object,
            default: null
        },
        editingCalculationId: {
            type: [Number, String],
            default: null
        },
        isCalculating: {
            type: Boolean,
            default: false
        }
    },
    
    emits: ['save-calculation', 'update-calculation'],
    
    computed: {
        hasResult: function() {
            return this.result && typeof this.result === 'object';
        },
        
        isEditing: function() {
            return this.editingCalculationId !== null;
        },
        
        // Debug: проверка данных плотности
        hasDensityInfo: function() {
            console.log('🔍 DEBUG hasDensityInfo:', {
                has_result: !!this.result,
                has_density_info: !!(this.result && this.result.density_info),
                density_info: this.result ? this.result.density_info : null,
                has_logistics: !!(this.result && this.result.logistics),
                logistics: this.result ? this.result.logistics : null
            });
            return this.result && 
                   this.result.density_info && 
                   this.result.density_info.has_density_data === true;
        },
        
        // Debug: проверка данных Prologix
        hasPrologixInfo: function() {
            console.log('🔍 DEBUG hasPrologixInfo:', {
                has_result: !!this.result,
                has_prologix: !!(this.result && this.result.prologix_cost),
                prologix_cost: this.result ? this.result.prologix_cost : null
            });
            return this.result && this.result.prologix_cost;
        },
        
            // Проверяем наличие данных пакинга для точных расчетов
            hasPackingData: function() {
                var hasPacking = this.result && 
                               this.result.packing_units_per_box > 0 && 
                               this.result.packing_box_weight > 0 && 
                               this.result.packing_box_length > 0 &&
                               this.result.packing_box_width > 0 && 
                               this.result.packing_box_height > 0;
                return hasPacking;
            },
        
        // Расчет общего количества коробок
        totalBoxes: function() {
            if (!this.hasPackingData) return 0;
            return Math.ceil(this.result.quantity / this.result.packing_units_per_box);
        },
        
        // Расчет общего объема всех коробок
        totalVolume: function() {
            if (!this.hasPackingData) return 0;
            var boxVolume = this.result.packing_box_length * this.result.packing_box_width * this.result.packing_box_height;
            return boxVolume * this.totalBoxes;
        },
        
        // Расчет общего веса всех коробок
        totalPackingWeight: function() {
            if (!this.hasPackingData) return 0;
            return this.result.packing_box_weight * this.totalBoxes;
        },
        
        // Проверяем наличие данных по пошлинам
        hasCustomsInfo: function() {
            return this.result && this.result.customs_info && this.result.customs_info.tnved_code;
        }
    },
    
    methods: {
        getPercentOfCost: function(amount, totalCost) {
            if (!totalCost || totalCost === 0) return '0';
            var percent = (amount / totalCost) * 100;
            return percent.toFixed(1).replace('.', ',');
        },
        
        formatNumber: function(number, decimals) {
            if (typeof number !== 'number') return '0';
            if (decimals === undefined) decimals = 2;
            return number.toFixed(decimals).replace('.', ',');
        },
        
        formatNumberWithSpaces: function(number) {
            if (typeof number !== 'number') return '0';
            return number.toLocaleString('ru-RU').replace(/\./g, ',');
        },
        
        onSaveCalculation: function() {
            if (this.hasResult) {
                if (this.isEditing) {
                    this.$emit('update-calculation', {
                        id: this.editingCalculationId,
                        data: this.result
                    });
                } else {
                    this.$emit('save-calculation', this.result);
                }
            }
        },
        
        copySalePrice: function() {
            console.log('🔍 copySalePrice вызвана!');
            if (!this.hasResult) {
                console.log('❌ Нет результата для копирования');
                return;
            }
            
            // Формируем строку для копирования: доллары + табулятор + рубли
            var priceText = this.formatNumber(this.result.sale_price.per_unit.usd) + '\t' + this.formatNumberWithSpaces(this.result.sale_price.per_unit.rub);
            console.log('📋 Копируем текст:', priceText);
            
            // Копируем в буфер обмена
            if (navigator.clipboard && window.isSecureContext) {
                // Современный способ
                navigator.clipboard.writeText(priceText).then(function() {
                    console.log('✅ Цена скопирована в буфер обмена');
                }).catch(function(err) {
                    console.error('❌ Ошибка копирования:', err);
                    fallbackCopyTextToClipboard(priceText);
                });
            } else {
                // Fallback для старых браузеров
                console.log('🔄 Используем fallback копирование');
                fallbackCopyTextToClipboard(priceText);
            }
        }
    },
    
    template: '<div v-if="hasResult" class="results">' +
        '<div class="card">' +
            '<h2 class="card-title">Результат расчета</h2>' +
            '<p class="card-subtitle">{{ result.product_name }}</p>' +
            
            '<!-- Price Per Unit (Main for Client) -->' +
            '<div class="per-unit-metrics" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; padding: 24px; margin-bottom: 24px; border: 2px solid #e2e8f0;">' +
                '<h3 style="text-align: center; margin: 0 0 20px 0; color: #374151; font-size: 18px; font-weight: 600;">Цена для клиента (за единицу)</h3>' +
                '<div class="metrics">' +
                    '<div class="metric-card" style="border: 1px solid #d1d5db; position: relative;">' +
                        '<div class="metric-title">Цена продажи</div>' +
                        '<div class="metric-value" style="font-weight: 800; color: #111827; font-size: 28px;">{{ formatNumberWithSpaces(result.sale_price.per_unit.rub) }} руб</div>' +
                        '<div class="metric-secondary">${{ formatNumber(result.sale_price.per_unit.usd) }}</div>' +
                        '<div class="metric-unit" style="color: #6b7280;">За {{ result.quantity.toLocaleString() }} шт: {{ formatNumberWithSpaces(result.sale_price.total.rub) }} руб</div>' +
                        '<button @click="copySalePrice" class="copy-button" title="Копировать цены для Excel (USD + TAB + RUB)">' +
                            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">' +
                                '<rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>' +
                                '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>' +
                            '</svg>' +
                        '</button>' +
                    '</div>' +
                    
                    '<div class="metric-card" style="border: 1px solid #d1d5db;">' +
                        '<div class="metric-title">Себестоимость</div>' +
                        '<div class="metric-value" style="font-weight: 700; color: #374151;">{{ formatNumberWithSpaces(result.cost_price.per_unit.rub) }} руб</div>' +
                        '<div class="metric-secondary">${{ formatNumber(result.cost_price.per_unit.usd) }}</div>' +
                        '<div class="metric-unit" style="color: #6b7280;">За {{ result.quantity.toLocaleString() }} шт: {{ formatNumberWithSpaces(result.cost_price.total.rub) }} руб</div>' +
                    '</div>' +
                    
                    '<div class="metric-card" style="border: 1px solid #d1d5db;">' +
                        '<div class="metric-title">Прибыль</div>' +
                        '<div class="metric-value" style="font-weight: 700; color: #374151;">{{ formatNumberWithSpaces(result.profit.per_unit.rub) }} руб</div>' +
                        '<div class="metric-secondary">${{ formatNumber(result.profit.per_unit.usd) }}</div>' +
                        '<div class="metric-unit" style="color: #6b7280;">За {{ result.quantity.toLocaleString() }} шт: {{ formatNumberWithSpaces(result.profit.total.rub) }} руб</div>' +
                    '</div>' +
                '</div>' +
            '</div>' +

            '<!-- Total Metrics -->' +
            '<div class="metrics">' +
                '<div class="metric-card">' +
                    '<div class="metric-title">Общая стоимость продажи</div>' +
                    '<div class="metric-value" style="font-weight: 700; color: #1f2937;">{{ formatNumberWithSpaces(result.sale_price.total.rub) }} руб</div>' +
                    '<div class="metric-secondary">${{ formatNumber(result.sale_price.total.usd) }}</div>' +
                '</div>' +
                
                '<div class="metric-card">' +
                    '<div class="metric-title">Общая себестоимость</div>' +
                    '<div class="metric-value" style="font-weight: 700; color: #1f2937;">{{ formatNumberWithSpaces(result.cost_price.total.rub) }} руб</div>' +
                    '<div class="metric-secondary">${{ formatNumber(result.cost_price.total.usd) }}</div>' +
                '</div>' +
                
                '<div class="metric-card">' +
                    '<div class="metric-title">Общая прибыль</div>' +
                    '<div class="metric-value" style="font-weight: 700; color: #059669;">{{ formatNumberWithSpaces(result.profit.total.rub) }} руб</div>' +
                    '<div class="metric-secondary">${{ formatNumber(result.profit.total.usd) }}</div>' +
                '</div>' +
            '</div>' +
            
            '<!-- Details -->' +
            '<div class="details">' +
                '<div class="detail-group">' +
                    '<div class="detail-title">Детали товара</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Категория:</span>' +
                        '<span class="detail-value">{{ result.category }}</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Тираж:</span>' +
                        '<span class="detail-value">{{ result.quantity.toLocaleString() }} шт</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Общий вес:</span>' +
                        '<span class="detail-value">{{ result.estimated_weight }} кг</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Доставка:</span>' +
                        '<span class="detail-value">{{ result.logistics.delivery_type === "rail" ? "Ж/Д" : "Авиа" }}</span>' +
                    '</div>' +
                '</div>' +
                
                '<!-- Packing Info Block (только для точных расчетов) -->' +
                '<div v-if="hasPackingData" class="detail-group">' +
                    '<div class="detail-title">Пакинг товара</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Штук в коробке:</span>' +
                        '<span class="detail-value">{{ result.packing_units_per_box }} шт</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Вес коробки:</span>' +
                        '<span class="detail-value">{{ formatNumber(result.packing_box_weight, 3) }} кг</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Размеры коробки:</span>' +
                        '<span class="detail-value">{{ formatNumber(result.packing_box_length, 3) }} × {{ formatNumber(result.packing_box_width, 3) }} × {{ formatNumber(result.packing_box_height, 3) }} м</span>' +
                    '</div>' +
                    '<div class="detail-item" style="border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 8px;">' +
                        '<span class="detail-label"><strong>Количество коробок:</strong></span>' +
                        '<span class="detail-value"><strong>{{ totalBoxes }} шт</strong></span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label"><strong>Общий объем:</strong></span>' +
                        '<span class="detail-value"><strong>{{ formatNumber(totalVolume, 3) }} м³</strong></span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label"><strong>Общий вес коробок:</strong></span>' +
                        '<span class="detail-value"><strong>{{ formatNumber(totalPackingWeight, 1) }} кг</strong></span>' +
                    '</div>' +
                '</div>' +
                
                '<div class="detail-group">' +
                    '<div class="detail-title">Структура затрат</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Товар:</span>' +
                        '<span class="detail-value">{{ formatNumberWithSpaces(result.total_price.rub) }} руб ({{ getPercentOfCost(result.total_price.rub, result.cost_price.total.rub) }}%)</span>' +
                    '</div>' +
                    
                    '<!-- Детализация логистической ставки -->' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Логистика:</span>' +
                        '<span class="detail-value">{{ formatNumberWithSpaces(result.logistics.cost_rub) }} руб ({{ getPercentOfCost(result.logistics.cost_rub, result.cost_price.total.rub) }}%)</span>' +
                    '</div>' +
                    '<div v-if="hasDensityInfo" style="margin-left: 20px; font-size: 12px; color: #6b7280;">' +
                        '<div style="display: flex; justify-content: space-between; padding: 2px 0;">' +
                            '<span>Базовая ставка:</span>' +
                            '<span>${{ formatNumber(result.logistics.base_rate_usd, 2) }}/кг</span>' +
                        '</div>' +
                        '<div v-if="result.logistics.density_surcharge_usd > 0" style="display: flex; justify-content: space-between; padding: 2px 0; color: #dc2626;">' +
                            '<span>⚠️ Надбавка за плотность ({{ formatNumber(result.density_info.density_kg_m3, 1) }} кг/м³):</span>' +
                            '<span>+${{ formatNumber(result.logistics.density_surcharge_usd, 2) }}/кг</span>' +
                        '</div>' +
                        '<div v-else style="display: flex; justify-content: space-between; padding: 2px 0; color: #059669;">' +
                            '<span>✅ Плотность оптимальная ({{ formatNumber(result.density_info.density_kg_m3, 1) }} кг/м³):</span>' +
                            '<span>Надбавка: $0.00</span>' +
                        '</div>' +
                        '<div style="display: flex; justify-content: space-between; padding: 2px 0; font-weight: 600; border-top: 1px solid #e5e7eb; margin-top: 2px;">' +
                            '<span>Итоговая ставка:</span>' +
                            '<span>${{ formatNumber(result.logistics.rate_usd, 2) }}/кг</span>' +
                        '</div>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Локальная доставка:</span>' +
                        '<span class="detail-value">{{ formatNumberWithSpaces(result.additional_costs.local_delivery_rub) }} руб ({{ getPercentOfCost(result.additional_costs.local_delivery_rub, result.cost_price.total.rub) }}%)</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Забор МСК:</span>' +
                        '<span class="detail-value">{{ formatNumberWithSpaces(result.additional_costs.msk_pickup_rub) }} руб ({{ getPercentOfCost(result.additional_costs.msk_pickup_rub, result.cost_price.total.rub) }}%)</span>' +
                    '</div>' +
                    '<div class="detail-item">' +
                        '<span class="detail-label">Прочие расходы:</span>' +
                        '<span class="detail-value">{{ formatNumberWithSpaces(result.additional_costs.other_costs_rub) }} руб ({{ getPercentOfCost(result.additional_costs.other_costs_rub, result.cost_price.total.rub) }}%)</span>' +
                    '</div>' +
                    '<div class="detail-item" style="border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 8px;">' +
                        '<span class="detail-label"><strong>Наценка:</strong></span>' +
                        '<span class="detail-value"><strong>{{ ((result.markup - 1) * 100).toFixed(0) }}%</strong></span>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            
            '<!-- Блок с данными по пошлинам -->' +
            '<div v-if="hasCustomsInfo" style="margin-top: 20px; padding: 16px; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px;">' +
                '<h4 style="font-size: 14px; font-weight: 600; color: #1f2937; margin-bottom: 12px;">Справочная информация по пошлинам</h4>' +
                '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 13px;">' +
                    '<div>' +
                        '<span style="color: #6b7280;">ТН ВЭД:</span> ' +
                        '<strong style="color: #1f2937;">{{ result.customs_info.tnved_code || "Не указан" }}</strong>' +
                    '</div>' +
                    '<div>' +
                        '<span style="color: #6b7280;">Пошлина:</span> ' +
                        '<strong style="color: #dc2626;">{{ result.customs_info.duty_rate || "Не указана" }}</strong>' +
                    '</div>' +
                    '<div>' +
                        '<span style="color: #6b7280;">НДС:</span> ' +
                        '<strong style="color: #dc2626;">{{ result.customs_info.vat_rate || "20%" }}</strong>' +
                    '</div>' +
                '</div>' +
                '<div v-if="result.customs_info.certificates && result.customs_info.certificates.length" style="margin-top: 12px;">' +
                    '<div style="color: #6b7280; font-size: 12px; margin-bottom: 4px;">Требуемые документы:</div>' +
                    '<div style="font-size: 12px; color: #059669; font-weight: 500;">' +
                        '{{ result.customs_info.certificates.join(", ") }}' +
                    '</div>' +
                '</div>' +
                '<div v-if="result.customs_calculations" style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">' +
                    '<div style="color: #6b7280; font-size: 12px; margin-bottom: 6px;">Примерные таможенные расходы:</div>' +
                    '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; font-size: 12px;">' +
                        '<div><span style="color: #6b7280;">Пошлина:</span> <strong>${{ result.customs_calculations.duty_amount_usd.toFixed(2) }}</strong></div>' +
                        '<div><span style="color: #6b7280;">НДС:</span> <strong>${{ result.customs_calculations.vat_amount_usd.toFixed(2) }}</strong></div>' +
                        '<div><span style="color: #6b7280;">Всего:</span> <strong style="color: #dc2626;">${{ result.customs_calculations.total_customs_cost_usd.toFixed(2) }}</strong></div>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            
        '<!-- 🔘 БЛОК СЕБЕСТОИМОСТИ ПОД КОНТРАКТ - СЕРЫЙ СТИЛЬ -->' +
        '<div v-show="result" style="margin-top: 20px; padding: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">' +
            '<h4 style="font-size: 14px; font-weight: 600; color: #1f2937; margin-bottom: 12px;">Себестоимость под контракт</h4>' +
            
            '<!-- Проверка наличия данных контракта -->' +
            '<template v-if="result && result.contract_cost">' +
                '<div style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">' +
                    'Логистика: {{ result.contract_cost.logistics_rate_usd }}$/кг, фиксированные расходы: {{ result.contract_cost.fixed_cost_rub.toLocaleString() }} ₽' +
                '</div>' +
                
                '<!-- Информация о пошлинах в контракте -->' +
                '<template v-if="result.customs_info && result.customs_calculations">' +
                    '<div style="font-size: 12px; color: #6b7280; margin-bottom: 12px; padding: 8px; background: #f1f5f9; border-radius: 6px;">' +
                        '<div style="font-weight: 500; margin-bottom: 4px;">Таможенные расходы:</div>' +
                        '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px;">' +
                            '<div>Пошлина: {{ result.customs_info.duty_rate }} (${{ result.customs_calculations.duty_amount_usd.toFixed(2) }})</div>' +
                            '<div>НДС: {{ result.customs_info.vat_rate }} (${{ result.customs_calculations.vat_amount_usd.toFixed(2) }})</div>' +
                            '<div>Всего: ${{ result.customs_calculations.total_customs_cost_usd.toFixed(2) }}</div>' +
                        '</div>' +
                    '</div>' +
                '</template>' +
                
                '<!-- Основные данные контракта -->' +
                '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 13px;">' +
                    '<div>' +
                        '<span style="color: #6b7280;">За единицу:</span> ' +
                        '<strong style="color: #1f2937;">{{ result.contract_cost.per_unit.rub.toLocaleString() }} ₽</strong>' +
                        '<span style="color: #6b7280;"> ({{ result.contract_cost.per_unit.usd.toFixed(2) }}$)</span>' +
                    '</div>' +
                    '<div>' +
                        '<span style="color: #6b7280;">Весь тираж:</span> ' +
                        '<strong style="color: #1f2937;">{{ result.contract_cost.total.rub.toLocaleString() }} ₽</strong>' +
                        '<span style="color: #6b7280;"> ({{ result.contract_cost.total.usd.toFixed(2) }}$)</span>' +
                    '</div>' +
                '</div>' +
                
                '<!-- Разница с обычной себестоимостью -->' +
                '<template v-if="result.cost_difference">' +
                    '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">' +
                        '<div style="color: #6b7280; font-size: 12px; margin-bottom: 6px;">Разница с обычной себестоимостью:</div>' +
                        '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; font-size: 12px;">' +
                            '<div>' +
                                '<span style="color: #6b7280;">За единицу:</span> ' +
                                '<strong :style="result.cost_difference.per_unit.rub >= 0 ? \'color: #dc2626\' : \'color: #059669\'">' +
                                    '{{ result.cost_difference.per_unit.rub >= 0 ? "+" : "" }}{{ result.cost_difference.per_unit.rub.toLocaleString() }} ₽' +
                                '</strong>' +
                            '</div>' +
                            '<div>' +
                                '<span style="color: #6b7280;">Весь тираж:</span> ' +
                                '<strong :style="result.cost_difference.total.rub >= 0 ? \'color: #dc2626\' : \'color: #059669\'">' +
                                    '{{ result.cost_difference.total.rub >= 0 ? "+" : "" }}{{ result.cost_difference.total.rub.toLocaleString() }} ₽' +
                                '</strong>' +
                            '</div>' +
                        '</div>' +
                    '</div>' +
                '</template>' +
            '</template>' +
            
            '<!-- Сообщение об отсутствии данных по пошлинам -->' +
            '<template v-else>' +
                '<div style="font-size: 13px; color: #dc2626; padding: 12px; background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; text-align: center;">' +
                    '<div style="font-weight: 500; margin-bottom: 4px;">⚠️ Расчет под контракт невозможен</div>' +
                    '<div style="font-size: 12px;">Не хватает данных по пошлинам и ТН ВЭД коду.</div>' +
                    '<div style="font-size: 12px; margin-top: 4px; color: #991b1b;">Обратитесь к таможенному брокеру для получения информации.</div>' +
                '</div>' +
            '</template>' +
        '</div>' +
        
        '<!-- БЛОК PROLOGIX - РАСЧЕТ ПО КУБОМЕТРАМ -->' +
        '<div v-if="hasPrologixInfo" style="margin-top: 20px; padding: 16px; background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px;">' +
            '<h4 style="font-size: 14px; font-weight: 600; color: #1f2937; margin-bottom: 12px;">Prologix (доставка по кубометрам)</h4>' +
            
            '<div style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">' +
                'Объем: {{ result.prologix_cost.total_volume_m3 }} м³ × {{ result.prologix_cost.rate_rub_per_m3.toLocaleString() }} руб/м³ = ' +
                '<strong style="color: #059669;">{{ result.prologix_cost.logistics_cost_rub.toLocaleString() }} ₽</strong> логистика' +
            '</div>' +
            
            '<div style="font-size: 12px; color: #6b7280; margin-bottom: 12px; padding: 8px; background: white; border-radius: 6px;">' +
                'Срок доставки: {{ result.prologix_cost.delivery_days_min }}-{{ result.prologix_cost.delivery_days_max }} дней (среднее: {{ result.prologix_cost.delivery_days_avg }} дней)' +
            '</div>' +
            
            '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; font-size: 13px;">' +
                '<div>' +
                    '<span style="color: #6b7280;">За единицу:</span> ' +
                    '<strong style="color: #1f2937;">{{ result.prologix_cost.cost_per_unit_rub.toLocaleString() }} ₽</strong>' +
                    '<span style="color: #6b7280;"> ({{ result.prologix_cost.cost_per_unit_usd.toFixed(2) }}$)</span>' +
                '</div>' +
                '<div>' +
                    '<span style="color: #6b7280;">Весь тираж:</span> ' +
                    '<strong style="color: #1f2937;">{{ result.prologix_cost.total_cost_rub.toLocaleString() }} ₽</strong>' +
                    '<span style="color: #6b7280;"> ({{ result.prologix_cost.total_cost_usd.toFixed(2) }}$)</span>' +
                '</div>' +
            '</div>' +
        '</div>' +
            
            '<!-- Product URL -->' +
            '<div v-if="result.product_url" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #e5e7eb;">' +
                '<a :href="result.product_url" target="_blank" style="color: #2563eb; text-decoration: none;">' +
                    '→ Открыть страницу товара' +
                '</a>' +
            '</div>' +
            
            '<!-- Note: Calculation is automatically saved to database -->' +
        '</div>' +
    '</div>'
};

// Регистрируем компонент глобально
if (typeof window !== 'undefined') {
    window.ResultsDisplay = ResultsDisplay;
}
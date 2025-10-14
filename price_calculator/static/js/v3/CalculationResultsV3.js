/**
 * CalculationResultsV3.js - Детальный экран с итогами расчета и маршрутами
 * 
 * ✅ РЕФАКТОРИНГ: Template вынесен в отдельный файл
 * @see ./templates/calculation-results.template.js
 */

// Импорт template (ES module)
import { CALCULATION_RESULTS_TEMPLATE } from './templates/calculation-results.template.js';

window.CalculationResultsV3 = {
    // ============================================
    // TEMPLATE (вынесен в отдельный файл)
    // ============================================
    template: CALCULATION_RESULTS_TEMPLATE,
    
    props: {
        result: {
            type: Object,
            default: null
        },
        initialRequestData: {
            type: Object,
            default: null
        }
    },
    
    data() {
        return {
            expandedRoutes: {},
            needsCustomParams: false,
            lastRequestData: null,
            showQuickEdit: false,  // Показывать модалку быстрого редактирования
            showCategoryChange: false  // ✅ NEW: Показывать модалку изменения категории
        };
    },
    
    computed: {
        sortedRoutes() {
            if (!this.result?.routes) return [];
            return Object.entries(this.result.routes).map(([key, data]) => ({
                key,
                ...data
            })).sort((a, b) => (a.per_unit || 0) - (b.per_unit || 0));
        }
    },
    
    methods: {
        formatPrice(value) {
            if (value === null || value === undefined) return '0';
            return Number(value).toFixed(2);
        },
        
        toggleRoute(routeKey) {
            this.expandedRoutes[routeKey] = !this.expandedRoutes[routeKey];
        },
        
        // ✅ NEW: Обработчик обновления маршрута из RouteEditorV3
        async handleUpdateRoute(data) {
            console.log('🔄 Пересчет маршрута:', data);
            
            try {
                // Пересчет с кастомными параметрами через PUT API
                const response = await axios.put(
                    `/api/v3/calculations/${this.result.calculation_id}`,
                    {
                        custom_logistics: data.customLogistics
                    }
                );
                
                console.log('✅ Пересчет маршрута выполнен');
                
                // Обновить результаты
                this.$emit('recalculate', response.data);
                
            } catch (error) {
                console.error('❌ Ошибка пересчета маршрута:', error);
                alert('Ошибка пересчета: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        // ✅ NEW: Открыть модалку быстрого редактирования
        openQuickEdit() {
            console.log('⚡ Открытие быстрого редактирования');
            this.showQuickEdit = true;
        },
        
        closeQuickEdit() {
            this.showQuickEdit = false;
        },
        
        handleQuickEditRecalculated(newResult) {
            console.log('✅ Результаты быстрого редактирования получены');
            this.$emit('recalculate', newResult);
        },
        
        // ✅ NEW: Открыть модалку изменения категории
        openCategoryChange() {
            console.log('🏷 Открытие изменения категории');
            this.showCategoryChange = true;
        },
        
        closeCategoryChange() {
            this.showCategoryChange = false;
        },
        
        handleCategoryChangeRecalculated(newResult) {
            console.log('✅ Результаты изменения категории получены');
            this.$emit('recalculate', newResult);
        },
        
        openCustomParams() {
            console.log('🔧 Открытие формы редактирования ставок');
            this.needsCustomParams = true;
            this.lastRequestData = this.initialRequestData;
        },
        
        async applyCustomLogistics(customLogistics) {
            try {
                const v3 = window.useCalculationV3();
                
                const requestData = {
                    ...this.lastRequestData,
                    custom_logistics: customLogistics
                };
                
                console.log('📤 Повторный расчет с кастомными параметрами:', requestData);
                
                const newResult = await v3.calculate(requestData);
                
                this.needsCustomParams = false;
                this.$emit('recalculate', newResult);
                
                console.log('✅ Результат с кастомными параметрами:', newResult);
                
            } catch (error) {
                console.error('❌ Ошибка расчёта с кастомными параметрами:', error);
                alert('Ошибка: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        cancelCustomParams() {
            this.needsCustomParams = false;
        },
        
        newCalculation() {
            this.$emit('new-calculation');
        }
    },
    
};



/**
 * QuickModeV3.js - Быстрый режим расчёта (Position + Calculation)
 * 
 * ✅ РЕФАКТОРИНГ: Template вынесен в отдельный файл
 * @see ./templates/quick-mode.template.js
 */

// Импорт template (ES module)
import { QUICK_MODE_TEMPLATE } from './templates/quick-mode.template.js';

window.QuickModeV3 = {
    // ============================================
    // TEMPLATE (вынесен в отдельный файл)
    // ============================================
    template: QUICK_MODE_TEMPLATE,
    
    
    data() {
        return {
            // Основные поля
            productName: '',
            category: '',
            factoryUrl: '',
            priceYuan: 0,
            quantity: 1000,
            markup: 1.7,
            
            // Режим расчёта
            detailedMode: false,
            
            // Вес (быстрый режим)
            weightKg: 0.2,
            
            // Паккинг (детальный режим)
            packingUnitsPerBox: 0,
            packingBoxWeight: 0,
            packingBoxLength: 0,
            packingBoxWidth: 0,
            packingBoxHeight: 0,
            
            // Состояние
            isCalculating: false,
            availableCategories: [],
            
            // Второй этап (кастомные параметры)
            needsCustomParams: false,
            placeholderRoutes: {},
            lastRequestData: null // Сохраняем данные первого запроса
        };
    },
    
    props: {
        position: {
            type: Object,
            default: null
        }
    },
    
    watch: {
        position: {
            immediate: true,
            handler(newPosition) {
                if (newPosition) {
                    console.log('📥 Получена позиция для расчета:', newPosition);
                    this.fillFromPosition(newPosition);
                    // НЕ запускаем расчет автоматически - пользователь должен ввести количество и наценку
                    console.log('ℹ️ Введите количество и наценку, затем нажмите "Рассчитать"');
                }
            }
        }
    },
    
    async mounted() {
        await this.loadCategories();
    },
    
    
    methods: {
        async loadCategories() {
            try {
                const response = await axios.get(`${window.location.origin}/api/v3/categories`);
                const data = response.data;
                
                // API возвращает массив напрямую
                if (Array.isArray(data)) {
                    this.availableCategories = data.map(c => c.category || c.name || c);
                } else if (data.categories && Array.isArray(data.categories)) {
                    // На случай если структура изменится
                    this.availableCategories = data.categories.map(c => c.category || c.name || c);
                } else {
                    console.warn('⚠️ Неожиданный формат данных категорий:', data);
                    this.availableCategories = [];
                }
                
                console.log('✅ Загружено категорий:', this.availableCategories.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        fillFromPosition(position) {
            // Заполняем поля из позиции
            this.productName = position.name || '';
            this.category = position.category || '';
            this.factoryUrl = position.factory_url || '';
            this.priceYuan = position.price_yuan || 0;
            
            // Если есть паккинг - используем детальный режим
            if (position.packing_units_per_box && position.packing_box_weight) {
                this.detailedMode = true;
                this.packingUnitsPerBox = position.packing_units_per_box;
                this.packingBoxWeight = position.packing_box_weight;
                this.packingBoxLength = position.packing_box_length || 0;
                this.packingBoxWidth = position.packing_box_width || 0;
                this.packingBoxHeight = position.packing_box_height || 0;
            } else if (position.weight_kg) {
                // Иначе используем простой режим
                this.detailedMode = false;
                this.weightKg = position.weight_kg;
            }
            
            console.log('✅ Форма заполнена из позиции');
        },
        
        detectCategory() {
            if (!this.productName || this.productName.length < 2) return;
            
            const nameLower = this.productName.toLowerCase();
            const detected = this.availableCategories.find(cat => 
                nameLower.includes(cat.toLowerCase())
            );
            
            if (detected && detected !== this.category) {
                this.category = detected;
                console.log('✅ Автоопределена категория:', detected);
            }
        },
        
        async calculate() {
            this.isCalculating = true;
            this.result = null;
            this.needsCustomParams = false;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Подготавливаем данные для API
                const requestData = {
                    product_name: this.productName,
                    product_url: this.factoryUrl || '',
                    price_yuan: this.priceYuan,
                    quantity: this.quantity,
                    markup: this.markup,
                    forced_category: this.category || undefined,
                    is_precise_calculation: this.detailedMode
                };
                
                // Добавляем данные упаковки или веса
                if (this.detailedMode) {
                    requestData.packing_units_per_box = this.packingUnitsPerBox;
                    requestData.packing_box_weight = this.packingBoxWeight;
                    requestData.packing_box_length = this.packingBoxLength;
                    requestData.packing_box_width = this.packingBoxWidth;
                    requestData.packing_box_height = this.packingBoxHeight;
                } else {
                    requestData.weight_kg = this.weightKg;
                }
                
                // Сохраняем данные для второго этапа
                this.lastRequestData = requestData;
                
                console.log('📤 Отправка данных на расчет:', requestData);
                
                // Выполняем расчёт
                const result = await v3.calculate(requestData);
                
                // Проверяем нужны ли кастомные параметры
                if (result.needs_custom_params) {
                    console.log('⚠️ Требуются кастомные параметры');
                    this.needsCustomParams = true;
                    this.placeholderRoutes = result.routes || {};
                    this.category = result.category;
                } else {
                    // Эмитим событие для перехода на страницу результатов
                    console.log('✅ Расчёт завершен, переход к результатам');
                    this.$emit('calculation-complete', {
                        result: result,
                        requestData: requestData
                    });
                }
                
            } catch (error) {
                console.error('❌ Ошибка расчёта:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось выполнить расчёт';
                alert(`Ошибка: ${errorMsg}`);
            } finally {
                this.isCalculating = false;
            }
        },
        
        async applyCustomLogistics(customLogistics) {
            this.isCalculating = true;
            
            try {
                const v3 = window.useCalculationV3();
                
                // Добавляем кастомные параметры к исходному запросу
                const requestData = {
                    ...this.lastRequestData,
                    custom_logistics: customLogistics
                };
                
                console.log('📤 Повторный расчет с кастомными параметрами:', requestData);
                
                // Выполняем расчёт с кастомными параметрами
                const result = await v3.calculate(requestData);
                
                // Скрываем форму кастомных параметров и эмитим результат
                this.needsCustomParams = false;
                console.log('✅ Результат с кастомными параметрами, переход к результатам');
                this.$emit('calculation-complete', {
                    result: result,
                    requestData: requestData
                });
                
            } catch (error) {
                console.error('❌ Ошибка расчёта с кастомными параметрами:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось выполнить расчёт';
                alert(`Ошибка: ${errorMsg}`);
            } finally {
                this.isCalculating = false;
            }
        },
        
        openCustomParams() {
            // Открываем форму кастомных параметров с текущими результатами
            console.log('🔧 Открытие формы редактирования ставок');
            this.needsCustomParams = true;
            this.placeholderRoutes = this.result.routes || {};
            this.lastRequestData = {
                product_name: this.productName,
                price_yuan: this.priceYuan,
                quantity: this.quantity,
                markup: this.markup,
                category: this.category,
                is_precise_calculation: this.detailedMode
            };
            
            if (this.detailedMode) {
                this.lastRequestData.packing_box_length = this.packingBoxLength;
                this.lastRequestData.packing_box_width = this.packingBoxWidth;
                this.lastRequestData.packing_box_height = this.packingBoxHeight;
                this.lastRequestData.packing_box_weight = this.packingBoxWeight;
                this.lastRequestData.packing_units_per_box = this.packingUnitsPerBox;
            } else {
                this.lastRequestData.weight_kg = this.weightKg;
            }
        },
        
        cancelCustomParams() {
            this.needsCustomParams = false;
            this.placeholderRoutes = {};
        },
        
        reset() {
            this.result = null;
            this.productName = '';
            this.factoryUrl = '';
            this.priceYuan = 0;
            this.quantity = 1000;
            this.weightKg = 0.2;
            this.markup = 1.7;
            this.expandedRoutes = {};
        },
        
        toggleRoute(key) {
            // Vue 3 не требует $set, просто изменяем напрямую
            this.expandedRoutes[key] = !this.expandedRoutes[key];
        },
        
        formatRouteName(key) {
            const names = {
                highway_rail: 'ЖД',
                highway_air: 'Авиа',
                highway_contract: 'Контракт',
                prologix: 'Prologix',
                sea_container: 'Море'
            };
            return names[key] || key;
        },
        
        formatPrice(price) {
            if (price === null || price === undefined || isNaN(price)) return '0';
            return Number(price).toLocaleString('ru-RU', {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2
            });
        }
    }
};


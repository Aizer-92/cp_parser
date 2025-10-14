/**
 * PositionsListV3.js - Список всех позиций товаров
 * 
 * ✅ РЕФАКТОРИНГ: Template вынесен в отдельный файл
 * @see ./templates/positions-list.template.js
 */

// Импорт template (ES module)
import { POSITIONS_LIST_TEMPLATE } from './templates/positions-list.template.js';

window.PositionsListV3 = {
    // ============================================
    // TEMPLATE (вынесен в отдельный файл)
    // ============================================
    template: POSITIONS_LIST_TEMPLATE,
    
    
    data() {
        return {
            positions: [],
            categories: [],
            isLoading: false,
            searchQuery: '',
            categoryFilter: '',
            currentPage: 1,
            itemsPerPage: 12,
            totalPositions: 0,
            showForm: false,
            editingPosition: null
        };
    },
    
    computed: {
        filteredPositions() {
            let filtered = this.positions;
            
            // Поиск по названию или категории
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(p =>
                    p.name.toLowerCase().includes(query) ||
                    (p.category && p.category.toLowerCase().includes(query)) ||
                    (p.description && p.description.toLowerCase().includes(query))
                );
            }
            
            // Фильтр по категории
            if (this.categoryFilter) {
                filtered = filtered.filter(p => p.category === this.categoryFilter);
            }
            
            return filtered;
        },
        
        totalPages() {
            return Math.ceil(this.totalPositions / this.itemsPerPage);
        }
    },
    
    async mounted() {
        await this.loadPositions();
        await this.loadCategories();
    },
    
    methods: {
        async loadPositions() {
            this.isLoading = true;
            try {
                const positionsAPI = window.usePositionsV3();
                const response = await positionsAPI.getPositions(
                    (this.currentPage - 1) * this.itemsPerPage,
                    this.itemsPerPage
                );
                
                // API возвращает массив напрямую
                this.positions = Array.isArray(response) ? response : (response.items || []);
                this.totalPositions = response.total || this.positions.length;
                
                console.log('✅ Загружено позиций:', this.positions.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки позиций:', error);
                alert('Не удалось загрузить позиции');
            } finally {
                this.isLoading = false;
            }
        },
        
        async loadCategories() {
            try {
                // Используем прямой запрос к API
                const response = await axios.get(`${window.location.origin}/api/v3/categories`);
                const data = response.data;
                
                // Извлекаем уникальные категории
                const categories = data.categories || [];
                this.categories = [...new Set(categories.map(c => c.category || c.name || c))];
                
                console.log('✅ Загружено категорий:', this.categories.length);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        createPosition() {
            this.editingPosition = null;
            this.showForm = true;
        },
        
        openPosition(id) {
            // TODO: Открыть детали позиции
            console.log('Открыть позицию:', id);
            alert(`Просмотр позиции #${id} будет реализован в следующем этапе`);
        },
        
        editPosition(id) {
            const position = this.positions.find(p => p.id === id);
            if (position) {
                this.editingPosition = position;
                this.showForm = true;
            }
        },
        
        closeForm() {
            this.showForm = false;
            this.editingPosition = null;
        },
        
        async onPositionSaved() {
            await this.loadPositions();
        },
        
        async onCalculateRoutes(position) {
            console.log('🚀 Автоматический расчет для позиции:', position);
            
            try {
                const v3 = window.useCalculationV3();
                
                // Проверяем наличие всех данных для детального расчета
                const hasFullPacking = position.packing_units_per_box && 
                                      position.packing_box_weight && 
                                      position.packing_units_per_box > 0 && 
                                      position.packing_box_weight > 0;
                
                const hasWeight = position.weight_kg && position.weight_kg > 0;
                
                // Формируем запрос для расчета
                const requestData = {
                    product_name: position.name,
                    price_yuan: position.price_yuan,
                    quantity: 1000, // Значение по умолчанию
                    markup: 1.7, // Значение по умолчанию
                    category: position.category || '',
                    is_precise_calculation: hasFullPacking
                };
                
                // Добавляем данные в зависимости от режима
                if (hasFullPacking) {
                    requestData.packing_units_per_box = position.packing_units_per_box;
                    requestData.packing_box_weight = position.packing_box_weight;
                    requestData.packing_box_length = position.packing_box_length || 0;
                    requestData.packing_box_width = position.packing_box_width || 0;
                    requestData.packing_box_height = position.packing_box_height || 0;
                    // weight_kg рассчитается автоматически
                } else if (hasWeight) {
                    requestData.weight_kg = position.weight_kg;
                } else {
                    // Если нет ни паккинга, ни веса - используем вес по умолчанию
                    alert('⚠️ В позиции не указан вес или паккинг. Используется вес по умолчанию 0.2 кг');
                    requestData.weight_kg = 0.2;
                }
                
                console.log('📤 Запрос на расчет:', requestData);
                
                // Выполняем расчет
                const result = await v3.calculate(requestData);
                
                console.log('✅ Расчет завершен, переход к результатам');
                
                // Эмитим событие для перехода к результатам
                this.$emit('calculation-complete', {
                    result: result,
                    requestData: requestData
                });
                
            } catch (error) {
                console.error('❌ Ошибка расчёта:', error);
                const detail = error.response?.data?.detail;
                const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
                alert('Ошибка расчета: ' + message);
            }
        },
        
        confirmDelete(id) {
            if (!confirm('Удалить эту позицию?')) return;
            this.deletePosition(id);
        },
        
        async deletePosition(id) {
            try {
                const positionsAPI = window.usePositionsV3();
                await positionsAPI.deletePosition(id);
                
                console.log('✅ Позиция удалена:', id);
                await this.loadPositions();
            } catch (error) {
                console.error('❌ Ошибка удаления позиции:', error);
                alert('Не удалось удалить позицию');
            }
        },
        
        async prevPage() {
            if (this.currentPage > 1) {
                this.currentPage--;
                await this.loadPositions();
            }
        },
        
        async nextPage() {
            if (this.currentPage < this.totalPages) {
                this.currentPage++;
                await this.loadPositions();
            }
        },
        
        truncate(text, length) {
            if (!text) return '';
            return text.length > length ? text.substring(0, length) + '...' : text;
        },
        
        formatDate(dateString) {
            if (!dateString) return '';
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        }
    }
};

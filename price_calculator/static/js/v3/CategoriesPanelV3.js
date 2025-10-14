/**
 * CategoriesPanelV3.js - Управление категориями товаров
 * 
 * ✅ РЕФАКТОРИНГ: Template вынесен в отдельный файл
 * @see ./templates/categories-panel.template.js
 */

// Импорт template (ES module)
import { CATEGORIES_PANEL_TEMPLATE } from './templates/categories-panel.template.js';

window.CategoriesPanelV3 = {
    // ============================================
    // TEMPLATE (вынесен в отдельный файл)
    // ============================================
    template: CATEGORIES_PANEL_TEMPLATE,
    
    name: 'CategoriesPanelV3',
    
    data() {
        return {
            categories: [],
            statistics: {},
            searchQuery: '',
            isLoading: false,
            editingCategory: null,
            showEditForm: false,
            showAddForm: false,
            
            // Новая категория
            newCategory: {
                category: '',
                material: '',
                tnved_code: '',
                density: null,
                duty_type: 'percent',
                duty_rate: '',
                specific_rate: '',
                ad_valorem_rate: '',
                vat_rate: '',
                certificates: [],
                rates: {
                    rail_base: null,
                    air_base: null
                }
            }
        };
    },
    
    computed: {
        filteredCategories() {
            if (!this.searchQuery) {
                return this.categories;
            }
            const query = this.searchQuery.toLowerCase();
            return this.categories.filter(cat => 
                cat.category.toLowerCase().includes(query) ||
                (cat.tnved_code && cat.tnved_code.includes(query))
            );
        },
        
        currentForm() {
            return this.showEditForm ? this.editingCategory : this.newCategory;
        }
    },
    
    mounted() {
        this.loadCategories();
        this.loadStatistics();
    },
    
    methods: {
        async loadCategories() {
            this.isLoading = true;
            try {
                const response = await axios.get('/api/v3/categories');
                console.log('✅ Загружено категорий (V3):', response.data.length);
                this.categories = response.data;
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            } finally {
                this.isLoading = false;
            }
        },
        
        async loadStatistics() {
            try {
                const response = await axios.get('/api/v3/categories/statistics');
                console.log('✅ Загружена статистика (V3):', response.data.length);
                this.statistics = response.data.reduce((acc, stat) => {
                    acc[stat.category] = stat;
                    return acc;
                }, {});
            } catch (error) {
                console.error('❌ Ошибка загрузки статистики:', error);
            }
        },
        
        getStats(categoryName) {
            return this.statistics[categoryName] || null;
        },
        
        formatPrice(price) {
            if (!price) return '—';
            return price.toFixed(2) + ' ¥';
        },
        
        startAdd() {
            this.newCategory = {
                category: '',
                material: '',
                tnved_code: '',
                density: null,
                duty_type: 'percent',
                duty_rate: '',
                specific_rate: '',
                ad_valorem_rate: '',
                vat_rate: '',
                certificates: [],
                rates: {
                    rail_base: null,
                    air_base: null
                }
            };
            this.showAddForm = true;
            this.showEditForm = false;
        },
        
        startEdit(category) {
            const categoryClone = JSON.parse(JSON.stringify(category));
            if (!categoryClone.id && category.id) {
                categoryClone.id = category.id;
            }
            if (!categoryClone.rates) {
                categoryClone.rates = {
                    rail_base: null,
                    air_base: null
                };
            }
            this.editingCategory = categoryClone;
            this.showEditForm = true;
            this.showAddForm = false;
            console.log('🔧 Редактирование:', this.editingCategory.category);
        },
        
        cancelEdit() {
            this.showEditForm = false;
            this.showAddForm = false;
            this.editingCategory = null;
        },
        
        async saveCategory() {
            console.log('💾 Сохранение категории:', this.editingCategory);
            if (!this.editingCategory.id) {
                alert('❌ Ошибка: ID категории не найден');
                return;
            }
            try {
                await axios.put(`/api/v3/categories/${this.editingCategory.id}`, this.editingCategory);
                this.cancelEdit();
                this.loadCategories();
                this.loadStatistics();
            } catch (error) {
                console.error('❌ Ошибка сохранения:', error);
                alert('Ошибка: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        async addCategory() {
            if (!this.newCategory.category || !this.newCategory.rates.rail_base || !this.newCategory.rates.air_base) {
                alert('⚠️ Заполните обязательные поля');
                return;
            }
            try {
                await axios.post('/api/v3/categories', this.newCategory);
                this.cancelEdit();
                this.loadCategories();
            } catch (error) {
                console.error('❌ Ошибка добавления:', error);
                alert('Ошибка: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        async deleteCategory(category) {
            if (!confirm(`Удалить категорию "${category.category}"?`)) {
                return;
            }
            try {
                await axios.delete(`/api/v3/categories/${category.id}`);
                this.loadCategories();
                this.loadStatistics();
            } catch (error) {
                console.error('❌ Ошибка удаления:', error);
                alert('Ошибка: ' + (error.response?.data?.detail || error.message));
            }
        },
        
        getCustomsInfo(category) {
            const customs = {
                duty_rate: null,
                vat_rate: null,
                duty_type: null,
                certificates: []
            };
            if (category.customs_info) {
                customs.duty_rate = category.customs_info.duty_rate;
                customs.vat_rate = category.customs_info.vat_rate;
                customs.duty_type = category.customs_info.duty_type;
                customs.certificates = category.customs_info.certificates || [];
            }
            if (!customs.duty_rate && category.duty_rate) {
                customs.duty_rate = category.duty_rate;
            }
            if (!customs.vat_rate && category.vat_rate) {
                customs.vat_rate = category.vat_rate;
            }
            if (!customs.duty_type && category.duty_type) {
                customs.duty_type = category.duty_type;
            }
            if (!customs.certificates.length && category.certificates) {
                customs.certificates = Array.isArray(category.certificates) 
                    ? category.certificates 
                    : category.certificates.split(',').map(c => c.trim());
            }
            if (customs.duty_rate || customs.vat_rate) {
                return customs;
            }
            return null;
        }
    }
};


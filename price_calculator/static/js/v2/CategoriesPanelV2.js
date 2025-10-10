/**
 * 📦 CATEGORIES PANEL V2 COMPONENT
 * Управление категориями товаров для V2 интерфейса
 * Дизайн в стиле RouteDetailsV2
 */

window.CategoriesPanelV2 = {
    name: 'CategoriesPanelV2',
    
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
                duty_type: 'percent',  // percent, specific, combined
                duty_rate: '',  // Для percent и combined (ad valorem)
                specific_rate: '',  // Для specific и combined
                ad_valorem_rate: '',  // Для combined
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
        
        // Текущая форма (для редактирования или добавления)
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
                const response = await axios.get('/api/categories');
                console.log('✅ Загружено категорий:', response.data.length);
                this.categories = response.data;
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            } finally {
                this.isLoading = false;
            }
        },
        
        async loadStatistics() {
            try {
                const response = await axios.get('/api/categories/statistics');
                console.log('✅ Загружена статистика:', response.data.length);
                // Преобразуем в Map для быстрого доступа
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
                await axios.put(`/api/categories/${this.editingCategory.id}`, this.editingCategory);
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
                await axios.post('/api/categories', this.newCategory);
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
                await axios.delete(`/api/categories/${category.id}`);
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
    },
    
    template: `
        <div>
            <!-- Header -->
            <div style="margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <input 
                        v-model="searchQuery" 
                        type="text" 
                        placeholder="Поиск по названию или ТН ВЭД..." 
                        style="padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 6px; width: 400px; font-size: 14px;"
                    />
                    <button 
                        @click="startAdd" 
                        style="padding: 10px 20px; background: #111827; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 14px;"
                    >
                        Добавить категорию
                    </button>
                </div>
            </div>
            
            <!-- Loading -->
            <div v-if="isLoading" style="display: flex; flex-direction: column; align-items: center; padding: 60px;">
                <div style="width: 40px; height: 40px; border: 3px solid #e5e7eb; border-top-color: #111827; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
                <p style="margin-top: 16px; color: #6b7280; font-size: 14px;">Загрузка...</p>
            </div>
            
            <!-- Add/Edit Form -->
            <div v-else-if="showAddForm || showEditForm" style="background: #f9fafb; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 20px;">
                    {{ showAddForm ? 'Новая категория' : ('Редактирование: ' + (currentForm.category || '')) }}
                </h3>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">Название *</label>
                        <input 
                            v-model="currentForm.category" 
                            type="text" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">Материал</label>
                        <input 
                            v-model="currentForm.material" 
                            type="text" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">ТН ВЭД</label>
                        <input 
                            v-model="currentForm.tnved_code" 
                            type="text" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">Плотность (кг/м³)</label>
                        <input 
                            v-model.number="currentForm.density" 
                            type="number" 
                            step="0.1" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">ЖД ($/кг) *</label>
                        <input 
                            v-model.number="currentForm.rates.rail_base" 
                            type="number" 
                            step="0.1" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">Авиа ($/кг) *</label>
                        <input 
                            v-model.number="currentForm.rates.air_base" 
                            type="number" 
                            step="0.1" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                </div>
                
                <!-- Тип пошлины -->
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">Тип пошлины</label>
                    <select 
                        v-model="currentForm.duty_type" 
                        style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; background: white;"
                    >
                        <option value="percent">Процентные (только %)</option>
                        <option value="specific">Весовые (только EUR/кг)</option>
                        <option value="combined">Комбинированные (% ИЛИ EUR/кг)</option>
                    </select>
                </div>
                
                <!-- Поля пошлин в зависимости от типа -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
                    <!-- Процентная пошлина (percent или combined) -->
                    <div v-if="currentForm.duty_type === 'percent' || currentForm.duty_type === 'combined'">
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">
                            {{ currentForm.duty_type === 'combined' ? 'Процентная пошлина' : 'Пошлина' }}
                        </label>
                        <input 
                            v-model="currentForm.duty_type === 'combined' ? currentForm.ad_valorem_rate : currentForm.duty_rate" 
                            type="text" 
                            placeholder="10%" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                    
                    <!-- Весовая пошлина (specific или combined) -->
                    <div v-if="currentForm.duty_type === 'specific' || currentForm.duty_type === 'combined'">
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">
                            Весовая пошлина 
                            <span style="font-size: 12px; color: #6b7280;">(EUR/кг)</span>
                        </label>
                        <input 
                            v-model.number="currentForm.specific_rate" 
                            type="number" 
                            step="0.1"
                            min="0"
                            placeholder="2.2" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                    
                    <!-- НДС (всегда показываем) -->
                    <div>
                        <label style="display: block; margin-bottom: 6px; font-size: 13px; font-weight: 500; color: #374151;">НДС</label>
                        <input 
                            v-model="currentForm.vat_rate" 
                            type="text" 
                            placeholder="20%" 
                            style="width: 100%; padding: 9px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;"
                        />
                    </div>
                </div>
                
                <!-- Подсказка по типу пошлины -->
                <div v-if="currentForm.duty_type" style="background: #f0f9ff; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 12px; color: #0369a1;">
                    <div v-if="currentForm.duty_type === 'percent'">
                        <strong>Процентные пошлины:</strong> Рассчитываются как процент от таможенной стоимости (например, 10% от стоимости товара + логистика).
                    </div>
                    <div v-if="currentForm.duty_type === 'specific'">
                        <strong>Весовые пошлины:</strong> Рассчитываются по весу товара (например, 2.2 EUR за каждый килограмм). Используется для текстиля ТН ВЭД 6307.
                    </div>
                    <div v-if="currentForm.duty_type === 'combined'">
                        <strong>Комбинированные пошлины:</strong> Рассчитываются оба варианта (процент И вес), применяется БОЛЬШАЯ. Используется для одежды и текстиля.
                    </div>
                </div>
                
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button @click="cancelEdit" style="padding: 10px 20px; background: #6b7280; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 14px;">Отмена</button>
                    <button @click="showAddForm ? addCategory() : saveCategory()" style="padding: 10px 20px; background: #111827; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500; font-size: 14px;">{{ showAddForm ? 'Добавить' : 'Сохранить' }}</button>
                </div>
            </div>
            
            <!-- Categories List -->
            <div v-else>
                <div v-for="cat in filteredCategories" :key="cat.id" style="background: #f9fafb; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <!-- Заголовок категории -->
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                        <div>
                            <div style="font-size: 15px; font-weight: 600; color: #111827;">{{ cat.category }}</div>
                            <div v-if="cat.material" style="font-size: 13px; color: #6b7280; margin-top: 2px;">{{ cat.material }}</div>
                        </div>
                        <div style="display: flex; gap: 8px;">
                            <button @click="startEdit(cat)" style="padding: 6px 14px; background: white; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; font-size: 13px; color: #374151;">Изменить</button>
                            <button @click="deleteCategory(cat)" style="padding: 6px 14px; background: white; border: 1px solid #ef4444; color: #ef4444; border-radius: 6px; cursor: pointer; font-size: 13px;">Удалить</button>
                        </div>
                    </div>
                    
                    <!-- Данные категории -->
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px;">
                        <div style="background: white; border-radius: 6px; padding: 10px;">
                            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">ТН ВЭД</div>
                            <div style="font-size: 13px; font-weight: 600; color: #111827; font-family: monospace;">{{ cat.tnved_code || '—' }}</div>
                        </div>
                        <div style="background: white; border-radius: 6px; padding: 10px;">
                            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">ЖД</div>
                            <div style="font-size: 13px; font-weight: 600; color: #111827;">{{ cat.rates?.rail_base || '—' }} $/кг</div>
                        </div>
                        <div style="background: white; border-radius: 6px; padding: 10px;">
                            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">Авиа</div>
                            <div style="font-size: 13px; font-weight: 600; color: #111827;">{{ cat.rates?.air_base || '—' }} $/кг</div>
                        </div>
                        <div style="background: white; border-radius: 6px; padding: 10px;">
                            <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">
                                Тип пошлины
                            </div>
                            <div style="font-size: 12px; font-weight: 600; color: #111827;">
                                <span v-if="getCustomsInfo(cat)?.duty_type === 'combined'" style="color: #059669;">
                                    Комбинир.
                                </span>
                                <span v-else-if="getCustomsInfo(cat)?.duty_type === 'specific'" style="color: #0369a1;">
                                    Весовые
                                </span>
                                <span v-else style="color: #6b7280;">
                                    Процент
                                </span>
                            </div>
                            <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">
                                {{ getCustomsInfo(cat)?.duty_rate || '—' }} / НДС {{ getCustomsInfo(cat)?.vat_rate || '—' }}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Статистика цен -->
                    <div v-if="getStats(cat.category)" style="border-top: 1px solid #e5e7eb; padding-top: 12px;">
                        <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 8px;">Статистика цен (из истории расчетов)</div>
                        <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;">
                            <div style="background: white; border-radius: 6px; padding: 8px;">
                                <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Расчетов</div>
                                <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ getStats(cat.category).count }}</div>
                            </div>
                            <div style="background: white; border-radius: 6px; padding: 8px;">
                                <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Мин</div>
                                <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).min_price) }}</div>
                            </div>
                            <div style="background: white; border-radius: 6px; padding: 8px;">
                                <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Макс</div>
                                <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).max_price) }}</div>
                            </div>
                            <div style="background: white; border-radius: 6px; padding: 8px;">
                                <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Средняя</div>
                                <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).avg_price) }}</div>
                            </div>
                            <div v-if="getStats(cat.category).median_price" style="background: white; border-radius: 6px; padding: 8px;">
                                <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Медиана</div>
                                <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).median_price) }}</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div v-if="filteredCategories.length === 0" style="padding: 60px; text-align: center; color: #6b7280;">
                    Категории не найдены
                </div>
            </div>
        </div>
        
        <style>
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        </style>
    `
};

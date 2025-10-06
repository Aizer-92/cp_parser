/**
 * 📦 CATEGORIES PANEL COMPONENT
 * Управление категориями товаров
 */

const CategoriesPanel = {
    name: 'CategoriesPanel',
    
    data: function() {
        return {
            categories: [],
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
                rates: {
                    rail_base: null,
                    air_base: null
                }
            }
        }
    },
    
    computed: {
        filteredCategories: function() {
            if (!this.searchQuery) {
                return this.categories;
            }
            var query = this.searchQuery.toLowerCase();
            return this.categories.filter(function(cat) {
                return cat.category.toLowerCase().includes(query) ||
                       (cat.tnved_code && cat.tnved_code.includes(query));
            });
        }
    },
    
    mounted: function() {
        this.loadCategories();
    },
    
    methods: {
        loadCategories: function() {
            var self = this;
            self.isLoading = true;
            
            axios.get('/api/categories')
                .then(function(response) {
                    console.log('🔍 RAW API RESPONSE:', response.data);
                    console.log('🔍 Тип response.data:', typeof response.data, Array.isArray(response.data));
                    
                    // Проверяем первый элемент ДО присвоения
                    if (response.data && response.data.length > 0) {
                        console.log('🔍 Первый элемент из API:', response.data[0]);
                        console.log('🔍 ID в первом элементе:', response.data[0].id);
                        console.log('🔍 Все ключи первого элемента:', Object.keys(response.data[0]));
                    }
                    
                    self.categories = response.data;
                    console.log('✅ Загружено категорий:', self.categories.length);
                    
                    // Проверяем ПОСЛЕ присвоения
                    if (self.categories.length > 0) {
                        console.log('Первая категория ПОСЛЕ:', self.categories[0]);
                        console.log('ID первой категории ПОСЛЕ:', self.categories[0].id);
                    }
                })
                .catch(function(error) {
                    console.error('❌ Ошибка загрузки категорий:', error);
                    alert('Ошибка загрузки категорий');
                })
                .finally(function() {
                    self.isLoading = false;
                });
        },
        
        startAdd: function() {
            this.newCategory = {
                category: '',
                material: '',
                tnved_code: '',
                density: null,
                rates: {
                    rail_base: null,
                    air_base: null
                }
            };
            this.showAddForm = true;
            this.showEditForm = false;
        },
        
        startEdit: function(category) {
            // Глубокая копия с явным сохранением ID
            var categoryClone = JSON.parse(JSON.stringify(category));
            
            // КРИТИЧНО: Убеждаемся что ID скопирован
            if (!categoryClone.id && category.id) {
                categoryClone.id = category.id;
            }
            
            this.editingCategory = categoryClone;
            this.showEditForm = true;
            this.showAddForm = false;
            
            console.log('🔧 Редактирование категории:', this.editingCategory.category);
            console.log('🔧 ID категории:', this.editingCategory.id, 'тип:', typeof this.editingCategory.id);
            console.log('🔧 Оригинальный ID:', category.id, 'тип:', typeof category.id);
        },
        
        cancelEdit: function() {
            this.showEditForm = false;
            this.showAddForm = false;
            this.editingCategory = null;
        },
        
        saveCategory: function() {
            var self = this;
            
            console.log('Сохранение категории:', this.editingCategory);
            console.log('ID категории:', this.editingCategory.id);
            
            if (!this.editingCategory.id) {
                alert('Ошибка: ID категории не найден. Категория: ' + JSON.stringify(this.editingCategory));
                return;
            }
            
            axios.put('/api/categories/' + this.editingCategory.id, this.editingCategory)
                .then(function(response) {
                    alert('✅ Категория сохранена!');
                    self.cancelEdit();
                    self.loadCategories();
                })
                .catch(function(error) {
                    console.error('❌ Ошибка сохранения:', error);
                    alert('Ошибка сохранения: ' + (error.response?.data?.detail || error.message));
                });
        },
        
        addCategory: function() {
            var self = this;
            
            if (!this.newCategory.category || !this.newCategory.rates.rail_base || !this.newCategory.rates.air_base) {
                alert('Заполните обязательные поля: название, ставки ЖД и Авиа');
                return;
            }
            
            axios.post('/api/categories', this.newCategory)
                .then(function(response) {
                    alert('✅ Категория добавлена!');
                    self.cancelEdit();
                    self.loadCategories();
                })
                .catch(function(error) {
                    console.error('❌ Ошибка добавления:', error);
                    alert('Ошибка добавления: ' + (error.response?.data?.detail || error.message));
                });
        },
        
        deleteCategory: function(category) {
            console.log('🗑️ Удаление категории:', category.category);
            console.log('🗑️ ID категории:', category.id, 'тип:', typeof category.id);
            console.log('🗑️ Полный объект:', JSON.stringify(category));
            
            if (!category.id) {
                alert('Ошибка: ID категории не найден!\n\nОбъект: ' + JSON.stringify(category, null, 2));
                return;
            }
            
            if (!confirm('Удалить категорию "' + category.category + '"?')) {
                return;
            }
            
            var self = this;
            var categoryId = category.id;
            console.log('🗑️ Отправляем DELETE запрос для ID:', categoryId);
            
            axios.delete('/api/categories/' + categoryId)
                .then(function() {
                    alert('✅ Категория удалена');
                    self.loadCategories();
                })
                .catch(function(error) {
                    console.error('❌ Ошибка удаления:', error);
                    alert('Ошибка удаления: ' + (error.response?.data?.detail || error.message));
                });
        },
        
        getCustomsInfo: function(category) {
            // Пошлины могут быть в разных местах:
            // 1. В customs_info (новый формат)
            // 2. Напрямую в категории (старый формат)
            // 3. В поле duty_rate/vat_rate
            
            var customs = {
                duty_rate: null,
                vat_rate: null,
                duty_type: null,
                certificates: []
            };
            
            // Проверяем customs_info
            if (category.customs_info) {
                customs.duty_rate = category.customs_info.duty_rate;
                customs.vat_rate = category.customs_info.vat_rate;
                customs.duty_type = category.customs_info.duty_type;
                customs.certificates = category.customs_info.certificates || [];
            }
            
            // Fallback на прямые поля
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
                    : category.certificates.split(',').map(function(c) { return c.trim(); });
            }
            
            // Возвращаем только если есть хоть какие-то данные
            if (customs.duty_rate || customs.vat_rate) {
                return customs;
            }
            
            return null;
        }
    },
    
    template:
        '<div class="categories-panel-content">' +
            '<!-- Header -->' +
            '<div class="panel-header-row">' +
                '<h3 class="panel-title">Управление категориями товаров</h3>' +
                '<div class="panel-actions">' +
                    '<input v-model="searchQuery" type="text" placeholder="Поиск по названию или ТН ВЭД..." class="search-input-field" />' +
                    '<button @click="startAdd" class="btn-primary">+ Добавить категорию</button>' +
                '</div>' +
            '</div>' +
            
            '<!-- Loading -->' +
            '<div v-if="isLoading" class="loading-container">' +
                '<div class="spinner-loader"></div>' +
                '<p>Загрузка категорий...</p>' +
            '</div>' +
            
            '<!-- Add Form -->' +
            '<div v-else-if="showAddForm" class="form-card">' +
                '<div class="form-card-header">' +
                    '<h4>Новая категория</h4>' +
                    '<button @click="cancelEdit" class="btn-close-form">✖</button>' +
                '</div>' +
                '<div class="form-card-body">' +
                    '<div class="form-row-grid">' +
                        '<div class="form-group-item">' +
                            '<label>Название категории *</label>' +
                            '<input v-model="newCategory.category" type="text" class="input-text" />' +
                        '</div>' +
                        '<div class="form-group-item">' +
                            '<label>Материал</label>' +
                            '<input v-model="newCategory.material" type="text" class="input-text" />' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-row-grid">' +
                        '<div class="form-group-item">' +
                            '<label>Код ТН ВЭД</label>' +
                            '<input v-model="newCategory.tnved_code" type="text" class="input-text" />' +
                        '</div>' +
                        '<div class="form-group-item">' +
                            '<label>Плотность (кг/м³)</label>' +
                            '<input v-model.number="newCategory.density" type="number" step="0.1" class="input-text" />' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-row-grid">' +
                        '<div class="form-group-item">' +
                            '<label>Ставка ЖД ($/кг) *</label>' +
                            '<input v-model.number="newCategory.rates.rail_base" type="number" step="0.1" class="input-text" />' +
                        '</div>' +
                        '<div class="form-group-item">' +
                            '<label>Ставка Авиа ($/кг) *</label>' +
                            '<input v-model.number="newCategory.rates.air_base" type="number" step="0.1" class="input-text" />' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-actions-row">' +
                        '<button @click="addCategory" class="btn-save">Добавить</button>' +
                        '<button @click="cancelEdit" class="btn-cancel-action">Отмена</button>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            
            '<!-- Edit Form -->' +
            '<div v-else-if="showEditForm && editingCategory" class="form-card">' +
                '<div class="form-card-header">' +
                    '<h4>Редактирование: {{ editingCategory.category }}</h4>' +
                    '<button @click="cancelEdit" class="btn-close-form">✖</button>' +
                '</div>' +
                '<div class="form-card-body">' +
                    '<div class="form-row-grid">' +
                        '<div class="form-group-item">' +
                            '<label>Название</label>' +
                            '<input v-model="editingCategory.category" type="text" class="input-text" />' +
                        '</div>' +
                        '<div class="form-group-item">' +
                            '<label>Материал</label>' +
                            '<input v-model="editingCategory.material" type="text" class="input-text" />' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-row-grid">' +
                        '<div class="form-group-item">' +
                            '<label>Код ТН ВЭД</label>' +
                            '<input v-model="editingCategory.tnved_code" type="text" class="input-text" />' +
                        '</div>' +
                        '<div class="form-group-item">' +
                            '<label>Плотность (кг/м³)</label>' +
                            '<input v-model.number="editingCategory.density" type="number" step="0.1" class="input-text" />' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-row-grid">' +
                        '<div class="form-group-item">' +
                            '<label>Ставка ЖД ($/кг)</label>' +
                            '<input v-model.number="editingCategory.rates.rail_base" type="number" step="0.1" class="input-text" />' +
                        '</div>' +
                        '<div class="form-group-item">' +
                            '<label>Ставка Авиа ($/кг)</label>' +
                            '<input v-model.number="editingCategory.rates.air_base" type="number" step="0.1" class="input-text" />' +
                        '</div>' +
                    '</div>' +
                    '<div class="form-actions-row">' +
                        '<button @click="saveCategory" class="btn-save">Сохранить</button>' +
                        '<button @click="cancelEdit" class="btn-cancel-action">Отмена</button>' +
                    '</div>' +
                '</div>' +
            '</div>' +
            
            '<!-- Categories Table -->' +
            '<div v-else class="table-container">' +
                '<table class="data-table">' +
                    '<thead>' +
                        '<tr>' +
                            '<th>Категория</th>' +
                            '<th>Материал</th>' +
                            '<th>ТН ВЭД</th>' +
                            '<th>ЖД ($/кг)</th>' +
                            '<th>Авиа ($/кг)</th>' +
                            '<th>Пошлина</th>' +
                            '<th>НДС</th>' +
                            '<th>Сертификаты</th>' +
                            '<th>Действия</th>' +
                        '</tr>' +
                    '</thead>' +
                    '<tbody>' +
                        '<tr v-for="cat in filteredCategories" :key="cat.id">' +
                            '<td><strong>{{ cat.category }}</strong></td>' +
                            '<td>{{ cat.material || "-" }}</td>' +
                            '<td><code class="code-badge">{{ cat.tnved_code || "-" }}</code></td>' +
                            '<td>{{ cat.rates.rail_base }}</td>' +
                            '<td>{{ cat.rates.air_base }}</td>' +
                            '<td>' +
                                '<span v-if="getCustomsInfo(cat)">' +
                                    '<strong>{{ getCustomsInfo(cat).duty_rate }}</strong>' +
                                    '<span v-if="getCustomsInfo(cat).duty_type === \'combined\'" class="duty-type-badge">комб.</span>' +
                                    '<span v-else-if="getCustomsInfo(cat).duty_type === \'specific\'" class="duty-type-badge">спец.</span>' +
                                '</span>' +
                                '<span v-else>-</span>' +
                            '</td>' +
                            '<td>{{ getCustomsInfo(cat)?.vat_rate || "-" }}</td>' +
                            '<td class="certificates-cell">' +
                                '<span v-if="getCustomsInfo(cat) && getCustomsInfo(cat).certificates.length > 0" class="certificates-count">' +
                                    '{{ getCustomsInfo(cat).certificates.length }} шт.' +
                                '</span>' +
                                '<span v-else>-</span>' +
                            '</td>' +
                            '<td class="actions-cell">' +
                                '<button @click="startEdit(cat)" class="btn-action btn-edit">Изменить</button>' +
                                '<button @click="deleteCategory(cat)" class="btn-action btn-delete">Удалить</button>' +
                            '</td>' +
                        '</tr>' +
                    '</tbody>' +
                '</table>' +
                
                '<div v-if="filteredCategories.length === 0" class="empty-state-message">' +
                    '<p>Категории не найдены</p>' +
                '</div>' +
            '</div>' +
        '</div>'
};

// Регистрируем компонент глобально
window.CategoriesPanel = CategoriesPanel;
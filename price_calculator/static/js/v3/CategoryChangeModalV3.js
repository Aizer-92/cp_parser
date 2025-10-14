// CategoryChangeModalV3.js - Изменение категории товара
window.CategoryChangeModalV3 = {
    props: {
        calculationId: Number,
        currentCategory: String,
        productName: String
    },
    
    data() {
        return {
            availableCategories: [],
            selectedCategory: this.currentCategory,
            isRecalculating: false
        };
    },
    
    mounted() {
        this.loadCategories();
    },
    
    methods: {
        async loadCategories() {
            try {
                const response = await axios.get('/api/v3/categories');
                
                // Обработать ответ (может быть массив или объект)
                if (Array.isArray(response.data)) {
                    this.availableCategories = response.data.map(c => c.category || c.name || c);
                } else if (response.data.categories && Array.isArray(response.data.categories)) {
                    this.availableCategories = response.data.categories.map(c => c.category || c.name || c);
                } else {
                    console.warn('⚠️ Неожиданный формат категорий:', response.data);
                    this.availableCategories = [];
                }
                
                console.log('✅ Категории загружены:', this.availableCategories.length);
                
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
                alert('Не удалось загрузить список категорий');
            }
        },
        
        close() {
            this.$emit('close');
        },
        
        async apply() {
            console.log('🔄 Изменение категории:', {
                calculationId: this.calculationId,
                oldCategory: this.currentCategory,
                newCategory: this.selectedCategory
            });
            
            // Валидация
            if (!this.selectedCategory) {
                alert('Выберите категорию');
                return;
            }
            
            if (this.selectedCategory === this.currentCategory) {
                alert('Категория не изменилась');
                return;
            }
            
            this.isRecalculating = true;
            
            try {
                // Пересчет с новой категорией через PUT API
                const response = await axios.put(
                    `/api/v3/calculations/${this.calculationId}`,
                    {
                        forced_category: this.selectedCategory
                    }
                );
                
                console.log('✅ Пересчет с новой категорией выполнен');
                
                // Эмитим обновленные результаты
                this.$emit('recalculated', response.data);
                
                // Закрываем модалку
                this.close();
                
            } catch (error) {
                console.error('❌ Ошибка пересчета:', error);
                const detail = error.response?.data?.detail;
                const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
                alert('Ошибка пересчета: ' + message);
            } finally {
                this.isRecalculating = false;
            }
        }
    },
    
    template: `
    <div class="modal-overlay" @click.self="close">
        <div class="modal-content" style="max-width: 500px;">
            <!-- Заголовок -->
            <div class="modal-header">
                <h3>Изменение категории</h3>
                <button @click="close" class="btn-close">×</button>
            </div>
            
            <!-- Форма -->
            <div class="modal-body">
                <div class="form-group">
                    <label>Товар</label>
                    <input
                        :value="productName"
                        readonly
                        class="form-input"
                        style="background: #f9fafb; cursor: not-allowed;"
                    />
                </div>
                
                <div class="form-group">
                    <label>Текущая категория</label>
                    <input
                        :value="currentCategory"
                        readonly
                        class="form-input"
                        style="background: #f9fafb; cursor: not-allowed;"
                    />
                </div>
                
                <div class="form-group">
                    <label>Новая категория</label>
                    <select
                        v-model="selectedCategory"
                        class="form-input"
                        :disabled="isRecalculating || availableCategories.length === 0"
                    >
                        <option value="">— Выберите категорию —</option>
                        <option
                            v-for="category in availableCategories"
                            :key="category"
                            :value="category"
                        >
                            {{ category }}
                        </option>
                    </select>
                    <div v-if="availableCategories.length === 0" class="form-hint" style="color: #f59e0b;">
                        Загрузка категорий...
                    </div>
                    <div v-else class="form-hint">
                        Изменение категории пересчитает пошлины и НДС
                    </div>
                </div>
            </div>
            
            <!-- Кнопки -->
            <div class="modal-footer">
                <button
                    @click="apply"
                    :disabled="isRecalculating || !selectedCategory || selectedCategory === currentCategory"
                    class="btn-primary"
                >
                    {{ isRecalculating ? 'Пересчёт...' : 'Применить' }}
                </button>
                <button
                    @click="close"
                    :disabled="isRecalculating"
                    class="btn-secondary"
                >
                    Отмена
                </button>
            </div>
        </div>
    </div>
    `
};


// PositionsListV3.js - Список всех позиций товаров
window.PositionsListV3 = {
    template: `
    <div class="positions-list">
        <!-- Форма создания/редактирования -->
        <PositionFormV3
            v-if="showForm"
            :position="editingPosition"
            @close="closeForm"
            @saved="onPositionSaved"
        />
        
        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 class="card-title">Позиции товаров</h2>
                <button @click="createPosition" class="btn-primary">
                    + Создать позицию
                </button>
            </div>
            
            <!-- Поиск и фильтры -->
            <div class="filters-bar">
                <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="Поиск по названию или категории..."
                    class="form-input"
                    style="flex: 1;"
                />
                <select v-model="categoryFilter" class="form-input" style="width: 200px;">
                    <option value="">Все категории</option>
                    <option v-for="cat in categories" :key="cat" :value="cat">
                        {{ cat }}
                    </option>
                </select>
            </div>
            
            <!-- Загрузка -->
            <div v-if="isLoading" class="loading-state">
                <div class="spinner"></div>
                <p>Загрузка позиций...</p>
            </div>
            
            <!-- Пустой список -->
            <div v-else-if="filteredPositions.length === 0" class="empty-state">
                <p>Нет позиций</p>
                <button @click="createPosition" class="btn-secondary">
                    Создать первую позицию
                </button>
            </div>
            
            <!-- Список позиций -->
            <div v-else class="positions-grid">
                <div
                    v-for="position in filteredPositions"
                    :key="position.id"
                    class="position-card"
                    @click="openPosition(position.id)"
                >
                    <!-- Фото -->
                    <div class="position-image">
                        <img
                            :src="(position.design_files_urls && position.design_files_urls.length > 0) ? position.design_files_urls[0] : 'https://via.placeholder.com/300x200?text=No+Image'"
                            :alt="position.name"
                            @error="$event.target.src='https://via.placeholder.com/300x200?text=No+Image'"
                        />
                    </div>
                    
                    <!-- Информация -->
                    <div class="position-info">
                        <h3 class="position-name">{{ position.name }}</h3>
                        <p v-if="position.category" class="position-category">
                            {{ position.category }}
                        </p>
                        <p v-if="position.description" class="position-description">
                            {{ truncate(position.description, 80) }}
                        </p>
                        
                        <!-- Метаданные -->
                        <div class="position-meta">
                            <span class="meta-item">
                                ID: {{ position.id }}
                            </span>
                            <span class="meta-item">
                                {{ formatDate(position.created_at) }}
                            </span>
                        </div>
                    </div>
                    
                    <!-- Действия -->
                    <div class="position-actions">
                        <button
                            @click.stop="editPosition(position.id)"
                            class="btn-icon"
                            title="Редактировать"
                        >
                            ✏
                        </button>
                        <button
                            @click.stop="confirmDelete(position.id)"
                            class="btn-icon btn-danger"
                            title="Удалить"
                        >
                            🗑
                        </button>
                    </div>
                </div>
            </div>
            
            <!-- Пагинация -->
            <div v-if="totalPages > 1" class="pagination">
                <button
                    @click="prevPage"
                    :disabled="currentPage === 1"
                    class="btn-secondary btn-sm"
                >
                    ← Назад
                </button>
                <span class="pagination-info">
                    Страница {{ currentPage }} из {{ totalPages }}
                </span>
                <button
                    @click="nextPage"
                    :disabled="currentPage === totalPages"
                    class="btn-secondary btn-sm"
                >
                    Вперёд →
                </button>
            </div>
        </div>
    </div>
    `,
    
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

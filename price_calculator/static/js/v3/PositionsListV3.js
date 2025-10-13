// PositionsListV3.js - Список позиций
window.PositionsListV3 = {
    template: `
    <div class="positions-list">
        <!-- Заголовок -->
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">Позиции</h2>
                <button @click="createPosition" class="btn-primary">
                    Новая позиция
                </button>
            </div>
            
            <!-- Поиск и фильтры -->
            <div class="search-bar">
                <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="Поиск позиций..."
                    class="form-input"
                    @input="onSearch"
                />
                <select v-model="filterCategory" class="form-input" style="max-width: 200px;">
                    <option value="">Все категории</option>
                    <option v-for="cat in categories" :key="cat" :value="cat">
                        {{ cat }}
                    </option>
                </select>
            </div>
        </div>
        
        <!-- Список позиций -->
        <div v-if="loading" class="card">
            <p>Загрузка...</p>
        </div>
        
        <div v-else-if="filteredPositions.length === 0" class="card">
            <p>Позиций пока нет. Создайте первую!</p>
        </div>
        
        <div v-else class="positions-grid">
            <div
                v-for="position in filteredPositions"
                :key="position.id"
                class="position-card card"
                @click="openPosition(position.id)"
            >
                <!-- Фото (если есть) -->
                <div v-if="position.design_files_urls && position.design_files_urls.length > 0" class="position-photo">
                    <img :src="position.design_files_urls[0]" :alt="position.name" />
                </div>
                
                <!-- Информация -->
                <div class="position-info">
                    <h3 class="position-name">{{ position.name }}</h3>
                    <p class="position-category">{{ position.category || 'Без категории' }}</p>
                    <div class="position-meta">
                        <span v-if="position.design_files_urls">
                            Фото: {{ position.design_files_urls.length }} шт
                        </span>
                        <span v-if="position.calculations_count">
                            Расчётов: {{ position.calculations_count }}
                        </span>
                        <span v-if="position.updated_at">
                            {{ formatDate(position.updated_at) }}
                        </span>
                    </div>
                </div>
                
                <!-- Действия -->
                <div class="position-actions" @click.stop>
                    <button @click="editPosition(position.id)" class="btn-text btn-sm">
                        Редактировать
                    </button>
                    <button @click="deletePosition(position.id)" class="btn-text btn-sm" style="color: var(--color-danger);">
                        Удалить
                    </button>
                </div>
            </div>
        </div>
    </div>
    `,
    
    data() {
        return {
            positions: [],
            searchQuery: '',
            filterCategory: '',
            categories: [],
            loading: true
        };
    },
    
    computed: {
        filteredPositions() {
            let filtered = this.positions;
            
            // Поиск
            if (this.searchQuery) {
                const query = this.searchQuery.toLowerCase();
                filtered = filtered.filter(p =>
                    p.name.toLowerCase().includes(query) ||
                    (p.description && p.description.toLowerCase().includes(query))
                );
            }
            
            // Фильтр по категории
            if (this.filterCategory) {
                filtered = filtered.filter(p => p.category === this.filterCategory);
            }
            
            return filtered;
        }
    },
    
    async mounted() {
        await this.loadPositions();
        this.extractCategories();
    },
    
    methods: {
        async loadPositions() {
            this.loading = true;
            try {
                const api = window.usePositionsV3();
                const response = await api.getPositions(0, 1000);
                this.positions = response.items || response || [];
                
                // Загружаем количество расчётов для каждой позиции
                await this.loadCalculationsCounts();
            } catch (error) {
                console.error('Ошибка загрузки позиций:', error);
                alert('Не удалось загрузить позиции');
            } finally {
                this.loading = false;
            }
        },
        
        async loadCalculationsCounts() {
            const calcApi = window.useCalculationsV3();
            for (const position of this.positions) {
                try {
                    const calcs = await calcApi.getCalculationsByPosition(position.id);
                    position.calculations_count = calcs.length;
                } catch (error) {
                    position.calculations_count = 0;
                }
            }
        },
        
        extractCategories() {
            const cats = new Set();
            this.positions.forEach(p => {
                if (p.category) cats.add(p.category);
            });
            this.categories = Array.from(cats).sort();
        },
        
        onSearch() {
            // Дебаунс уже работает через v-model
        },
        
        createPosition() {
            this.$emit('switch-tab', 'position-form');
            // TODO: открыть форму создания
        },
        
        openPosition(positionId) {
            console.log('Открыть позицию:', positionId);
            this.$emit('open-position', positionId);
            // TODO: переключиться на детали позиции
        },
        
        editPosition(positionId) {
            console.log('Редактировать позицию:', positionId);
            // TODO: открыть форму редактирования
        },
        
        async deletePosition(positionId) {
            if (!confirm('Удалить эту позицию и все её расчёты?')) return;
            
            try {
                const api = window.usePositionsV3();
                await api.deletePosition(positionId);
                await this.loadPositions();
            } catch (error) {
                console.error('Ошибка удаления:', error);
                alert('Не удалось удалить позицию');
            }
        },
        
        formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('ru-RU');
        }
    }
};


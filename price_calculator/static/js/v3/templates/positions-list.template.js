/**
 * Template для PositionsListV3
 * 
 * Список позиций товаров с карточками
 * - Grid layout с карточками
 * - Поиск и фильтры по категориям
 * - Интеграция с PositionFormV3 для создания/редактирования
 * - Пагинация
 */
export const POSITIONS_LIST_TEMPLATE = `
<div class="positions-list">
    <!-- ============================================ -->
    <!--  ФОРМА СОЗДАНИЯ/РЕДАКТИРОВАНИЯ              -->
    <!-- ============================================ -->
    <PositionFormV3
        v-if="showForm"
        :position="editingPosition"
        @close="closeForm"
        @saved="onPositionSaved"
        @calculate-routes="onCalculateRoutes"
    />
    
    <div class="card">
        <!-- ============================================ -->
        <!--  HEADER                                     -->
        <!-- ============================================ -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <h2 class="card-title">Позиции товаров</h2>
            <button @click="createPosition" class="btn-primary">
                + Создать позицию
            </button>
        </div>
        
        <!-- ============================================ -->
        <!--  ПОИСК И ФИЛЬТРЫ                            -->
        <!-- ============================================ -->
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
        
        <!-- ============================================ -->
        <!--  LOADING STATE                              -->
        <!-- ============================================ -->
        <div v-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <p>Загрузка позиций...</p>
        </div>
        
        <!-- ============================================ -->
        <!--  EMPTY STATE                                -->
        <!-- ============================================ -->
        <div v-else-if="filteredPositions.length === 0" class="empty-state">
            <p>Нет позиций</p>
            <button @click="createPosition" class="btn-secondary">
                Создать первую позицию
            </button>
        </div>
        
        <!-- ============================================ -->
        <!--  GRID ПОЗИЦИЙ                               -->
        <!-- ============================================ -->
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
        
        <!-- ============================================ -->
        <!--  PAGINATION                                 -->
        <!-- ============================================ -->
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
`;


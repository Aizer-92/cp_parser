/**
 * Template для CalculationResultsV3
 * 
 * Отображение результатов расчета с детальной разбивкой по маршрутам
 * - Модалки для быстрого редактирования и смены категории
 * - RouteEditorV3 для каждого маршрута
 * - Детальная структура затрат
 * - История расчетов для позиции
 */
export const CALCULATION_RESULTS_TEMPLATE = `
<div class="calculation-results">
    <!-- ============================================ -->
    <!--  МОДАЛКИ                                    -->
    <!-- ============================================ -->
    <QuickEditModalV3
        v-if="showQuickEdit && result && result.calculation_id"
        :calculation-id="result.calculation_id"
        :initial-quantity="result.quantity"
        :initial-markup="result.markup"
        @close="closeQuickEdit"
        @recalculated="handleQuickEditRecalculated"
    />
    
    <CategoryChangeModalV3
        v-if="showCategoryChange && result && result.calculation_id"
        :calculation-id="result.calculation_id"
        :current-category="result.category"
        :product-name="result.product_name || result.name || 'Товар'"
        @close="closeCategoryChange"
        @recalculated="handleCategoryChangeRecalculated"
    />
    
    <!-- ============================================ -->
    <!--  ПУСТОЕ СОСТОЯНИЕ                           -->
    <!-- ============================================ -->
    <div v-if="!result" class="card">
        <div class="empty-state" style="padding: 60px 20px; text-align: center;">
            <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
            <h3 style="font-size: 18px; font-weight: 600; color: #111827; margin-bottom: 8px;">
                Нет результатов расчета
            </h3>
            <p style="color: #6b7280; margin-bottom: 24px;">
                Выполните расчет в разделе "Быстрый расчёт" или создайте позицию
            </p>
            <button @click="newCalculation" class="btn-primary">
                Перейти к расчету
            </button>
        </div>
    </div>
    
    <!-- ============================================ -->
    <!--  ФОРМА КАСТОМНЫХ ПАРАМЕТРОВ                 -->
    <!-- ============================================ -->
    <CustomLogisticsFormV3
        v-else-if="needsCustomParams"
        :category="result.category"
        :routes="result.routes || {}"
        @apply="applyCustomLogistics"
        @cancel="cancelCustomParams"
    />
    
    <!-- ============================================ -->
    <!--  РЕЗУЛЬТАТЫ РАСЧЕТА                         -->
    <!-- ============================================ -->
    <div v-else class="card">
        <!-- Заголовок с действиями -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
            <div>
                <h2 class="card-title">Результаты расчета</h2>
                <p style="color: #6b7280; font-size: 14px; margin-top: 4px;">
                    {{ result.product_name || result.name || 'Товар' }}
                    <span v-if="result.category"> · {{ result.category }}</span>
                </p>
            </div>
            <div style="display: flex; gap: 12px;">
                <button @click="openQuickEdit" class="btn-secondary">
                    ✏ Изменить кол-во/наценку
                </button>
                <button @click="openCategoryChange" class="btn-secondary">
                    🏷 Изменить категорию
                </button>
                <button @click="newCalculation" class="btn-primary">
                    🆕 Новый расчет
                </button>
            </div>
        </div>
        
        <!-- Маршруты -->
        <div v-if="sortedRoutes && sortedRoutes.length > 0">
            <div v-for="route in sortedRoutes" :key="route.key" style="margin-bottom: 16px;">
                <RouteEditorV3
                    :route-key="route.key"
                    :route="route"
                    :calculation-id="result.calculation_id"
                    :category="result.category"
                    @update-route="handleUpdateRoute"
                />
            </div>
        </div>
        <div v-else style="padding: 40px; text-align: center; color: #6b7280;">
            Нет доступных маршрутов
        </div>
        
        <!-- История расчетов (если есть position_id) -->
        <div v-if="result.position_id" style="margin-top: 32px;">
            <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 16px;">
                История расчетов для этой позиции
            </h3>
            <CalculationHistoryV3 :position-id="result.position_id" />
        </div>
    </div>
</div>
`;


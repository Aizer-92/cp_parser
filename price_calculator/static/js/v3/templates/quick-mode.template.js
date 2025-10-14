/**
 * Template для QuickModeV3
 * 
 * Упрощенная форма быстрого расчета товара
 * - Минимум полей (название, категория, фабрика, цена, кол-во, вес/паккинг, наценка)
 * - Автоопределение категории
 * - Два режима: по весу / детальный паккинг
 * - Интеграция с CustomLogisticsFormV3 для второго этапа
 */
export const QUICK_MODE_TEMPLATE = `
<div class="quick-mode">
    <div class="card">
        <h2 class="card-title">Быстрый расчёт</h2>
        
        <form @submit.prevent="calculate" class="form">
            
            <!-- ============================================ -->
            <!--  НАЗВАНИЕ ТОВАРА                            -->
            <!-- ============================================ -->
            <div class="form-group">
                <label for="product-name">Название товара *</label>
                <input
                    id="product-name"
                    v-model="productName"
                    type="text"
                    placeholder="Например: Футболка хлопковая"
                    required
                    class="form-input"
                    @input="detectCategory"
                />
            </div>
            
            <!-- ============================================ -->
            <!--  КАТЕГОРИЯ (автоопределяется)               -->
            <!-- ============================================ -->
            <div class="form-group">
                <label for="category">
                    Категория 
                    <span style="color: #6b7280; font-size: 13px;">(автоопределяется)</span>
                </label>
                <input
                    id="category"
                    v-model="category"
                    type="text"
                    list="categories-list"
                    placeholder="Определится автоматически"
                    class="form-input"
                />
                <datalist id="categories-list">
                    <option v-for="cat in availableCategories" :key="cat" :value="cat">
                </datalist>
            </div>
            
            <!-- ============================================ -->
            <!--  ФАБРИКА                                     -->
            <!-- ============================================ -->
            <div class="form-group">
                <label for="factory">Фабрика (WeChat / URL)</label>
                <input
                    id="factory"
                    v-model="factoryUrl"
                    type="text"
                    placeholder="https://... или WeChat ID"
                    class="form-input"
                />
            </div>
            
            <!-- ============================================ -->
            <!--  ЦЕНА И КОЛИЧЕСТВО                           -->
            <!-- ============================================ -->
            <div class="form-row">
                <div class="form-group flex-1">
                    <label for="price">Цена (¥) *</label>
                    <input
                        id="price"
                        v-model.number="priceYuan"
                        type="number"
                        step="0.01"
                        required
                        class="form-input"
                    />
                </div>
                
                <div class="form-group flex-1">
                    <label for="quantity">Кол-во *</label>
                    <input
                        id="quantity"
                        v-model.number="quantity"
                        type="number"
                        required
                        class="form-input"
                    />
                </div>
            </div>
                
            <!-- ============================================ -->
            <!--  ПЕРЕКЛЮЧАТЕЛЬ РЕЖИМОВ                       -->
            <!-- ============================================ -->
            <div class="mode-toggle">
                <label class="toggle-label">
                    <input
                        type="radio"
                        :value="false"
                        v-model="detailedMode"
                        class="toggle-radio"
                    />
                    <span>По весу</span>
                </label>
                <label class="toggle-label">
                    <input
                        type="radio"
                        :value="true"
                        v-model="detailedMode"
                        class="toggle-radio"
                    />
                    <span>Детальный (упаковка)</span>
                </label>
            </div>
            
            <!-- ============================================ -->
            <!--  ВЕС (быстрый режим)                         -->
            <!-- ============================================ -->
            <div v-if="!detailedMode" class="form-group">
                <label for="weight">Вес 1 единицы (кг) *</label>
                <input
                    id="weight"
                    v-model.number="weightKg"
                    type="number"
                    step="0.01"
                    required
                    class="form-input"
                />
            </div>
            
            <!-- ============================================ -->
            <!--  ПАККИНГ (детальный режим)                   -->
            <!-- ============================================ -->
            <div v-else class="packing-section">
                <!-- Штук в коробке + Вес коробки -->
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label for="units-per-box">Штук в коробке *</label>
                        <input
                            id="units-per-box"
                            v-model.number="packingUnitsPerBox"
                            type="number"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="box-weight">Вес коробки (кг) *</label>
                        <input
                            id="box-weight"
                            v-model.number="packingBoxWeight"
                            type="number"
                            step="0.01"
                            required
                            class="form-input"
                        />
                    </div>
                </div>
                
                <!-- Размеры коробки: Длина, Ширина, Высота -->
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label for="box-length">Длина (см) *</label>
                        <input
                            id="box-length"
                            v-model.number="packingBoxLength"
                            type="number"
                            step="0.1"
                            required
                            class="form-input"
                            placeholder="50"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="box-width">Ширина (см) *</label>
                        <input
                            id="box-width"
                            v-model.number="packingBoxWidth"
                            type="number"
                            step="0.1"
                            required
                            class="form-input"
                            placeholder="40"
                        />
                    </div>
                    
                    <div class="form-group flex-1">
                        <label for="box-height">Высота (см) *</label>
                        <input
                            id="box-height"
                            v-model.number="packingBoxHeight"
                            type="number"
                            step="0.1"
                            required
                            class="form-input"
                            placeholder="30"
                        />
                    </div>
                </div>
            </div>
            
            <!-- ============================================ -->
            <!--  НАЦЕНКА                                     -->
            <!-- ============================================ -->
            <div class="form-group">
                <label for="markup">Наценка *</label>
                <input
                    id="markup"
                    v-model.number="markup"
                    type="number"
                    step="0.01"
                    required
                    class="form-input"
                />
            </div>
            
            <!-- ============================================ -->
            <!--  КНОПКА РАСЧЁТА                              -->
            <!-- ============================================ -->
            <div class="form-actions">
                <button
                    type="submit"
                    :disabled="isCalculating"
                    class="btn-primary"
                >
                    {{ isCalculating ? 'Расчёт...' : 'Рассчитать' }}
                </button>
            </div>
        </form>
    </div>
    
    <!-- ============================================ -->
    <!--  ВТОРОЙ ЭТАП: КАСТОМНЫЕ ПАРАМЕТРЫ            -->
    <!-- ============================================ -->
    <CustomLogisticsFormV3
        v-if="needsCustomParams"
        :category="category"
        :routes="placeholderRoutes"
        @apply="applyCustomLogistics"
        @cancel="cancelCustomParams"
    />
    
</div>
`;


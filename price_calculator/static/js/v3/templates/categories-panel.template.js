/**
 * Template для CategoriesPanelV3
 * 
 * Управление категориями товаров: список, добавление, редактирование, удаление
 * Особенности:
 * - Поиск по названию и ТН ВЭД
 * - 3 типа пошлин (процентные, весовые, комбинированные)
 * - Статистика цен по категориям
 * - Inline-форма редактирования
 */
export const CATEGORIES_PANEL_TEMPLATE = `
<div>
    <!-- ============================================ -->
    <!--  HEADER (Поиск + Добавить)                  -->
    <!-- ============================================ -->
    <div style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <input 
                v-model="searchQuery" 
                type="text" 
                placeholder="Поиск по названию или ТН ВЭД..." 
                class="form-input"
                style="width: 400px;"
            />
            <button 
                @click="startAdd" 
                class="btn-primary"
            >
                Добавить категорию
            </button>
        </div>
    </div>
    
    <!-- ============================================ -->
    <!--  LOADING STATE                              -->
    <!-- ============================================ -->
    <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Загрузка...</p>
    </div>
    
    <!-- ============================================ -->
    <!--  ADD/EDIT FORM                              -->
    <!-- ============================================ -->
    <div v-else-if="showAddForm || showEditForm" class="card" style="margin-bottom: 20px;">
        <h3 style="font-size: 16px; font-weight: 600; color: #111827; margin-bottom: 20px;">
            {{ showAddForm ? 'Новая категория' : ('Редактирование: ' + (currentForm.category || '')) }}
        </h3>
        
        <!-- Название + Материал -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <div>
                <label class="form-label">Название *</label>
                <input 
                    v-model="currentForm.category" 
                    type="text" 
                    class="form-input"
                />
            </div>
            <div>
                <label class="form-label">Материал</label>
                <input 
                    v-model="currentForm.material" 
                    type="text" 
                    class="form-input"
                />
            </div>
        </div>
        
        <!-- ТН ВЭД + Плотность -->
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <div>
                <label class="form-label">ТН ВЭД</label>
                <input 
                    v-model="currentForm.tnved_code" 
                    type="text" 
                    class="form-input"
                />
            </div>
            <div>
                <label class="form-label">Плотность (кг/м³)</label>
                <input 
                    v-model.number="currentForm.density" 
                    type="number" 
                    step="0.1" 
                    class="form-input"
                />
            </div>
        </div>
        
        <!-- ЖД + Авиа ставки -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px;">
            <div>
                <label class="form-label">ЖД ($/кг) *</label>
                <input 
                    v-model.number="currentForm.rates.rail_base" 
                    type="number" 
                    step="0.1" 
                    class="form-input"
                />
            </div>
            <div>
                <label class="form-label">Авиа ($/кг) *</label>
                <input 
                    v-model.number="currentForm.rates.air_base" 
                    type="number" 
                    step="0.1" 
                    class="form-input"
                />
            </div>
        </div>
        
        <!-- Тип пошлины -->
        <div style="margin-bottom: 20px;">
            <label class="form-label">Тип пошлины</label>
            <select 
                v-model="currentForm.duty_type" 
                class="form-input"
            >
                <option value="percent">Процентные (только %)</option>
                <option value="specific">Весовые (только EUR/кг)</option>
                <option value="combined">Комбинированные (% ИЛИ EUR/кг)</option>
            </select>
        </div>
        
        <!-- Поля пошлин (динамически в зависимости от типа) -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px;">
            <!-- Процентная пошлина -->
            <div v-if="currentForm.duty_type === 'percent' || currentForm.duty_type === 'combined'">
                <label class="form-label">
                    {{ currentForm.duty_type === 'combined' ? 'Процентная пошлина' : 'Пошлина' }}
                </label>
                <input 
                    v-model="currentForm.duty_type === 'combined' ? currentForm.ad_valorem_rate : currentForm.duty_rate" 
                    type="text" 
                    placeholder="10%" 
                    class="form-input"
                />
            </div>
            
            <!-- Весовая пошлина -->
            <div v-if="currentForm.duty_type === 'specific' || currentForm.duty_type === 'combined'">
                <label class="form-label">
                    Весовая пошлина 
                    <span style="font-size: 12px; color: #6b7280;">(EUR/кг)</span>
                </label>
                <input 
                    v-model.number="currentForm.specific_rate" 
                    type="number" 
                    step="0.1"
                    min="0"
                    placeholder="2.2" 
                    class="form-input"
                />
            </div>
            
            <!-- НДС -->
            <div>
                <label class="form-label">НДС</label>
                <input 
                    v-model="currentForm.vat_rate" 
                    type="text" 
                    placeholder="20%" 
                    class="form-input"
                />
            </div>
        </div>
        
        <!-- Подсказка по типу пошлины -->
        <div v-if="currentForm.duty_type" style="background: #f0f9ff; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 12px; color: #0369a1;">
            <div v-if="currentForm.duty_type === 'percent'">
                <strong>Процентные пошлины:</strong> Рассчитываются как процент от таможенной стоимости.
            </div>
            <div v-if="currentForm.duty_type === 'specific'">
                <strong>Весовые пошлины:</strong> Рассчитываются по весу товара (например, 2.2 EUR за каждый килограмм).
            </div>
            <div v-if="currentForm.duty_type === 'combined'">
                <strong>Комбинированные пошлины:</strong> Рассчитываются оба варианта, применяется БОЛЬШАЯ.
            </div>
        </div>
        
        <!-- Кнопки действий -->
        <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button @click="cancelEdit" class="btn-secondary">Отмена</button>
            <button @click="showAddForm ? addCategory() : saveCategory()" class="btn-primary">
                {{ showAddForm ? 'Добавить' : 'Сохранить' }}
            </button>
        </div>
    </div>
    
    <!-- ============================================ -->
    <!--  CATEGORIES LIST                            -->
    <!-- ============================================ -->
    <div v-else>
        <div v-for="cat in filteredCategories" :key="cat.id" class="card" style="margin-bottom: 12px;">
            <!-- Заголовок категории -->
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                <div>
                    <div style="font-size: 15px; font-weight: 600; color: #111827;">{{ cat.category }}</div>
                    <div v-if="cat.material" style="font-size: 13px; color: #6b7280; margin-top: 2px;">{{ cat.material }}</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button @click="startEdit(cat)" class="btn-icon">✏</button>
                    <button @click="deleteCategory(cat)" class="btn-icon" style="color: #ef4444; border-color: #ef4444;">🗑</button>
                </div>
            </div>
            
            <!-- Основные данные (ТН ВЭД, ЖД, Авиа, Тип пошлины) -->
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px;">
                <!-- ТН ВЭД -->
                <div style="background: #f9fafb; border-radius: 6px; padding: 10px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">ТН ВЭД</div>
                    <div style="font-size: 13px; font-weight: 600; color: #111827; font-family: monospace;">{{ cat.tnved_code || '—' }}</div>
                </div>
                
                <!-- ЖД -->
                <div style="background: #f9fafb; border-radius: 6px; padding: 10px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">ЖД</div>
                    <div style="font-size: 13px; font-weight: 600; color: #111827;">{{ cat.rates?.rail_base || '—' }} $/кг</div>
                </div>
                
                <!-- Авиа -->
                <div style="background: #f9fafb; border-radius: 6px; padding: 10px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">Авиа</div>
                    <div style="font-size: 13px; font-weight: 600; color: #111827;">{{ cat.rates?.air_base || '—' }} $/кг</div>
                </div>
                
                <!-- Тип пошлины -->
                <div style="background: #f9fafb; border-radius: 6px; padding: 10px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 4px;">
                        Тип пошлины
                    </div>
                    <div style="font-size: 12px; font-weight: 600; color: #111827;">
                        <span v-if="getCustomsInfo(cat)?.duty_type === 'combined'">
                            Комбинир.
                        </span>
                        <span v-else-if="getCustomsInfo(cat)?.duty_type === 'specific'">
                            Весовые
                        </span>
                        <span v-else>
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
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #6b7280; margin-bottom: 8px;">Статистика цен</div>
                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px;">
                    <!-- Количество расчетов -->
                    <div style="background: #f9fafb; border-radius: 6px; padding: 8px;">
                        <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Расчетов</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ getStats(cat.category).count }}</div>
                    </div>
                    
                    <!-- Мин цена -->
                    <div style="background: #f9fafb; border-radius: 6px; padding: 8px;">
                        <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Мин</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).min_price) }}</div>
                    </div>
                    
                    <!-- Макс цена -->
                    <div style="background: #f9fafb; border-radius: 6px; padding: 8px;">
                        <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Макс</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).max_price) }}</div>
                    </div>
                    
                    <!-- Средняя цена -->
                    <div style="background: #f9fafb; border-radius: 6px; padding: 8px;">
                        <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Средняя</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).avg_price) }}</div>
                    </div>
                    
                    <!-- Медиана -->
                    <div v-if="getStats(cat.category).median_price" style="background: #f9fafb; border-radius: 6px; padding: 8px;">
                        <div style="font-size: 10px; color: #9ca3af; margin-bottom: 3px;">Медиана</div>
                        <div style="font-size: 14px; font-weight: 700; color: #111827;">{{ formatPrice(getStats(cat.category).median_price) }}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Empty state -->
        <div v-if="filteredCategories.length === 0" class="empty-state">
            Категории не найдены
        </div>
    </div>
</div>
`;


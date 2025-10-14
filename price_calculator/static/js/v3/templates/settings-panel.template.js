/**
 * Template для SettingsPanelV3
 * 
 * Панель настроек приложения
 * - Курсы валют
 * - Формула расчета (комиссии, ставки)
 * - Значения по умолчанию
 * - Управление категориями (вложенная CategoriesPanelV3)
 */
export const SETTINGS_PANEL_TEMPLATE = `
<div>
    <div class="card">
        <h2 class="card-title">Настройки</h2>
        
        <!-- Tabs -->
        <div class="tabs" style="margin-bottom: 24px;">
            <button
                @click="activeTab = 'general'"
                class="tab"
                :class="{ 'active': activeTab === 'general' }"
            >
                Общие настройки
            </button>
            <button
                @click="activeTab = 'categories'"
                class="tab"
                :class="{ 'active': activeTab === 'categories' }"
            >
                Управление категориями
            </button>
        </div>
        
        <!-- General Settings Tab -->
        <div v-if="activeTab === 'general'">
            <!-- Currencies Section -->
            <div style="margin-bottom: 32px;">
                <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #111827;">
                    Курсы валют
                </h3>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Юань → Доллар</label>
                        <input v-model.number="localSettings.currencies.yuan_to_usd" type="number" step="0.001" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Доллар → Рубль</label>
                        <input v-model.number="localSettings.currencies.usd_to_rub" type="number" step="0.1" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Юань → Рубль</label>
                        <input v-model.number="localSettings.currencies.yuan_to_rub" type="number" step="0.01" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Евро → Рубль</label>
                        <input v-model.number="localSettings.currencies.eur_to_rub" type="number" step="0.1" class="form-input" />
                    </div>
                </div>
            </div>
            
            <!-- Formula Section -->
            <div style="margin-bottom: 32px;">
                <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #111827;">
                    Параметры формулы расчета
                </h3>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Комиссия за выкуп (%)</label>
                        <input v-model.number="localSettings.formula.toni_commission_percent" type="number" step="0.1" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Процент перевода (%)</label>
                        <input v-model.number="localSettings.formula.transfer_percent" type="number" step="0.1" class="form-input" />
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Доставка внутри Китая (¥/кг)</label>
                        <input v-model.number="localSettings.formula.local_delivery_rate_yuan_per_kg" type="number" step="0.1" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Вывоз из Москвы (₽)</label>
                        <input v-model.number="localSettings.formula.msk_pickup_total_rub" type="number" step="100" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Прочие расходы (%)</label>
                        <input v-model.number="localSettings.formula.other_costs_percent" type="number" step="0.1" class="form-input" />
                    </div>
                </div>
            </div>
            
            <!-- Defaults Section -->
            <div style="margin-bottom: 32px;">
                <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #111827;">
                    Значения по умолчанию
                </h3>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Наценка по умолчанию</label>
                        <input v-model.number="localSettings.defaultMarkup" type="number" step="0.1" class="form-input" />
                    </div>
                    <div class="form-group flex-1">
                        <label>Количество по умолчанию</label>
                        <input v-model.number="localSettings.defaultQuantity" type="number" step="100" class="form-input" />
                    </div>
                </div>
                <div class="form-group">
                    <label>
                        <input v-model="localSettings.autoSaveCalculations" type="checkbox" />
                        <span style="margin-left: 8px;">Автоматически сохранять расчеты</span>
                    </label>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="form-actions">
                <button @click="resetToDefaults" class="btn-secondary">
                    Сбросить к значениям по умолчанию
                </button>
                <button @click="saveSettings" class="btn-primary">
                    Сохранить настройки
                </button>
            </div>
        </div>
        
        <!-- Categories Tab -->
        <div v-if="activeTab === 'categories'">
            <CategoriesPanelV3 />
        </div>
    </div>
</div>
`;


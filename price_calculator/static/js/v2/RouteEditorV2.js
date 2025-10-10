// RouteEditorV2.js - Редактор параметров маршрута
window.RouteEditorV2 = {
    mixins: [window.RouteEditorMixin],
    
    props: {
        routeKey: String,
        route: Object,
        isNewCategory: {
            type: Boolean,
            default: false
        }
    },
    
    data() {
        return {
            isEditing: false,
            editParams: {
                custom_rate: null,
                duty_type: 'percent',  // percent, specific, combined
                duty_rate: null,       // Для percent и combined
                specific_rate: null,   // Для specific и combined  
                vat_rate: null
            }
        };
    },
    
    computed: {
        routeTitle() {
            return this.getRouteTitle(this.routeKey);
        },
        
        routeType() {
            return this.getRouteType(this.routeKey);
        },
        
        isHighway() {
            return this.routeType.isHighway;
        },
        
        isContract() {
            return this.routeType.isContract;
        },
        
        isPrologix() {
            return this.routeType.isPrologix;
        },
        
        isSeaContainer() {
            return this.routeType.isSeaContainer;
        }
    },
    
    methods: {
        openEdit() {
            this.isEditing = true;
            
            // Загружаем логистическую ставку (для всех кроме sea_container)
            if (!this.isSeaContainer) {
                this.editParams.custom_rate = this.extractLogisticsRate(
                    this.route, 
                    this.routeKey, 
                    this.isNewCategory
                );
            }
            
            // Загружаем данные о пошлинах (для Contract, Prologix, SeaContainer)
            if (this.isContract || this.isPrologix || this.isSeaContainer) {
                const dutyData = this.extractDutyData(this.route, this.routeKey);
                this.editParams.duty_type = dutyData.duty_type;
                this.editParams.duty_rate = dutyData.duty_rate;
                this.editParams.vat_rate = dutyData.vat_rate;
                this.editParams.specific_rate = dutyData.specific_rate;
            }
            
            console.log('✏️ Открыто редактирование:', this.routeKey, 'Текущая ставка:', this.editParams.custom_rate);
        },
        
        cancelEdit() {
            this.isEditing = false;
        },
        
        saveEdit() {
            console.log('💾 Сохранение параметров для', this.routeKey, this.editParams);
            
            // Валидация параметров
            const validation = this.validateRouteParams(
                this.editParams, 
                this.routeKey, 
                this.isNewCategory
            );
            
            if (!validation.isValid) {
                alert(validation.message);
                return;
            }
            
            // Очистка и преобразование параметров
            const cleanParams = this.cleanNumericParams(this.editParams);
            
            console.log('💾 Очищенные параметры:', cleanParams);
            this.$emit('save', this.routeKey, cleanParams);
            this.isEditing = false;
        }
    },
    
    mounted() {
        // ✨ V3: Умное автооткрытие - только если параметры не заполнены
        const v3 = window.useCalculationV3();
        
        // Проверяем нужно ли показывать форму (только для "Новая категория" без параметров)
        if (v3.shouldShowEditForm(this.category, this.route.custom_logistics)) {
            this.openEdit();
            console.log(`🆕 Автоматическое открытие редактирования для "${this.routeKey}" (параметры не заполнены)`);
        } else if (this.isNewCategory) {
            console.log(`✅ "${this.routeKey}" параметры уже заполнены - форма не открывается автоматически`);
        }
    },
    
    template: `
        <div style="margin-top: 8px;">
            <!-- Кнопка с иконкой "Изменить параметры" -->
            <button 
                v-if="!isEditing"
                @click="openEdit"
                title="Изменить параметры маршрута"
                style="padding: 6px 10px; background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12px; color: #6b7280; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px;"
                onmouseover="this.style.borderColor='#111827'; this.style.background='#f9fafb'"
                onmouseout="this.style.borderColor='#e5e7eb'; this.style.background='transparent'"
            >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
                <span>Параметры</span>
            </button>
            
            <!-- Форма редактирования -->
            <div v-else style="background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; margin-top: 8px;">
                <div style="font-size: 13px; font-weight: 600; color: #111827; margin-bottom: 12px;">
                    Параметры маршрута: {{ routeTitle }}
                </div>
                
                <!-- Информация для "Новая категория" -->
                <div v-if="isNewCategory" style="background: #fef3c7; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; color: #92400e; border: 1px solid #fbbf24;">
                    <div style="font-weight: 600; margin-bottom: 4px;">🆕 Новая категория</div>
                    <div>Товар не был распознан автоматически. Пожалуйста, укажите:</div>
                    <ul style="margin: 6px 0 0 20px; padding: 0;">
                        <li v-if="isHighway">Логистическую ставку в $/кг</li>
                        <li v-if="!isHighway && !isSeaContainer">Пошлины и НДС (см. ниже)</li>
                        <li v-if="isSeaContainer">Пошлины и НДС для контейнеров (см. ниже)</li>
                    </ul>
                </div>
                
                <!-- Логистическая ставка (для всех КРОМЕ sea_container) -->
                <div v-if="!isSeaContainer" style="margin-bottom: 12px;">
                    <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px;">
                        <span v-if="isPrologix">Ставка (₽/м³)</span>
                        <span v-else>Логистическая ставка ($/кг)</span>
                        <span v-if="isNewCategory" style="color: #dc2626; margin-left: 4px;">*</span>
                    </label>
                    <input 
                        type="number"
                        step="0.1"
                        v-model.number="editParams.custom_rate"
                        :placeholder="isNewCategory ? (isPrologix ? 'Введите ставку в ₽/м³' : 'Введите ставку в $/кг') : ''"
                        :required="isNewCategory"
                        style="width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                    />
                </div>
                
                <!-- Информация для sea_container (тарифы фиксированные) -->
                <div v-if="isSeaContainer" style="background: #f0fdf4; padding: 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px; color: #047857;">
                    <div style="font-weight: 600; margin-bottom: 4px;">Тарифы на контейнеры фиксированные:</div>
                    <div>• 20-футовый: 1500$ + 180000₽</div>
                    <div>• 40-футовый: 2050$ + 225000₽</div>
                    <div style="margin-top: 4px; font-size: 11px;">Можно изменить только пошлины и НДС ниже</div>
                </div>
                
                <!-- Пошлины и НДС (только для Контракта, Prologix и SeaContainer) -->
                <div v-if="isContract || isPrologix || isSeaContainer">
                    <!-- Тип пошлины -->
                    <div style="margin-bottom: 12px;">
                        <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px;">
                            Тип пошлины
                        </label>
                        <select 
                            v-model="editParams.duty_type" 
                            style="width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px; background: white;"
                        >
                            <option value="percent">Процентные (только %)</option>
                            <option value="specific">Весовые (только EUR/кг)</option>
                            <option value="combined">Комбинированные (% ИЛИ EUR/кг)</option>
                        </select>
                    </div>
                    
                    <!-- Поля пошлин в зависимости от типа -->
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                        <!-- Процентная пошлина (percent или combined) -->
                        <div v-if="editParams.duty_type === 'percent' || editParams.duty_type === 'combined'">
                            <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px;">
                                {{ editParams.duty_type === 'combined' ? 'Процент (%)' : 'Пошлина (%)' }}
                            </label>
                            <input 
                                type="number"
                                step="0.1"
                                v-model.number="editParams.duty_rate"
                                placeholder="10"
                                style="width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                            />
                        </div>
                        
                        <!-- Весовая пошлина (specific или combined) -->
                        <div v-if="editParams.duty_type === 'specific' || editParams.duty_type === 'combined'">
                            <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px;">
                                Весовая 
                                <span style="font-size: 11px; color: #9ca3af;">(EUR/кг)</span>
                            </label>
                            <input 
                                type="number"
                                step="0.1"
                                min="0"
                                v-model.number="editParams.specific_rate"
                                placeholder="2.2"
                                style="width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                            />
                        </div>
                        
                        <!-- НДС (всегда показываем) -->
                        <div>
                            <label style="display: block; font-size: 12px; color: #6b7280; margin-bottom: 4px;">
                                НДС (%)
                            </label>
                            <input 
                                type="number"
                                step="0.1"
                                v-model.number="editParams.vat_rate"
                                placeholder="20"
                                style="width: 100%; padding: 6px 8px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 13px;"
                            />
                        </div>
                    </div>
                    
                    <!-- Подсказка -->
                    <div style="background: #f0f9ff; padding: 8px; border-radius: 4px; margin-bottom: 12px; font-size: 11px; color: #0369a1;">
                        <span v-if="editParams.duty_type === 'percent'">Рассчитывается от таможенной стоимости</span>
                        <span v-if="editParams.duty_type === 'specific'">Рассчитывается по весу товара</span>
                        <span v-if="editParams.duty_type === 'combined'">Рассчитывается оба варианта, применяется больший</span>
                    </div>
                </div>
                
                <!-- Кнопки -->
                <div style="display: flex; gap: 8px; justify-content: flex-end;">
                    <button 
                        @click="cancelEdit"
                        style="padding: 6px 12px; background: white; border: 1px solid #d1d5db; border-radius: 4px; font-size: 12px; color: #6b7280; cursor: pointer;"
                    >
                        Отмена
                    </button>
                    <button 
                        @click="saveEdit"
                        style="padding: 6px 12px; background: #111827; border: none; border-radius: 4px; font-size: 12px; color: white; cursor: pointer; font-weight: 500;"
                    >
                        Применить
                    </button>
                </div>
            </div>
        </div>
    `
};


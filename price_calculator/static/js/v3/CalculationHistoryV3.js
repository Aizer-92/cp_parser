// CalculationHistoryV3.js - История расчетов для позиции
window.CalculationHistoryV3 = {
    props: {
        positionId: Number
    },
    
    data() {
        return {
            calculations: [],
            isLoading: false
        };
    },
    
    mounted() {
        if (this.positionId) {
            this.loadCalculations();
        }
    },
    
    watch: {
        positionId(newId) {
            if (newId) {
                this.loadCalculations();
            }
        }
    },
    
    methods: {
        async loadCalculations() {
            this.isLoading = true;
            
            try {
                // Загружаем позицию с расчетами
                const positionsAPI = window.usePositionsV3();
                const position = await positionsAPI.getPosition(this.positionId);
                
                // Извлекаем массив расчетов
                this.calculations = position.calculations || [];
                
                console.log('✅ История расчетов загружена:', this.calculations.length);
                
            } catch (error) {
                console.error('❌ Ошибка загрузки истории:', error);
                alert('Не удалось загрузить историю расчетов');
            } finally {
                this.isLoading = false;
            }
        },
        
        async openCalculation(calcId) {
            console.log('📂 Открытие расчета:', calcId);
            
            try {
                // Загружаем детали расчета
                const response = await axios.get(`/api/v3/calculations/${calcId}`);
                
                console.log('✅ Расчет загружен');
                
                // Эмитим событие для перехода к результатам
                this.$emit('open-calculation', response.data);
                
            } catch (error) {
                console.error('❌ Ошибка загрузки расчета:', error);
                alert('Не удалось загрузить расчет');
            }
        },
        
        formatDate(dateString) {
            if (!dateString) return '—';
            
            try {
                const date = new Date(dateString);
                return date.toLocaleString('ru-RU', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch {
                return dateString;
            }
        },
        
        formatPrice(value) {
            if (!value) return '0';
            return Number(value).toFixed(2);
        }
    },
    
    template: `
    <div class="calculation-history">
        <h3 style="font-size: 16px; font-weight: 600; margin-bottom: 16px; color: #111827;">
            История расчетов ({{ calculations.length }})
        </h3>
        
        <!-- Состояние загрузки -->
        <div v-if="isLoading" class="loading-state">
            <div class="spinner"></div>
            <p>Загрузка истории...</p>
        </div>
        
        <!-- Список расчетов -->
        <div v-else-if="calculations.length > 0" class="history-list">
            <div
                v-for="calc in calculations"
                :key="calc.id"
                @click="openCalculation(calc.id)"
                class="history-item"
            >
                <div class="history-header">
                    <div>
                        <div class="history-date">
                            {{ formatDate(calc.created_at) }}
                        </div>
                        <div v-if="calc.updated_at && calc.updated_at !== calc.created_at" class="history-updated">
                            Обновлено: {{ formatDate(calc.updated_at) }}
                        </div>
                    </div>
                    <div class="history-arrow">→</div>
                </div>
                
                <div class="history-params">
                    <div class="history-param">
                        <span class="param-label">Количество:</span>
                        <span class="param-value">{{ calc.quantity }} шт</span>
                    </div>
                    <div class="history-param">
                        <span class="param-label">Наценка:</span>
                        <span class="param-value">×{{ calc.markup }}</span>
                    </div>
                    <div v-if="calc.category" class="history-param">
                        <span class="param-label">Категория:</span>
                        <span class="param-value">{{ calc.category }}</span>
                    </div>
                </div>
                
                <!-- Индикатор кастомных параметров -->
                <div v-if="calc.custom_logistics || calc.forced_category" class="history-badges">
                    <span v-if="calc.forced_category" class="history-badge">
                        Категория изменена
                    </span>
                    <span v-if="calc.custom_logistics" class="history-badge">
                        Кастомные ставки
                    </span>
                </div>
            </div>
        </div>
        
        <!-- Пустое состояние -->
        <div v-else class="empty-state">
            <p>История расчетов пуста</p>
            <p style="font-size: 14px; color: #6b7280;">
                Выполните первый расчет для этой позиции
            </p>
        </div>
    </div>
    `
};


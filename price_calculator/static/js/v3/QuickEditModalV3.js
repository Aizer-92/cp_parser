// QuickEditModalV3.js - Быстрое редактирование quantity/markup
window.QuickEditModalV3 = {
    props: {
        calculationId: Number,
        initialQuantity: Number,
        initialMarkup: Number
    },
    
    data() {
        return {
            quantity: this.initialQuantity,
            markup: this.initialMarkup,
            isRecalculating: false
        };
    },
    
    methods: {
        close() {
            this.$emit('close');
        },
        
        async apply() {
            console.log('💾 Быстрое редактирование:', {
                calculationId: this.calculationId,
                quantity: this.quantity,
                markup: this.markup
            });
            
            // Валидация
            if (!this.quantity || this.quantity <= 0) {
                alert('Количество должно быть больше 0');
                return;
            }
            
            if (!this.markup || this.markup <= 0) {
                alert('Наценка должна быть больше 0');
                return;
            }
            
            this.isRecalculating = true;
            
            try {
                // Пересчет через PUT API
                const response = await axios.put(
                    `/api/v3/calculations/${this.calculationId}`,
                    {
                        quantity: parseInt(this.quantity),
                        markup: parseFloat(this.markup)
                    }
                );
                
                console.log('✅ Пересчет выполнен');
                
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
        <div class="modal-content" style="max-width: 400px;">
            <!-- Заголовок -->
            <div class="modal-header">
                <h3>Быстрое редактирование</h3>
                <button @click="close" class="btn-close">×</button>
            </div>
            
            <!-- Форма -->
            <div class="modal-body">
                <div class="form-group">
                    <label>Количество (шт)</label>
                    <input
                        v-model.number="quantity"
                        type="number"
                        min="1"
                        step="1"
                        class="form-input"
                        placeholder="Например: 1000"
                        :disabled="isRecalculating"
                    />
                </div>
                
                <div class="form-group">
                    <label>Наценка (множитель)</label>
                    <input
                        v-model.number="markup"
                        type="number"
                        min="0.01"
                        step="0.01"
                        class="form-input"
                        placeholder="Например: 1.7"
                        :disabled="isRecalculating"
                    />
                    <div class="form-hint">
                        Например: 1.7 = 70% прибыли, 2.0 = 100% прибыли
                    </div>
                </div>
            </div>
            
            <!-- Кнопки -->
            <div class="modal-footer">
                <button
                    @click="apply"
                    :disabled="isRecalculating"
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


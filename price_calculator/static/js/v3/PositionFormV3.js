// PositionFormV3.js - Пошаговая форма создания позиции (как в V2)
window.PositionFormV3 = {
    template: `
    <div class="position-form-overlay" @click.self="close">
        <div class="position-form-modal" style="max-width: 800px;">
            <div class="modal-header">
                <div>
                    <h2>{{ isEdit ? 'Редактировать позицию' : 'Создать позицию' }}</h2>
                    <div class="step-indicator">
                        Шаг {{ currentStep }} из 3
                    </div>
                </div>
                <button @click="close" class="btn-close">×</button>
            </div>
            
            <form @submit.prevent="handleSubmit" class="form">
                <!-- ШАГ 1: Основная информация -->
                <div v-show="currentStep === 1" class="step-content">
                    <h3 class="step-title">Основная информация о товаре</h3>
                    
                    <div class="form-group">
                        <label for="name">Название товара *</label>
                        <input
                            id="name"
                            v-model="form.name"
                            type="text"
                            placeholder="Например: Футболка хлопковая"
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="category">Категория *</label>
                        <input
                            id="category"
                            v-model="form.category"
                            type="text"
                            placeholder="футболка, кружка, рюкзак..."
                            required
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Описание товара</label>
                        <textarea
                            id="description"
                            v-model="form.description"
                            rows="3"
                            placeholder="Краткое описание товара..."
                            class="form-input"
                        ></textarea>
                    </div>
                </div>
                
                <!-- ШАГ 2: Фабрика и стоимость -->
                <div v-show="currentStep === 2" class="step-content">
                    <h3 class="step-title">Данные от фабрики</h3>
                    
                    <div class="form-group">
                        <label for="factory">Фабрика (WeChat / URL)</label>
                        <input
                            id="factory"
                            v-model="form.factory_url"
                            type="text"
                            placeholder="https://... или WeChat ID"
                            class="form-input"
                        />
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="price">Цена (¥)</label>
                            <input
                                id="price"
                                v-model.number="form.price_yuan"
                                type="number"
                                step="0.01"
                                min="0"
                                placeholder="125.00"
                                class="form-input"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="weight">Вес единицы (кг)</label>
                            <input
                                id="weight"
                                v-model.number="form.weight_kg"
                                type="number"
                                step="0.01"
                                min="0"
                                placeholder="0.2"
                                class="form-input"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- ШАГ 3: Кастомизация и фото -->
                <div v-show="currentStep === 3" class="step-content">
                    <h3 class="step-title">Кастомизация и материалы</h3>
                    
                    <div class="form-group">
                        <label for="customization">Кастомизация товара</label>
                        <textarea
                            id="customization"
                            v-model="form.customization"
                            rows="3"
                            placeholder="Требования к кастомизации (печать, гравировка и т.д.)"
                            class="form-input"
                        ></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Фотографии товара (URL)</label>
                        <input
                            v-model="photoUrl"
                            type="url"
                            placeholder="https://example.com/photo.jpg"
                            class="form-input"
                            @keyup.enter="addPhoto"
                        />
                        <button type="button" @click="addPhoto" class="btn-secondary btn-sm" style="margin-top: 8px;">
                            Добавить фото
                        </button>
                        
                        <div v-if="form.design_files_urls.length > 0" class="photo-list">
                            <div v-for="(url, index) in form.design_files_urls" :key="index" class="photo-item">
                                <img :src="url" :alt="'Фото ' + (index + 1)" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px;" />
                                <span class="photo-url">{{ truncateUrl(url) }}</span>
                                <button type="button" @click="removePhoto(index)" class="btn-remove">×</button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Навигация -->
                <div class="form-actions" style="justify-content: space-between;">
                    <button type="button" @click="prevStep" v-if="currentStep > 1" class="btn-secondary">
                        ← Назад
                    </button>
                    <button type="button" @click="close" class="btn-secondary">
                        Отмена
                    </button>
                    <div style="display: flex; gap: 12px;">
                        <button type="button" @click="nextStep" v-if="currentStep < 3" class="btn-primary">
                            Далее →
                        </button>
                        <button type="submit" v-if="currentStep === 3" :disabled="isSaving" class="btn-primary">
                            {{ isSaving ? 'Сохранение...' : 'Сохранить позицию' }}
                        </button>
                    </div>
                </div>
            </form>
        </div>
    </div>
    `,
    
    props: {
        position: {
            type: Object,
            default: null
        }
    },
    
    data() {
        return {
            currentStep: 1,
            form: {
                name: '',
                category: '',
                description: '',
                factory_url: '',
                price_yuan: null,
                weight_kg: null,
                customization: '',
                design_files_urls: []
            },
            photoUrl: '',
            isSaving: false
        };
    },
    
    computed: {
        isEdit() {
            return !!this.position;
        }
    },
    
    mounted() {
        if (this.position) {
            this.form = { 
                ...this.position,
                design_files_urls: this.position.design_files_urls || []
            };
        }
    },
    
    methods: {
        nextStep() {
            // Валидация шага 1
            if (this.currentStep === 1) {
                if (!this.form.name || !this.form.category) {
                    alert('Заполните обязательные поля');
                    return;
                }
            }
            
            this.currentStep++;
        },
        
        prevStep() {
            this.currentStep--;
        },
        
        handleSubmit() {
            if (this.currentStep === 3) {
                this.save();
            }
        },
        
        async save() {
            this.isSaving = true;
            try {
                const positionsAPI = window.usePositionsV3();
                
                // Подготавливаем данные (убираем null значения)
                const data = { ...this.form };
                Object.keys(data).forEach(key => {
                    if (data[key] === null || data[key] === '') {
                        delete data[key];
                    }
                });
                
                if (this.isEdit) {
                    await positionsAPI.updatePosition(this.position.id, data);
                    console.log('✅ Позиция обновлена');
                } else {
                    await positionsAPI.createPosition(data);
                    console.log('✅ Позиция создана');
                }
                
                this.$emit('saved');
                this.close();
            } catch (error) {
                console.error('❌ Ошибка сохранения:', error);
                alert('Не удалось сохранить позицию');
            } finally {
                this.isSaving = false;
            }
        },
        
        addPhoto() {
            if (this.photoUrl && this.photoUrl.trim()) {
                this.form.design_files_urls.push(this.photoUrl.trim());
                this.photoUrl = '';
            }
        },
        
        removePhoto(index) {
            this.form.design_files_urls.splice(index, 1);
        },
        
        truncateUrl(url) {
            return url.length > 50 ? url.substring(0, 47) + '...' : url;
        },
        
        close() {
            this.$emit('close');
        }
    }
};

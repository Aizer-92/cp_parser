// PositionFormV3.js - Полноэкранная пошаговая форма создания позиции
window.PositionFormV3 = {
    template: `
    <div class="position-form-fullscreen">
        <div class="fullscreen-content">
            <div class="modal-header">
                <div>
                    <h2>{{ isEdit ? 'Редактировать позицию' : 'Создать позицию' }}</h2>
                    <div class="step-indicator">
                        Шаг {{ currentStep }} из 2
                    </div>
                </div>
                <button @click="close" class="btn-close">×</button>
            </div>
            
            <form @submit.prevent="handleSubmit" class="form">
                <!-- ШАГ 1: Основная информация + Фото + Кастомизация -->
                <div v-show="currentStep === 1" class="step-content">
                    <h3 class="step-title">Основная информация о товаре</h3>
                    
                    <div class="form-row">
                        <!-- Левая колонка: основные поля -->
                        <div style="flex: 1; padding-right: 20px;">
                            <div class="form-group">
                                <label for="name">Название товара *</label>
                                <input
                                    id="name"
                                    v-model="form.name"
                                    type="text"
                                    placeholder="Например: Футболка хлопковая"
                                    required
                                    class="form-input"
                                    @input="detectCategory"
                                />
                            </div>
                            
                            <div class="form-group">
                                <label for="category">Категория * <span style="font-size: 12px; color: #9ca3af;">(автоопределяется)</span></label>
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
                            
                            <div class="form-group">
                                <label for="customization">Кастомизация товара</label>
                                <textarea
                                    id="customization"
                                    v-model="form.customization"
                                    rows="2"
                                    placeholder="Требования к кастомизации (печать, гравировка и т.д.)"
                                    class="form-input"
                                ></textarea>
                            </div>
                        </div>
                        
                        <!-- Правая колонка: фотографии -->
                        <div style="flex: 1;">
                            <div class="form-group">
                                <label>Фотографии товара</label>
                                <div 
                                    class="photo-dropzone"
                                    @drop.prevent="handleDrop"
                                    @dragover.prevent
                                    @dragenter.prevent="isDragging = true"
                                    @dragleave.prevent="isDragging = false"
                                    :class="{ 'dragging': isDragging }"
                                >
                                    <div v-if="form.design_files_urls.length === 0" class="dropzone-placeholder">
                                        <div style="text-align: center; width: 100%;">
                                            <div style="font-size: 14px; color: #6b7280; margin-bottom: 16px;">
                                                Перетащите фото сюда, выберите файл<br>или введите ссылку
                                            </div>
                                            <input
                                                type="file"
                                                accept="image/*"
                                                multiple
                                                @change="handleFileSelect"
                                                style="display: none;"
                                                :ref="el => fileInputRef = el"
                                            />
                                            <button type="button" @click="triggerFileInput" class="btn-primary" style="margin-bottom: 12px; width: 100%;">
                                                📁 Выбрать файлы с компьютера
                                            </button>
                                            <div style="display: flex; gap: 8px; align-items: center;">
                                                <input
                                                    v-model="photoUrl"
                                                    type="url"
                                                    placeholder="Или вставьте ссылку на фото"
                                                    class="form-input"
                                                    @keyup.enter="addPhoto"
                                                    style="flex: 1;"
                                                />
                                                <button type="button" @click="addPhoto" class="btn-secondary">
                                                    + Ссылка
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <div v-else class="photo-grid">
                                        <div v-for="(url, index) in form.design_files_urls" :key="index" class="photo-preview">
                                            <img :src="url" :alt="'Фото ' + (index + 1)" />
                                            <span v-if="index === 0" class="main-badge">основная</span>
                                            <button type="button" @click="removePhoto(index)" class="btn-remove-photo">×</button>
                                        </div>
                                        <div class="photo-add-more">
                                            <input
                                                type="file"
                                                accept="image/*"
                                                multiple
                                                @change="handleFileSelect"
                                                style="display: none;"
                                                :ref="el => fileInputMoreRef = el"
                                            />
                                            <button type="button" @click="triggerFileInputMore" class="btn-primary btn-sm" style="margin-bottom: 8px; width: 100%;">
                                                📁 Файл
                                            </button>
                                            <input
                                                v-model="photoUrl"
                                                type="url"
                                                placeholder="Ссылка"
                                                class="form-input"
                                                @keyup.enter="addPhoto"
                                                style="font-size: 12px; margin-bottom: 4px;"
                                            />
                                            <button type="button" @click="addPhoto" class="btn-secondary btn-sm" style="width: 100%;">+ Ссылка</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- ШАГ 2: Фабрика, цена и паккинг -->
                <div v-show="currentStep === 2" class="step-content">
                    <h3 class="step-title">Данные от фабрики и паккинг товара</h3>
                    
                    <div class="form-row">
                        <!-- Левая колонка: фабрика и цена -->
                        <div style="flex: 1; padding-right: 20px;">
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
                            
                            <div class="form-group">
                                <label for="price">Цена в юанях *</label>
                                <input
                                    id="price"
                                    v-model.number="form.price_yuan"
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    required
                                    placeholder="125.00"
                                    class="form-input"
                                />
                            </div>
                            
                            <div class="form-group" style="margin-top: 20px;">
                                <label>
                                    <input type="checkbox" v-model="useSimpleWeight" />
                                    <span style="margin-left: 8px;">Указать только вес единицы (без паккинга)</span>
                                </label>
                            </div>
                            
                            <div v-if="useSimpleWeight" class="form-group">
                                <label for="weight_kg">Вес единицы товара (кг) *</label>
                                <input
                                    id="weight_kg"
                                    v-model.number="form.weight_kg"
                                    type="number"
                                    step="0.001"
                                    min="0"
                                    required
                                    placeholder="0.25"
                                    class="form-input"
                                />
                            </div>
                        </div>
                        
                        <!-- Правая колонка: паккинг -->
                        <div style="flex: 1;">
                            <div v-if="!useSimpleWeight" class="packing-section">
                                <h4 style="margin-bottom: 16px; font-size: 16px; font-weight: 600;">Паккинг товара (рекомендуется)</h4>
                                
                                <div class="form-group">
                                    <label for="box_length">Длина коробки (см) *</label>
                                    <input
                                        id="box_length"
                                        v-model.number="form.packing_box_length"
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        :required="!useSimpleWeight"
                                        placeholder="50"
                                        class="form-input"
                                    />
                                </div>
                                
                                <div class="form-group">
                                    <label for="box_width">Ширина коробки (см) *</label>
                                    <input
                                        id="box_width"
                                        v-model.number="form.packing_box_width"
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        :required="!useSimpleWeight"
                                        placeholder="40"
                                        class="form-input"
                                    />
                                </div>
                                
                                <div class="form-group">
                                    <label for="box_height">Высота коробки (см) *</label>
                                    <input
                                        id="box_height"
                                        v-model.number="form.packing_box_height"
                                        type="number"
                                        step="0.1"
                                        min="0"
                                        :required="!useSimpleWeight"
                                        placeholder="30"
                                        class="form-input"
                                    />
                                </div>
                                
                                <div class="form-group">
                                    <label for="box_weight">Вес коробки (кг) *</label>
                                    <input
                                        id="box_weight"
                                        v-model.number="form.packing_box_weight"
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        :required="!useSimpleWeight"
                                        placeholder="12.5"
                                        class="form-input"
                                    />
                                </div>
                                
                                <div class="form-group">
                                    <label for="units_per_box">Штук в коробке *</label>
                                    <input
                                        id="units_per_box"
                                        v-model.number="form.packing_units_per_box"
                                        type="number"
                                        step="1"
                                        min="1"
                                        :required="!useSimpleWeight"
                                        placeholder="50"
                                        class="form-input"
                                    />
                                </div>
                                
                                <div v-if="calculatedWeight > 0" class="calculated-info">
                                    ℹ Расчетный вес единицы: <strong>{{ calculatedWeight.toFixed(3) }} кг</strong>
                                </div>
                            </div>
                            <div v-else style="padding: 40px; text-align: center; color: #9ca3af;">
                                <div style="font-size: 14px;">Паккинг не используется</div>
                                <div style="font-size: 12px; margin-top: 8px;">Будет использован указанный вес единицы</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Навигация -->
                <div class="form-actions" style="justify-content: space-between; margin-top: 30px;">
                    <div>
                        <button type="button" @click="prevStep" v-if="currentStep > 1" class="btn-secondary">
                            ← Назад
                        </button>
                    </div>
                    <div style="display: flex; gap: 12px;">
                        <button type="button" @click="close" class="btn-secondary">
                            Отмена
                        </button>
                        <button type="button" @click="nextStep" v-if="currentStep < 2" class="btn-primary">
                            Далее →
                        </button>
                        <button type="submit" v-if="currentStep === 2" :disabled="isSaving" class="btn-primary">
                            {{ isSaving ? 'Сохранение...' : (isEdit ? 'Обновить позицию' : 'Создать позицию') }}
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
            useSimpleWeight: false,
            isDragging: false,
            availableCategories: [],
            fileInputRef: null,
            fileInputMoreRef: null,
            form: {
                name: '',
                category: '',
                description: '',
                factory_url: '',
                price_yuan: null,
                weight_kg: null,
                customization: '',
                design_files_urls: [],
                // Паккинг (опционально)
                packing_box_length: null,
                packing_box_width: null,
                packing_box_height: null,
                packing_box_weight: null,
                packing_units_per_box: null
            },
            photoUrl: '',
            isSaving: false
        };
    },
    
    computed: {
        isEdit() {
            return !!this.position;
        },
        
        calculatedWeight() {
            if (!this.useSimpleWeight && 
                this.form.packing_box_weight && 
                this.form.packing_units_per_box && 
                this.form.packing_units_per_box > 0) {
                return this.form.packing_box_weight / this.form.packing_units_per_box;
            }
            return 0;
        }
    },
    
    async mounted() {
        // Загружаем категории для автоопределения
        await this.loadCategories();
        
        if (this.position) {
            this.form = { 
                ...this.position,
                design_files_urls: this.position.design_files_urls || []
            };
            
            // Определяем режим: если есть паккинг - показываем его
            if (this.position.packing_units_per_box) {
                this.useSimpleWeight = false;
            } else {
                this.useSimpleWeight = true;
            }
        }
    },
    
    methods: {
        nextStep() {
            // Валидация шага 1
            if (this.currentStep === 1) {
                if (!this.form.name || !this.form.category) {
                    alert('Заполните обязательные поля: название и категорию');
                    return;
                }
            }
            
            // Валидация шага 2
            if (this.currentStep === 2) {
                if (!this.form.price_yuan || this.form.price_yuan <= 0) {
                    alert('Укажите цену в юанях');
                    return;
                }
                
                if (this.useSimpleWeight) {
                    if (!this.form.weight_kg || this.form.weight_kg <= 0) {
                        alert('Укажите вес единицы товара');
                        return;
                    }
                } else {
                    if (!this.form.packing_box_length || !this.form.packing_box_width || 
                        !this.form.packing_box_height || !this.form.packing_box_weight || 
                        !this.form.packing_units_per_box) {
                        alert('Заполните все поля паккинга');
                        return;
                    }
                }
            }
            
            this.currentStep++;
        },
        
        prevStep() {
            this.currentStep--;
        },
        
        handleSubmit() {
            if (this.currentStep === 2) {
                this.save();
            }
        },
        
        async save() {
            this.isSaving = true;
            try {
                const positionsAPI = window.usePositionsV3();
                
                // Подготавливаем данные
                const data = { ...this.form };
                
                // Если используем простой вес - очищаем паккинг
                if (this.useSimpleWeight) {
                    data.packing_box_length = null;
                    data.packing_box_width = null;
                    data.packing_box_height = null;
                    data.packing_box_weight = null;
                    data.packing_units_per_box = null;
                } else {
                    // Если используем паккинг - вычисляем weight_kg
                    data.weight_kg = this.calculatedWeight;
                }
                
                // Убираем null/пустые значения
                Object.keys(data).forEach(key => {
                    if (data[key] === null || data[key] === '') {
                        delete data[key];
                    }
                });
                
                let savedPosition;
                if (this.isEdit) {
                    savedPosition = await positionsAPI.updatePosition(this.position.id, data);
                    console.log('✅ Позиция обновлена');
                } else {
                    savedPosition = await positionsAPI.createPosition(data);
                    console.log('✅ Позиция создана:', savedPosition);
                }
                
                // После создания/обновления - сразу запускаем расчет
                if (!this.isEdit) {
                    this.$emit('saved', savedPosition);
                    this.$emit('calculate-routes', savedPosition);
                } else {
                    this.$emit('saved');
                }
                
                this.close();
            } catch (error) {
                console.error('❌ Ошибка сохранения:', error);
                const errorMsg = error.response?.data?.detail || error.message || 'Не удалось сохранить позицию';
                alert(`Ошибка: ${errorMsg}`);
            } finally {
                this.isSaving = false;
            }
        },
        
        async loadCategories() {
            try {
                const response = await axios.get('/api/v3/categories');
                const data = response.data;
                
                // Обрабатываем разные форматы ответа
                if (Array.isArray(data)) {
                    this.availableCategories = data;
                } else if (data.categories && Array.isArray(data.categories)) {
                    this.availableCategories = data.categories;
                } else {
                    this.availableCategories = [];
                }
                
                console.log('✅ Категории загружены:', this.availableCategories);
            } catch (error) {
                console.error('❌ Ошибка загрузки категорий:', error);
            }
        },
        
        detectCategory() {
            if (!this.form.name || this.form.name.length < 3) return;
            
            const name = this.form.name.toLowerCase().trim();
            
            // Список категорий из availableCategories
            const categories = this.availableCategories.map(c => {
                if (typeof c === 'string') return c.toLowerCase();
                if (c.category) return c.category.toLowerCase();
                return '';
            }).filter(c => c);
            
            console.log('🔍 Поиск категории для:', name, 'в списке:', categories);
            
            // Ищем точное совпадение или вхождение
            for (const category of categories) {
                if (!category) continue;
                
                // Если категория содержится в названии
                if (name.includes(category)) {
                    this.form.category = category;
                    console.log('✅ Категория автоопределена:', category);
                    return;
                }
                
                // Или если название содержится в категории
                if (category.includes(name)) {
                    this.form.category = category;
                    console.log('✅ Категория автоопределена:', category);
                    return;
                }
            }
            
            console.log('⚠️ Категория не найдена для:', name);
        },
        
        triggerFileInput() {
            if (this.fileInputRef) {
                this.fileInputRef.click();
            }
        },
        
        triggerFileInputMore() {
            if (this.fileInputMoreRef) {
                this.fileInputMoreRef.click();
            }
        },
        
        handleDrop(e) {
            this.isDragging = false;
            
            // Проверяем файлы
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                this.handleFileUpload(e.dataTransfer.files);
                return;
            }
            
            // Проверяем URL
            const url = e.dataTransfer.getData('text/plain');
            if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
                this.form.design_files_urls.push(url);
            } else {
                alert('Пожалуйста, перетащите изображение или ссылку на него');
            }
        },
        
        handleFileSelect(e) {
            const files = e.target.files;
            if (files && files.length > 0) {
                this.handleFileUpload(files);
            }
        },
        
        async handleFileUpload(files) {
            console.log('📤 Загрузка файлов:', files.length);
            
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                
                // Проверка типа файла
                if (!file.type.startsWith('image/')) {
                    alert(`Файл ${file.name} не является изображением`);
                    continue;
                }
                
                try {
                    // Создаем FormData для загрузки
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('folder', 'calc');
                    
                    // Загружаем на SFTP
                    const response = await axios.post('/api/sftp/upload', formData, {
                        headers: { 'Content-Type': 'multipart/form-data' }
                    });
                    
                    if (response.data.url) {
                        this.form.design_files_urls.push(response.data.url);
                        console.log('✅ Фото загружено:', response.data.url);
                    }
                } catch (error) {
                    console.error('❌ Ошибка загрузки фото:', error);
                    alert(`Не удалось загрузить ${file.name}`);
                }
            }
        },
        
        addPhoto() {
            if (this.photoUrl && this.photoUrl.trim()) {
                const url = this.photoUrl.trim();
                if (url.startsWith('http://') || url.startsWith('https://')) {
                    this.form.design_files_urls.push(url);
                    this.photoUrl = '';
                } else {
                    alert('Введите корректную ссылку (начинается с http:// или https://)');
                }
            }
        },
        
        removePhoto(index) {
            this.form.design_files_urls.splice(index, 1);
        },
        
        close() {
            this.$emit('close');
        }
    }
};

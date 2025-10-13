// PositionFormV3.js - Форма создания/редактирования позиции
window.PositionFormV3 = {
    props: {
        positionId: {
            type: Number,
            default: null
        }
    },
    
    template: `
    <div class="position-form">
        <div class="card">
            <div class="card-header">
                <h2 class="card-title">
                    {{ positionId ? 'Редактирование позиции' : 'Новая позиция' }}
                </h2>
                <button @click="cancel" class="btn-text">Отмена</button>
            </div>
            
            <form @submit.prevent="save" class="form">
                <!-- Основная информация -->
                <div class="form-section">
                    <h3>Основная информация</h3>
                    
                    <div class="form-group">
                        <label for="name">Название *</label>
                        <input
                            id="name"
                            v-model="form.name"
                            type="text"
                            required
                            class="form-input"
                            placeholder="Например: Футболка хлопковая с принтом"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="category">Категория</label>
                        <input
                            id="category"
                            v-model="form.category"
                            type="text"
                            list="categories-list"
                            class="form-input"
                            placeholder="Например: футболка"
                        />
                        <datalist id="categories-list">
                            <option v-for="cat in availableCategories" :key="cat" :value="cat">
                        </datalist>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Описание</label>
                        <textarea
                            id="description"
                            v-model="form.description"
                            rows="3"
                            class="form-input"
                            placeholder="Описание товара: материал, размеры, вес..."
                        ></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="customization">Кастомизация</label>
                        <textarea
                            id="customization"
                            v-model="form.customization"
                            rows="3"
                            class="form-input"
                            placeholder="Кастомизация: печать, гравировка, упаковка..."
                        ></textarea>
                    </div>
                </div>
                
                <!-- Фотографии -->
                <div class="form-section">
                    <h3>Фотографии</h3>
                    
                    <div
                        class="photo-dropzone"
                        :class="{ 'dropzone-active': isDragging }"
                        @drop.prevent="onDrop"
                        @dragover.prevent="isDragging = true"
                        @dragleave.prevent="isDragging = false"
                        @click="$refs.fileInput.click()"
                    >
                        <p>Перетащите фото сюда или нажмите для выбора</p>
                        <input
                            ref="fileInput"
                            type="file"
                            accept="image/*"
                            multiple
                            style="display: none"
                            @change="onFileSelect"
                        />
                    </div>
                    
                    <!-- Превью фотографий -->
                    <div v-if="photos.length > 0" class="photos-preview">
                        <div
                            v-for="(photo, index) in photos"
                            :key="index"
                            class="photo-item"
                        >
                            <img :src="photo.preview" :alt="'Фото ' + (index + 1)" />
                            <div class="photo-overlay">
                                <button
                                    v-if="index === mainPhotoIndex"
                                    type="button"
                                    class="photo-badge"
                                >
                                    Основная
                                </button>
                                <button
                                    v-else
                                    type="button"
                                    @click="setMainPhoto(index)"
                                    class="photo-badge secondary"
                                >
                                    Сделать основной
                                </button>
                                <button
                                    type="button"
                                    @click="removePhoto(index)"
                                    class="photo-remove"
                                >
                                    ×
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <p v-if="uploadProgress > 0 && uploadProgress < 100" class="upload-progress">
                        Загрузка: {{ uploadProgress }}%
                    </p>
                </div>
                
                <!-- Дополнительно -->
                <div class="form-section">
                    <h3>Дополнительно</h3>
                    
                    <div class="form-row">
                        <div class="form-group flex-1">
                            <label for="material">Материал</label>
                            <input
                                id="material"
                                v-model="form.material"
                                type="text"
                                class="form-input"
                                placeholder="cotton"
                            />
                        </div>
                        
                        <div class="form-group flex-1">
                            <label for="colors">Цвета</label>
                            <input
                                id="colors"
                                v-model="form.colors"
                                type="text"
                                class="form-input"
                                placeholder="white, black"
                            />
                        </div>
                    </div>
                </div>
                
                <!-- Кнопки -->
                <div class="form-actions">
                    <button type="button" @click="cancel" class="btn-secondary">
                        Отмена
                    </button>
                    <button type="submit" :disabled="isSaving" class="btn-primary">
                        {{ isSaving ? 'Сохранение...' : 'Сохранить' }}
                    </button>
                </div>
            </form>
        </div>
    </div>
    `,
    
    data() {
        return {
            form: {
                name: '',
                category: '',
                description: '',
                customization: '',
                material: '',
                colors: ''
            },
            
            photos: [],
            mainPhotoIndex: 0,
            isDragging: false,
            isSaving: false,
            uploadProgress: 0,
            
            availableCategories: []
        };
    },
    
    async mounted() {
        await this.loadCategories();
        if (this.positionId) {
            await this.loadPosition();
        }
    },
    
    methods: {
        async loadCategories() {
            try {
                const v3 = window.useCalculationV3();
                const categories = await v3.getCategories();
                this.availableCategories = categories.map(c => c.category || c.name || c);
            } catch (error) {
                console.error('Ошибка загрузки категорий:', error);
            }
        },
        
        async loadPosition() {
            try {
                const api = window.usePositionsV3();
                const position = await api.getPosition(this.positionId);
                
                this.form.name = position.name;
                this.form.category = position.category || '';
                this.form.description = position.description || '';
                
                // Загружаем custom_fields
                if (position.custom_fields) {
                    this.form.customization = position.custom_fields.customization || '';
                    this.form.material = position.custom_fields.material || '';
                    this.form.colors = position.custom_fields.colors || '';
                }
                
                // Загружаем фото
                if (position.design_files_urls && position.design_files_urls.length > 0) {
                    this.photos = position.design_files_urls.map(url => ({
                        url: url,
                        preview: url,
                        isUploaded: true
                    }));
                }
            } catch (error) {
                console.error('Ошибка загрузки позиции:', error);
                alert('Не удалось загрузить позицию');
            }
        },
        
        onFileSelect(event) {
            const files = Array.from(event.target.files);
            this.addFiles(files);
        },
        
        onDrop(event) {
            this.isDragging = false;
            const files = Array.from(event.dataTransfer.files);
            this.addFiles(files);
        },
        
        async addFiles(files) {
            const uploadApi = window.useSFTPUpload();
            
            for (const file of files) {
                // Валидация
                if (!uploadApi.isValidImage(file)) continue;
                
                // Создаём превью
                const preview = await uploadApi.createPreview(file);
                
                this.photos.push({
                    file: file,
                    preview: preview,
                    isUploaded: false
                });
            }
        },
        
        setMainPhoto(index) {
            this.mainPhotoIndex = index;
        },
        
        removePhoto(index) {
            this.photos.splice(index, 1);
            if (this.mainPhotoIndex >= this.photos.length) {
                this.mainPhotoIndex = 0;
            }
        },
        
        async save() {
            if (!this.form.name) {
                alert('Заполните название позиции');
                return;
            }
            
            this.isSaving = true;
            this.uploadProgress = 0;
            
            try {
                const api = window.usePositionsV3();
                
                // Сначала создаём/обновляем позицию без фото
                const positionData = {
                    name: this.form.name,
                    category: this.form.category,
                    description: this.form.description,
                    custom_fields: {
                        customization: this.form.customization,
                        material: this.form.material,
                        colors: this.form.colors
                    },
                    photo_urls: []
                };
                
                let position;
                if (this.positionId) {
                    position = await api.updatePosition(this.positionId, positionData);
                } else {
                    position = await api.createPosition(positionData);
                }
                
                // Загружаем фото на SFTP
                const uploadApi = window.useSFTPUpload();
                const photoUrls = [];
                
                for (let i = 0; i < this.photos.length; i++) {
                    const photo = this.photos[i];
                    
                    if (photo.isUploaded) {
                        // Фото уже загружено
                        photoUrls.push(photo.url);
                    } else {
                        // Загружаем новое фото
                        this.uploadProgress = Math.round((i / this.photos.length) * 100);
                        const url = await uploadApi.uploadPhoto(photo.file, position.id);
                        photoUrls.push(url);
                    }
                }
                
                // Переставляем основное фото на первое место
                if (this.mainPhotoIndex > 0) {
                    const mainPhoto = photoUrls[this.mainPhotoIndex];
                    photoUrls.splice(this.mainPhotoIndex, 1);
                    photoUrls.unshift(mainPhoto);
                }
                
                // Обновляем позицию с фото
                if (photoUrls.length > 0) {
                    await api.updatePosition(position.id, {
                        photo_urls: photoUrls
                    });
                }
                
                this.uploadProgress = 100;
                alert('Позиция сохранена!');
                this.$emit('saved', position.id);
                
            } catch (error) {
                console.error('Ошибка сохранения:', error);
                alert(`Ошибка: ${error.message || 'Не удалось сохранить позицию'}`);
            } finally {
                this.isSaving = false;
            }
        },
        
        cancel() {
            this.$emit('cancel');
        }
    }
};


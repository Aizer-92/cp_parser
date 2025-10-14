/**
 * Template для PositionFormV3
 * 
 * Полноэкранная 2-шаговая форма создания/редактирования позиции
 * Шаг 1: Основная информация + Фото + Кастомизация
 * Шаг 2: Фабрика + Цена + Паккинг товара
 */
export const POSITION_FORM_TEMPLATE = `
<div class="position-form-fullscreen">
    <div class="fullscreen-content">
        <!-- ============================================ -->
        <!--  ЗАГОЛОВОК ФОРМЫ                            -->
        <!-- ============================================ -->
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
            <!-- ============================================ -->
            <!--  ШАГ 1: ОСНОВНАЯ ИНФОРМАЦИЯ                 -->
            <!-- ============================================ -->
            <div v-show="currentStep === 1" class="step-content">
                <h3 class="step-title">Основная информация о товаре</h3>
                
                <div class="form-row">
                    <!-- Левая колонка: основные поля -->
                    <div style="flex: 1; padding-right: 20px;">
                        <!-- Название товара -->
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
                        
                        <!-- Категория (автоопределяется) -->
                        <div class="form-group">
                            <label for="category">
                                Категория *
                                <span style="font-size: 12px; color: #9ca3af;">(автоопределяется)</span>
                            </label>
                            <input
                                id="category"
                                v-model="form.category"
                                type="text"
                                placeholder="футболка, кружка, рюкзак..."
                                required
                                class="form-input"
                            />
                        </div>
                        
                        <!-- Описание товара -->
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
                        
                        <!-- Кастомизация -->
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
                                <!-- Пустое состояние -->
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
                                        <button
                                            type="button"
                                            @click="triggerFileInput"
                                            class="btn-primary"
                                            style="margin-bottom: 12px; width: 100%;"
                                        >
                                            Выбрать файлы с компьютера
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
                                
                                <!-- Сетка фотографий -->
                                <div v-else class="photo-grid">
                                    <div v-for="(url, index) in form.design_files_urls" :key="index" class="photo-preview">
                                        <img :src="url" :alt="'Фото ' + (index + 1)" />
                                        <span v-if="index === 0" class="main-badge">основная</span>
                                        <button type="button" @click="removePhoto(index)" class="btn-remove-photo">×</button>
                                    </div>
                                    
                                    <!-- Кнопка добавить еще -->
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
                                            Файл
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
            
            <!-- ============================================ -->
            <!--  ШАГ 2: ФАБРИКА, ЦЕНА И ПАККИНГ             -->
            <!-- ============================================ -->
            <div v-show="currentStep === 2" class="step-content">
                <h3 class="step-title">Данные от фабрики и паккинг товара</h3>
                
                <div class="form-row">
                    <!-- Левая колонка: фабрика и цена -->
                    <div style="flex: 1; padding-right: 20px;">
                        <!-- Фабрика -->
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
                        
                        <!-- Цена в юанях -->
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
                        
                        <!-- Переключатель: Вес / Паккинг -->
                        <div class="form-group" style="margin-top: 20px;">
                            <label>
                                <input type="checkbox" v-model="useSimpleWeight" />
                                <span style="margin-left: 8px;">Указать только вес единицы (без паккинга)</span>
                            </label>
                        </div>
                        
                        <!-- Простой вес (если выбрано) -->
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
                        <!-- Детальный паккинг -->
                        <div v-if="!useSimpleWeight" class="packing-section">
                            <h4 style="margin-bottom: 16px; font-size: 16px; font-weight: 600;">
                                Паккинг товара (рекомендуется)
                            </h4>
                            
                            <!-- Длина коробки -->
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
                            
                            <!-- Ширина коробки -->
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
                            
                            <!-- Высота коробки -->
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
                            
                            <!-- Вес коробки -->
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
                            
                            <!-- Штук в коробке -->
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
                            
                            <!-- Расчетный вес -->
                            <div v-if="calculatedWeight > 0" class="calculated-info">
                                ℹ Расчетный вес единицы: <strong>{{ calculatedWeight.toFixed(3) }} кг</strong>
                            </div>
                        </div>
                        
                        <!-- Placeholder если простой вес -->
                        <div v-else style="padding: 40px; text-align: center; color: #9ca3af;">
                            <div style="font-size: 14px;">Паккинг не используется</div>
                            <div style="font-size: 12px; margin-top: 8px;">Будет использован указанный вес единицы</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- ============================================ -->
            <!--  НАВИГАЦИЯ                                   -->
            <!-- ============================================ -->
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
`;


/**
 * PositionFormV3.js - Полноэкранная пошаговая форма создания позиции
 * 
 * ✅ РЕФАКТОРИНГ: Template вынесен в отдельный файл
 * @see ./templates/position-form.template.js
 */

// Импорт template (ES module)
import { POSITION_FORM_TEMPLATE } from './templates/position-form.template.js';

window.PositionFormV3 = {
    // ============================================
    // TEMPLATE (вынесен в отдельный файл)
    // ============================================
    template: POSITION_FORM_TEMPLATE,
    
    
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
                
                // Убираем null/пустые значения (но НЕ 0!)
                Object.keys(data).forEach(key => {
                    if (data[key] === null || data[key] === '') {
                        delete data[key];
                    }
                });
                
                // КРИТИЧНО: price_yuan обязательно должен быть
                if (!data.price_yuan || data.price_yuan <= 0) {
                    alert('❌ Укажите цену в юанях больше 0');
                    this.isSaving = false;
                    return;
                }
                
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

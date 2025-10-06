/**
 * 🔍 CATEGORY SELECTOR COMPONENT - FIXED VERSION
 * Исправленная версия без синтаксических ошибок
 */

const CategorySelector = {
    name: 'CategorySelector',
    
    props: {
        modelValue: {
            type: [Number, String],
            default: null
        },
        detectedCategory: {
            type: Object,
            default: null
        },
        categories: {
            type: Array,
            default: function() { return []; }
        }
    },
    
    emits: ['update:modelValue', 'category-change', 'categories-load-required'],
    
    data() {
        return {
            categorySearch: '',
            filteredCategories: []
        }
    },
    
    computed: {
        selectedCategoryIndex: {
            get() {
                return this.modelValue;
            },
            set(value) {
                this.$emit('update:modelValue', value);
            }
        }
    },
    
    watch: {
        categorySearch: function() {
            this.updateFilteredCategories();
        },
        
        categories: {
            handler: function() {
                this.updateFilteredCategories();
            },
            immediate: true
        }
    },
    
    methods: {
        updateFilteredCategories() {
            console.log('CategorySelector: updateFilteredCategories called, categories.length:', this.categories.length, 'search:', this.categorySearch);
            
            if (!Array.isArray(this.categories) || this.categories.length === 0) {
                console.log('CategorySelector: Categories not loaded yet, setting empty filtered list');
                this.filteredCategories = [];
                return;
            }

            var query = this.categorySearch.trim().toLowerCase();
            var limit = 120;
            
            console.log('CategorySelector: Search query:', query, 'isEmpty:', !query);

            var matches = [];
            var self = this;
            
            this.categories.forEach(function(cat, index) {
                if (!cat) return;

                var synonyms = Array.isArray(cat.synonyms) ? cat.synonyms.join(' ') : '';
                var haystack = [
                    cat.category,
                    cat.material,
                    cat.tnved_code,
                    synonyms
                ].filter(Boolean).join(' ').toLowerCase();

                if (!query || haystack.indexOf(query) !== -1) {
                    matches.push({
                        originalIndex: index,
                        data: cat
                    });
                }
            });

            var selectedIndex = this.selectedCategoryIndex;
            if (selectedIndex !== null && selectedIndex !== '' && matches.findIndex(function(item) { return item.originalIndex === Number(selectedIndex); }) === -1) {
                var selectedCat = this.categories[selectedIndex];
                if (selectedCat) {
                    matches.unshift({ originalIndex: Number(selectedIndex), data: selectedCat });
                }
            }

            this.filteredCategories = matches.slice(0, limit);
            console.log('CategorySelector: Filtered categories count:', this.filteredCategories.length);
        },
        
        onCategoryChange() {
            if (this.selectedCategoryIndex !== null && this.selectedCategoryIndex !== '') {
                if (!Array.isArray(this.categories) || this.categories.length === 0) {
                    console.log('CategorySelector: Categories not loaded, emitting load request');
                    this.$emit('categories-load-required');
                    return;
                }

                var category = this.categories[this.selectedCategoryIndex];
                if (category) {
                    this.categorySearch = category.category;
                    this.$emit('category-change', {
                        category: category,
                        index: this.selectedCategoryIndex
                    });
                }
            }
        },
        
        resetSearch() {
            this.categorySearch = '';
            this.updateFilteredCategories();
        },
        
        getCleanCategoryName(categoryName) {
            return categoryName ? categoryName.replace(/\n/g, ' - ').trim() : '';
        }
    },
    
    template: '<div class="category-selector">' +
        '<div v-if="detectedCategory" style="font-size: 13px; color: #1f2937; font-weight: 500; margin-bottom: 6px;">' +
            'Определена категория: {{ getCleanCategoryName(detectedCategory.category) }}' +
        '</div>' +
        '<input v-model="categorySearch" type="text" class="form-input" placeholder="Начните вводить название или материал" style="margin-bottom: 8px;">' +
        '<select v-model="selectedCategoryIndex" @change="onCategoryChange" class="form-select" size="8" style="height: auto; padding: 10px;">' +
            '<option value="" disabled>Выберите категорию</option>' +
            '<option v-for="item in filteredCategories" :key="item.originalIndex" :value="item.originalIndex" style="padding: 6px 0; line-height: 1.4;">' +
                '{{ getCleanCategoryName(item.data.category) + " (" + item.data.material + ")" }}' +
            '</option>' +
            '<option v-if="filteredCategories.length === 0" disabled>Категории не найдены</option>' +
        '</select>' +
        '<div v-if="detectedCategory" style="font-size: 12px; color: #6b7280; margin-top: 4px;">' +
            '<span v-if="detectedCategory.density">Плотность: {{ detectedCategory.density.toFixed(0) }} кг/м³</span>' +
            '<span v-else>Плотность: N/A</span>' +
            ' • Ставка ЖД: ${{ detectedCategory.rates.rail_base }}' +
            ' • Авиа: ${{ detectedCategory.rates.air_base }}' +
        '</div>' +
        '<button v-if="categorySearch" @click="resetSearch" type="button" style="margin-top: 8px; padding: 4px 8px; font-size: 12px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer;">Очистить поиск</button>' +
    '</div>'
};

// Регистрируем компонент глобально
if (typeof window !== 'undefined') {
    window.CategorySelector = CategorySelector;
}
// Основной JavaScript для каталога товаров v4

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация
    initializeApp();
});

function initializeApp() {
    // Добавляем обработчики событий
    addEventListeners();
    
    // Инициализируем компоненты
    initializeComponents();
}

function addEventListeners() {
    // Обработчик для формы поиска
    const searchForm = document.querySelector('form[method="get"]');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    // Обработчики для фильтров
    const filters = document.querySelectorAll('select[name="route_name"], input[name="min_price"], input[name="max_price"]');
    filters.forEach(filter => {
        filter.addEventListener('change', handleFilterChange);
    });
}

function handleSearchSubmit(event) {
    // Валидация формы поиска
    const searchInput = event.target.querySelector('input[name="search"]');
    if (searchInput && searchInput.value.trim().length < 2) {
        event.preventDefault();
        showAlert('Введите минимум 2 символа для поиска', 'warning');
        return;
    }
}

function handleFilterChange(event) {
    // Автоматическая отправка формы при изменении фильтров
    const form = event.target.closest('form');
    if (form) {
        form.submit();
    }
}

function initializeComponents() {
    // Инициализация tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Инициализация popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function showAlert(message, type = 'info') {
    // Создаем уведомление
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Функции для работы с товарами
function showProductDetails(productId) {
    // Переход к детальной странице товара
    window.location.href = `/product/${productId}`;
}

function addToCart(productId, offerId) {
    // Добавление товара в корзину (заглушка)
    showAlert('Товар добавлен в корзину', 'success');
}

// Функции для работы с изображениями
function showImageModal(imageSrc, imageAlt) {
    // Показ изображения в модальном окне
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${imageAlt}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body text-center">
                    <img src="${imageSrc}" class="img-fluid" alt="${imageAlt}">
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Удаляем модальное окно после закрытия
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

// Утилиты
function formatPrice(price, currency = 'USD') {
    if (price === null || price === undefined) {
        return 'Не указана';
    }
    
    if (currency === 'USD') {
        return `$${parseFloat(price).toFixed(2)}`;
    } else if (currency === 'RUB') {
        return `${parseFloat(price).toFixed(2)} ₽`;
    } else {
        return `${parseFloat(price).toFixed(2)} ${currency}`;
    }
}

function formatQuantity(quantity) {
    if (quantity === null || quantity === undefined) {
        return 'Не указан';
    }
    
    return quantity.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

function formatDeliveryTime(deliveryTime) {
    if (deliveryTime === null || deliveryTime === undefined) {
        return 'Не указан';
    }
    
    return `${deliveryTime} дней`;
}


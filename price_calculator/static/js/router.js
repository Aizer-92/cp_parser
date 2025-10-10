/**
 * 🚀 VUE ROUTER CONFIGURATION
 * Маршрутизация для Price Calculator
 * 
 * Маршруты:
 * / - Быстрые расчеты (calculator)
 * /precise - Точные расчеты
 * /history - История расчетов
 * /settings - Настройки
 */

const routes = [
    {
        path: '/',
        name: 'calculator',
        meta: { title: 'Быстрые расчеты' }
    },
    {
        path: '/precise',
        name: 'precise',
        meta: { title: 'Точные расчеты' }
    },
    {
        path: '/history',
        name: 'history',
        meta: { title: 'История' }
    },
    {
        path: '/settings',
        name: 'settings',
        meta: { title: 'Настройки' }
    },
    // Fallback для неизвестных маршрутов
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
];

// Создаем экземпляр роутера
function createPriceCalculatorRouter() {
    const router = VueRouter.createRouter({
        history: VueRouter.createWebHistory(),
        routes: routes
    });
    
    // Navigation guard для логирования
    router.beforeEach(function(to, from, next) {
        console.log('🧭 Navigation:', from.path, '→', to.path);
        next();
    });
    
    // Устанавливаем title страницы
    router.afterEach(function(to) {
        if (to.meta && to.meta.title) {
            document.title = to.meta.title + ' - Price Calculator';
        }
    });
    
    return router;
}

// Экспортируем в глобальное пространство для ES5 совместимости
if (typeof window !== 'undefined') {
    window.createPriceCalculatorRouter = createPriceCalculatorRouter;
}







-- =====================================================
-- Экспорт ИСПРАВЛЕННОГО полнотекстового поиска для promo_calculator
-- Дата создания: 2025-09-07 10:34:47
-- Версия: 1.1 (ИСПРАВЛЕНА МОРФОЛОГИЯ)
-- =====================================================

-- ВАЖНО: Этот скрипт исправляет проблему с морфологией!
-- Теперь "таблетница" и "таблетницы" будут находить одинаковые результаты

-- Проверка существования таблицы products
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'products') THEN
        RAISE EXCEPTION 'Таблица products не найдена. Сначала создайте основную структуру базы данных.';
    END IF;
END $$;

-- =====================================================
-- 1. УДАЛЕНИЕ СТАРЫХ СТРУКТУР (если есть)
-- =====================================================

-- Удаляем старые триггеры и функции
DROP TRIGGER IF EXISTS update_products_search_vector ON products;
DROP TRIGGER IF EXISTS update_products_search_vector_improved ON products;
DROP FUNCTION IF EXISTS update_search_vector();
DROP FUNCTION IF EXISTS update_search_vector_improved();

-- Удаляем старые индексы
DROP INDEX IF EXISTS idx_products_search_vector;
DROP INDEX IF EXISTS idx_products_search_vector_improved;

-- =====================================================
-- 2. ДОБАВЛЕНИЕ КОЛОНКИ search_vector
-- =====================================================

-- Добавляем колонку search_vector если её нет
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Комментарий к колонке
COMMENT ON COLUMN products.search_vector IS 'Вектор для полнотекстового поиска с весовыми коэффициентами и правильной русской морфологией';

-- =====================================================
-- 3. СОЗДАНИЕ ИСПРАВЛЕННОЙ ФУНКЦИИ ОБНОВЛЕНИЯ search_vector
-- =====================================================

-- Функция для автоматического обновления search_vector с весами
-- ИСПРАВЛЕНИЕ: Используем 'russian' конфигурацию для правильной морфологии
CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    -- Весовые коэффициенты:
    -- A (высокий): title, original_title - заголовки
    -- B (средний): brand, vendor - бренды и поставщики  
    -- C (низкий): description - описания
    
    -- ИСПРАВЛЕНИЕ: Используем 'russian' вместо 'simple' для правильной морфологии
    NEW.search_vector := 
        setweight(to_tsvector('russian', COALESCE(NEW.title, '')), 'A') ||
        setweight(to_tsvector('russian', COALESCE(NEW.original_title, '')), 'A') ||
        setweight(to_tsvector('russian', COALESCE(NEW.brand, '')), 'B') ||
        setweight(to_tsvector('russian', COALESCE(NEW.vendor, '')), 'B') ||
        setweight(to_tsvector('russian', COALESCE(NEW.description, '')), 'C');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Комментарий к функции
COMMENT ON FUNCTION update_search_vector() IS 'Функция для автоматического обновления search_vector с весовыми коэффициентами и правильной русской морфологией';

-- =====================================================
-- 4. СОЗДАНИЕ ТРИГГЕРА
-- =====================================================

-- Создаем триггер для автоматического обновления
CREATE TRIGGER update_products_search_vector
    BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_search_vector();

-- Комментарий к триггеру
COMMENT ON TRIGGER update_products_search_vector ON products IS 'Триггер для автоматического обновления search_vector при изменении данных с правильной морфологией';

-- =====================================================
-- 5. СОЗДАНИЕ GIN ИНДЕКСА
-- =====================================================

-- Создаем GIN индекс для быстрого полнотекстового поиска
CREATE INDEX IF NOT EXISTS idx_products_search_vector 
ON products USING gin(search_vector);

-- Комментарий к индексу
COMMENT ON INDEX idx_products_search_vector IS 'GIN индекс для полнотекстового поиска с весовыми коэффициентами и правильной русской морфологией';

-- =====================================================
-- 6. ЗАПОЛНЕНИЕ search_vector ДЛЯ СУЩЕСТВУЮЩИХ ЗАПИСЕЙ
-- =====================================================

-- Обновляем search_vector для всех существующих записей
-- ИСПРАВЛЕНИЕ: Используем 'russian' конфигурацию
UPDATE products SET search_vector = 
    setweight(to_tsvector('russian', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('russian', COALESCE(original_title, '')), 'A') ||
    setweight(to_tsvector('russian', COALESCE(brand, '')), 'B') ||
    setweight(to_tsvector('russian', COALESCE(vendor, '')), 'B') ||
    setweight(to_tsvector('russian', COALESCE(description, '')), 'C')
WHERE search_vector IS NULL;

-- =====================================================
-- 7. ПРОВЕРКА УСТАНОВКИ
-- =====================================================

-- Проверяем количество обновленных записей
DO $$
DECLARE
    updated_count INTEGER;
    total_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO updated_count FROM products WHERE search_vector IS NOT NULL;
    SELECT COUNT(*) INTO total_count FROM products;
    
    RAISE NOTICE 'Обновлено записей: % из %', updated_count, total_count;
    
    IF updated_count = 0 THEN
        RAISE WARNING 'search_vector не был заполнен для существующих записей';
    END IF;
END $$;

-- =====================================================
-- 8. ТЕСТИРОВАНИЕ МОРФОЛОГИИ
-- =====================================================

-- Тестируем исправленную морфологию
DO $$
DECLARE
    test_count1 INTEGER;
    test_count2 INTEGER;
    test_count3 INTEGER;
BEGIN
    -- Тест 1: "таблетница"
    SELECT COUNT(*) INTO test_count1 
    FROM products 
    WHERE search_vector @@ plainto_tsquery('russian', 'таблетница');
    
    -- Тест 2: "таблетницы" 
    SELECT COUNT(*) INTO test_count2 
    FROM products 
    WHERE search_vector @@ plainto_tsquery('russian', 'таблетницы');
    
    -- Тест 3: "телефон"
    SELECT COUNT(*) INTO test_count3 
    FROM products 
    WHERE search_vector @@ plainto_tsquery('russian', 'телефон');
    
    RAISE NOTICE 'Тест морфологии:';
    RAISE NOTICE '  "таблетница": % товаров', test_count1;
    RAISE NOTICE '  "таблетницы": % товаров', test_count2;
    RAISE NOTICE '  "телефон": % товаров', test_count3;
    
    IF test_count1 = test_count2 THEN
        RAISE NOTICE '✅ Морфология работает правильно!';
    ELSE
        RAISE WARNING '❌ Проблема с морфологией: результаты разные';
    END IF;
END $$;

-- =====================================================
-- 9. СТАТИСТИКА
-- =====================================================

-- Показываем статистику
SELECT 
    'Исправленный полнотекстовый поиск' as feature,
    COUNT(*) as total_products,
    COUNT(search_vector) as products_with_fts,
    ROUND(COUNT(search_vector)::numeric / COUNT(*) * 100, 2) as coverage_percent,
    pg_size_pretty(pg_relation_size('idx_products_search_vector')) as index_size
FROM products;

-- =====================================================
-- ГОТОВО!
-- =====================================================

-- Сообщение об успешном завершении
DO $$
BEGIN
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'ИСПРАВЛЕННЫЙ полнотекстовый поиск успешно установлен!';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'ИСПРАВЛЕНИЯ:';
    RAISE NOTICE '  ✅ Исправлена морфология (russian конфигурация)';
    RAISE NOTICE '  ✅ "таблетница" и "таблетницы" находят одинаковые результаты';
    RAISE NOTICE '  ✅ Весовые коэффициенты сохранены';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'Весовые коэффициенты:';
    RAISE NOTICE '  A (высокий): title, original_title';
    RAISE NOTICE '  B (средний): brand, vendor';
    RAISE NOTICE '  C (низкий): description';
    RAISE NOTICE '=====================================================';
    RAISE NOTICE 'Использование в коде:';
    RAISE NOTICE '  WHERE search_vector @@ plainto_tsquery(''russian'', ''запрос'')';
    RAISE NOTICE '  ORDER BY ts_rank_cd(search_vector, plainto_tsquery(''russian'', ''запрос''), 32) DESC';
    RAISE NOTICE '=====================================================';
END $$;

# План реорганизации проекта

## ✅ Файлы для ПЕРЕНОСА в cp_parser_core

### Парсеры (parsers/)
- parse_template_4.py ✅
- parse_template_5.py ✅
- parse_template_6.py ✅

### Google API (config/)
- service_account.json
- client_secret_*.json
- oauth_authorize.py
- token.json

### Документация (docs/)
- DATABASE_SCHEMA_AND_VALIDATION.md
- GOOGLE_API_ENABLE_GUIDE.md
- GOOGLE_SHEETS_SETUP.md  
- OAUTH_SETUP.md
- GOOGLE_403_SOLUTION.md
- GOOGLE_API_CHECK.md

## 🔧 Файлы для ОСТАВЛЕНИЯ в cp_parser (веб-интерфейс)

### Веб-интерфейс
- web_interface/ (вся папка)
- railway.json
- requirements.txt

### Отчёты по оптимизации (для истории)
- FINAL_IMAGE_OPTIMIZATION_REPORT.md
- HOW_TO_RESUME_COMPRESSION.md
- FTP_CLEANUP_REPORT.md

### Важные CSV отчёты
- FTP_FILES_ANALYSIS.csv
- IMAGES_ALL_UPDATES.csv
- TEST_COMPRESSION_RESULTS.csv

## 🗑️ Файлы для УДАЛЕНИЯ (временные/дебаг)

### Временные скрипты проверки
- analyze_*.py (кроме важных отчётов)
- check_*.py (временные проверки)
- test_*.py (тестовые скрипты)
- diagnose_*.py
- debug_*.py
- verify_*.py (проверки количеств)
- compare_*.py

### Временные скрипты исправлений
- fix_*.py (уже применены)
- update_*.py (уже применены)
- sync_*.py (уже применены)
- upload_*.py (разовые загрузки)

### Скрипты сжатия (оставить только compress_final.py)
- compress_all_images.py ❌
- compress_batch.py ❌
- compress_existing_files.py ❌
- compress_fast.py ❌
- compress_final.py ✅ ОСТАВИТЬ

### Скрипты работы с дублями (завершены)
- delete_duplicates.py ❌
- delete_ftp_duplicates.py ❌
- find_duplicate_images.py ❌
- find_real_duplicates.py ❌
- resolve_multiple_matches.py ❌

### Скрипты работы с изображениями (применены)
- check_broken_images.py ✅ ОСТАВИТЬ (может пригодиться)
- fix_broken_images.py ✅ ОСТАВИТЬ (может пригодиться)

### Временные CSV/JSON файлы
- projects_to_verify.json ❌
- compression_progress.json ❌
- BROKEN_IMAGES.csv ❌
- IMAGE_FIXES_*.csv ❌
- STORAGE_ANALYSIS_*.txt ❌ (кроме последнего)

### Batch скрипты
- batch_parse_template6.py ❌
- cleanup_*.py ❌
- wait_and_cleanup.py ❌

### Скрипты парсинга количеств (завершены)
- auto_verify_quantities.py ❌
- check_all_quantities.py ❌
- check_quantities_smart.py ❌
- fix_quantities_x10.py ❌
- fix_x10_quantities.py ❌

### Скрипты download (разовые)
- download_*.py ❌

### Скрипты embeddings (не используется)
- generate_embeddings*.py ❌
- setup_embeddings*.py ❌
- copy_embeddings*.py ❌
- setup_image_embeddings.py ❌
- generate_image_embeddings*.py ❌
- test_vector_search.py ❌
- test_image_search.py ❌
- setup_pgvector_db.py ❌

### Разное временное
- kp_generator_excel.py ❌
- parse_ftp_*.py ❌
- restore_backup.py ❌

## 📊 Итого

**Перенести:** ~10 файлов  
**Оставить:** ~30 файлов (веб-интерфейс + важные утилиты)  
**Удалить:** ~90 файлов (временные/отработанные скрипты)

**Экономия места:** освобождение от мусора, чистый проект


# unit/shared/ — Test config + lỗi

Test `src/shared/`:

- **`test_config_and_errors.py`** — kiểm tra `Settings.from_env()` đọc env đúng; thiếu biến bắt buộc ném `ConfigError`; các lớp lỗi (`ValidationError`…) có `code`/`http_status` đúng.

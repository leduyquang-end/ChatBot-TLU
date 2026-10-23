# unit/shared/ — Test `src/shared/`

Cấu trúc mirror theo `src/shared/` (AGENT.md mục 116):

- **`common/test_errors.py`** — đủ 7 lớp lỗi có `code`/`http_status` khớp bảng trong README; `AppError` mặc định `message = code`; `detail`.
- **`config/test_settings.py`** — `Settings.from_env()`: thiếu biến bắt buộc (kể cả toàn khoảng trắng) → `ConfigError` nêu tên biến; số sai kiểu → `ConfigError`; số để trống → mặc định; giá trị mặc định; `LOG_LEVEL` chữ hoa; URL bỏ `/` cuối; `DATABASE_URL`; `get_settings()` ghi nhớ.
- **`database/test_connection.py`** — `connect()` tạo file + thư mục cha, query đọc theo tên cột, `PRAGMA foreign_keys`; `:memory:`; đường dẫn tương đối; dialect khác/URL sai → `ConfigError`; `get_connection()` theo settings; `db_connection()` tự đóng.
- **`events/test_bus.py`** — publish đúng loại chính xác (không gồm lớp cha), không handler → 0, subscribe trùng chỉ chạy 1 lần, unsubscribe (kể cả chưa đăng ký), handler lỗi không phá handler khác, đa luồng, singleton + reset, `clear()`.
- **`events/test_types.py`** — sự kiện là con `Event`, bất biến (frozen), `KnowledgeIngested` chỉ có trường số liệu.

Chạy: `python -m pytest tests/unit/shared -q`

# logging/ — "Camera an ninh" của chương trình

## Mục đích

Ghi lại những gì đang xảy ra trong chương trình, để khi có lỗi hoặc cần kiểm tra thì xem lại được. Giống như camera an ninh ghi hình — khi có sự cố, ta mở lại file xem chuyện gì đã xảy ra.

Quy tắc đầy đủ: AGENT.md mục 10 (Logging).

## File chính

### `setup.py`

**Hàm chính:**

- `setup_logging(level="INFO", force=False)` — bật hệ thống ghi log. Gọi **một lần duy nhất** khi khởi động (`src/main.py`, script). Lời gọi lần thứ hai bị bỏ qua (trừ `force=True`). Mức log không tồn tại → tự fallback về `INFO` (ghi cảnh báo `event=logging.bad_level`).
- `reset_logging()` — gỡ cấu hình (dùng cho test / cần cấu hình lại từ đầu).
- `get_logger(name)` — lấy logger theo tên module.
- `log_event(logger, level, event, **fields)` — ghi một sự kiện dạng `event=... key=value`. **Tự che (redact) khóa nhạy cảm** trước khi ghi.

### `audit.py`

- `register_audit_handlers(bus)` — gắn handler audit vào bus sự kiện; gọi ở `src/main.py` và `scripts/ingest_tlu.py` (đăng ký lặp lại an toàn).
- Ghi: `audit.user.logged_in` (user_id, role), `audit.user.password_changed` (user_id), `audit.knowledge.ingested` (chunks, entities, relations, duration_s).
- Chỉ ghi id/số liệu — không ghi mật khẩu, token, nội dung tài liệu hay thông tin cá nhân.

**Định dạng mỗi dòng** (AGENT.md 10.3): `2026-10-23 10:00:00 level=INFO event=app.started port=8000`

**Quy tắc an toàn khi ghi (log_event):**

- Khóa chứa đoạn `password`, `secret`, `token`, `api_key`, `authorization`, `question`, `answer`, `content`, `mssv`, `email`, `phone`, `full_name`... → giá trị bị thay bằng `[REDACTED]` (so khớp không phân biệt hoa thường, bắt cả `user_password`, `access_token`).
- Dict/list **lồng nhau** cũng bị quét (vd `headers.Authorization`).
- Khóa lạ có ký tự đặc biệt → được dọn về dạng an toàn; giá trị có khoảng trắng hoặc xuống dòng → bọc ngoặc kép/thay `\\n` để **vẫn đảm bảo mỗi dòng một sự kiện**.
- Không nhạy cảm thì giữ nguyên (vd `conversation_id`, `mode`, `port`).

**Không bao giờ** ghi mật khẩu, khóa API, câu hỏi/trả lời, thông tin cá nhân ra log ở mức INFO trở lên — nếu cần, phải che bớt (redact) đi trước.

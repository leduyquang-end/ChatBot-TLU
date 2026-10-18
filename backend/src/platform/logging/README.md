# logging/ — "Camera an ninh" của chương trình

## Mục đích

Ghi lại những gì đang xảy ra trong chương trình, để khi có lỗi hoặc cần kiểm tra thì xem lại được. Giống như camera an ninh ghi hình — khi có sự cố, ta mở lại file xem chuyện gì đã xảy ra.

## File chính

### `setup.py`

Chỉ có một hàm chính: `setup_logging(level)` — bật hệ thống ghi log (log = "ghi chép sự kiện").

**Cách hoạt động:**
- Khi chương trình chạy, mọi thông điệp log sẽ có định dạng `key=value`, ví dụ: `event=chat.router.selected mode=Vector`
- Mức độ chi tiết do biến `LOG_LEVEL` quyết định (INFO = ghi trung bình, DEBUG = ghi rất chi tiết)

**Quy tắc an toàn:**
- **Không bao giờ** ghi log mật khẩu hoặc mã khóa API ra file — nếu cần ghi, phải che bớt (redact) đi trước
- Gọi hàm này **một lần duy nhất** khi khởi động app, trong `src/main.py`

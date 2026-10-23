# user/api/ - "Quầy order" của phòng user

## File chính

### `routes.py`

Blueprint `user`, tiền tố `/user`:

| Endpoint | Method | Quyền | Việc làm |
|----------|--------|-------|----------|
| `/user/me` | GET | Đã đăng nhập | Trả hồ sơ user hiện tại |
| `/user/me` | PUT | Đã đăng nhập | Sửa họ tên (`full_name`, 1..100 ký tự) |
| `/user/change-password` | POST | Đã đăng nhập | Đổi mật khẩu (`old_password`, `new_password`) |
| `/user` | GET | **Admin** | Liệt kê user (sắp theo `id`) |

Helper:
- `_current_user()` - đọc `Authorization: Bearer <token>`, `verify_token()` → `GetUserById`
- `_json_body()` - JSON sai/không phải object → `{}`
- `_serialize()` - chỉ trả `id`, `username`, `full_name`, `role`

Lỗi: thiếu/k sai token → 401; thiếu field → 400; sai mật khẩu cũ → 401; không phải admin → 403.
Mọi lỗi ném `AppError` (xử lý tập trung ở `src/main.py`).

Đăng ký Blueprint trong `src/main.py`.

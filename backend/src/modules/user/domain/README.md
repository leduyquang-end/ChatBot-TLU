# user/domain/ — Thực thể User

## File chính

### `user.py`

- `User` — frozen dataclass: `id`, `username`, `full_name`, `role`
- Hằng `ROLE_STUDENT = "student"`, `ROLE_ADMIN = "admin"`, `FULL_NAME_MAX_LENGTH = 100`
- `__post_init__` — role hoặc họ tên không hợp lệ → `ValueError`
- `is_admin()` — kiểm tra quyền admin
- `with_full_name(full_name)` — trả về bản sao với họ tên mới (bất biến); input sai → `ValidationError` (400)

### `password_rules.py`

- `PASSWORD_MIN_LENGTH = 6`, `PASSWORD_MAX_LENGTH = 128`
- `validate_password_format(password)` — sai độ dài → `ValidationError` (400)
- `ensure_password_changed(old, new)` — trùng mật khẩu cũ → `ValidationError` (400)

## Quy tắc domain (mọi entity đều vậy)

- Không import Flask/DB/LLM — thuần Python
- Bất biến (frozen dataclass) — không sửa object sau khi tạo
- Validate ngay lúc tạo dữ liệu (`ValueError` = lệch nội bộ; input người dùng → `ValidationError`)

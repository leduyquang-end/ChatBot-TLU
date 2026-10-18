# user/domain/ — Thực thể User

## File chính

### `user.py`

- `User` — frozen dataclass: `id`, `username`, `full_name`, `role`
- Hằng `ROLE_STUDENT = "student"`, `ROLE_ADMIN = "admin"`
- `__post_init__` — role không hợp lệ → `ValueError`
- `is_admin()` — kiểm tra quyền admin

## Quy tắc domain (mọi entity đều vậy)

- Không import Flask/DB/LLM — thuần Python
- Bất biến (frozen dataclass) — không sửa object sau khi tạo
- Validate ngay lúc tạo dữ liệu

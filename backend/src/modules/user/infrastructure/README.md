# user/infrastructure/ — "Kho nguyên liệu" của user

## File chính

### `in_memory_user_repository.py`

`InMemoryUserRepository` — lưu `dict` trong RAM:

- `find_by_id`, `find_by_username`, `save`
- `set_password(username, password)` — hash PBKDF2 qua `platform/security`
- `check_password(username, password)` — verify timing-safe
- Singleton: `_USER_REPOSITORY` + `get_user_repository()` — trả repository chung cho cả app
- `_seed_demo_users()` — seed 2 tài khoản demo (`sinhvien01`, `admin01` / `demo-password`)

## Khi code theo

**Thay DB thật:** viết class mới (ví dụ `SqlUserRepository`) cài cùng interface, đổi trong `get_user_repository()` — các chỗ khác không đổi.

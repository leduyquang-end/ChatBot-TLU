# user/infrastructure/ - "Kho nguyên liệu" của user

## File chính

### `in_memory_user_repository.py`

`InMemoryUserRepository` - lưu `dict` trong RAM (cài đủ `UserRepository` port):

- `find_by_id`, `find_by_username`, `save`, `list_all`
- `set_password(username, password)` - hash PBKDF2 qua `platform/security`; username không tồn tại → `NotFoundError` (không ghi credential mồ côi)
- `check_password(username, password)` - verify timing-safe; chưa đặt mật khẩu → `False`
- Singleton: `_USER_REPOSITORY` + lock `threading` (`get_user_repository()`) - seed xong mới gán, an toàn khi 2 request cold start chạy song song
- `_seed_demo_users()` - seed 2 tài khoản demo (`sinhvien01`, `admin01` / `demo-password`)
- `reset_user_repository()` - xóa singleton để lần gọi sau seed lại (dùng cho test)

## Khi code theo

**Thay DB thật:** viết class mới (vd `SqlUserRepository`) cài cùng interface, đổi trong `get_user_repository()` - các chỗ khác không đổi.

# user/application/ — "Bếp trưởng" xử lý user

## File chính

### `get_user_by_id.py`

- `GetUserById(repo).execute(user_id) -> User`
- Không thấy user → ném `NotFoundError` (404)

### `update_my_profile.py`

- `UpdateMyProfile(repo).execute(user_id, full_name) -> User`
- Cập nhật họ tên của chính user hiện tại (PUT /user/me)
- Quy tắc họ tên nằm ở domain (`User.with_full_name` — rỗng/quá 100 ký tự → `ValidationError` 400)
- Không thấy user → `NotFoundError` (404)

### `change_password.py`

- `ChangePassword(repo, event_bus).execute(user_id, old_password, new_password) -> None`
- Đổi mật khẩu của chính user hiện tại (POST /user/change-password)
- Thành công → bắn `UserPasswordChanged` (audit log); thất bại → không bắn
- Quy tắc mật khẩu nằm ở domain (`password_rules` — sai độ dài 6..128 hoặc trùng cũ → `ValidationError` 400)
- Mật khẩu cũ sai → `UnauthorizedError` (401) — cùng nhóm lỗi đăng nhập sai
- Không thấy user → `NotFoundError` (404)

### `list_users.py`

- `ListUsers(repo).execute() -> list[User]` — sắp xếp theo `id`
- Kiểm tra quyền admin do api layer thực hiện (AGENT.md 11.2)

### ports/user_repository.py

- `UserRepository(Protocol)` — hợp đồng cho mọi repository user:
  - `find_by_id(user_id) -> User | None`
  - `find_by_username(username) -> User | None`
  - `save(user) -> User`
  - `list_all() -> list[User]`
  - `set_password(username, password) -> None`
  - `check_password(username, password) -> bool`

## Khi code theo

Thêm use case mới: class nhận port qua constructor, method `execute()`, ném lỗi từ `shared/common/errors.py`.

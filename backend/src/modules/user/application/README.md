# user/application/ — "Bếp trưởng" xử lý user

## File chính

### `get_user_by_id.py`

- `GetUserById(repo).execute(user_id) -> User`
- Không thấy user → ném `NotFoundError` (404)

### ports/user_repository.py

- `UserRepository(Protocol)` — hợp đồng cho mọi repository user:
  - `find_by_id(user_id) -> User | None`

## Khi code theo

Thêm use case mới: class nhận port qua constructor, method `execute()`, ném lỗi từ `shared/common/errors.py`.

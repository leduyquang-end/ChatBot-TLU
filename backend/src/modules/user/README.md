# user/ — Phòng quản lý thông tin người dùng

## Mục đích

Lưu trữ và lấy thông tin người dùng (họ tên, tài khoản, vai trò). Phục vụ:
- Auth: tra cứu user khi đăng nhập
- API `/user/me`: trả thông tin user hiện tại

## Kiến trúc 4 lớp

```
user/
├── api/routes.py                        ← Quầy order (GET /user/me)
├── application/
│   ├── get_user_by_id.py                ← Bếp trưởng (lấy user theo id)
│   └── ports/user_repository.py         ← Hợp đồng (interface)
├── domain/
│   └── user.py                          ← Thực đơn (entity User)
└── infrastructure/
    └── in_memory_user_repository.py     ← Kho nguyên liệu (lưu trong RAM)
```

## domain/user.py — Thực thể User

`User` là "thực thể" (entity) — gói thông tin về một người dùng:

```python
@dataclass(frozen=True)
class User:
    id: str
    username: str
    full_name: str
    role: str  # "student" hoặc "admin"
```

- Bất biến (frozen) — không sửa sau khi tạo
- Role sai → `ValueError` ngay khi tạo
- Có method `is_admin()` kiểm tra quyền admin

## Luồng hoạt động `/user/me`

```
GET /user/me  + header Authorization: Bearer <token>
   → verify_token(token) → user_id
   → GetUserById(repo).execute(user_id)
   → 200 {id, username, full_name, role}
   (sai token → 401; không thấy user → 404)
```

## infrastructure — Kho nguyên liệu

`InMemoryUserRepository` — lưu trong bộ nhớ (RAM):

- `find_by_id` / `find_by_username` / `save`
- `set_password` / `check_password` (dùng `hash_password`/`verify_password` từ platform/security)
- `get_user_repository()` — singleton (một instance duy nhất) + seed 2 user demo

## Khi code theo

**Query mới:** thêm method vào `ports/user_repository.py` + cài trong repository + use case riêng trong `application/`.

**Chuyển sang DB thật:** viết repository mới thỏa cùng interface, thay trong `get_user_repository()`.

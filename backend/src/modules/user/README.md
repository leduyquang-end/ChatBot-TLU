# user/ - Phòng quản lý thông tin người dùng

## Mục đích

Lưu trữ và lấy thông tin người dùng (họ tên, tài khoản, vai trò). Phục vụ:
- Auth: tra cứu user khi đăng nhập / refresh
- API `/user`: xem hồ sơ, sửa họ tên, đổi mật khẩu; admin xem danh sách

## Kiến trúc 4 lớp

```
user/
├── api/routes.py                        → Quầy order (4 endpoint)
├── application/
│   ├── get_user_by_id.py                → Bếp trưởng (lấy user theo id)
│   ├── update_my_profile.py             → sửa họ tên
│   ├── change_password.py               → đổi mật khẩu
│   ├── list_users.py                    → liệt kê (admin)
│   └── ports/user_repository.py         → Hợp đồng (interface)
├── domain/
│   ├── user.py                          → Thực đơn (entity User)
│   └── password_rules.py                → quy tắc mật khẩu
└── infrastructure/
    └── in_memory_user_repository.py     → Kho nguyên liệu (lưu trong RAM)
```

## domain/user.py - Thực thể User

```python
@dataclass(frozen=True)
class User:
    id: str
    username: str
    full_name: str
    role: str  # "student" hoặc "admin"
```

- Bất biến (frozen) - không sửa sau khi tạo; muốn đổi họ tên → `with_full_name()` trả bản sao
- Role sai → `ValueError`; họ tên rỗng/quá 100 ký tự → `ValueError` (lỗi nội bộ)
- `with_full_name()`: input người dùng sai → `ValidationError` (400)
- `is_admin()` kiểm tra quyền admin

## Các endpoint

| Endpoint | Method | Việc làm |
|----------|--------|----------|
| `/user/me` | GET | Xem hồ sơ của chính mình |
| `/user/me` | PUT | Sửa họ tên (`full_name`) |
| `/user/change-password` | POST | Đổi mật khẩu (`old_password`, `new_password`) — xong bắn `UserPasswordChanged` |
| `/user` | GET | Danh sách user — **chỉ admin** (403 nếu sinh viên) |

Luồng chung: `Bearer token` → `verify_token()` → `GetUserById` → use case → JSON.
Quyền admin kiểm tra ở `api` bằng `require_role(me.role, {ROLE_ADMIN})` (AGENT.md 11.2).

## infrastructure - Kho nguyên liệu

`InMemoryUserRepository` - lưu trong bộ nhớ (RAM):

- `find_by_id` / `find_by_username` / `save` / `list_all`
- `set_password` / `check_password` (dùng `hash_password`/`verify_password` từ platform/security)
- `set_password` với user không tồn tại → `NotFoundError`
- `get_user_repository()` - singleton an toàn luồng + seed 2 user demo
- `reset_user_repository()` - dùng cho test

## Khi code theo

**Query mới:** thêm method vào `ports/user_repository.py` + cài trong repository + use case riêng trong `application/`.

**Chuyển sang DB thật:** viết repository mới thỏa cùng interface, thay trong `get_user_repository()`.

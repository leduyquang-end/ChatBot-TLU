# auth/ 

## Mục đích

Cho phép người dùng đăng nhập bằng tài khoản/mật khẩu, nhận về "thẻ ra vào" (token) để dùng các chức năng khác mà không phải đăng nhập lại mỗi lần.

Giống như quầy tiếp tân của khách sạn: bạn xuất trình giấy tờ (tài khoản/mật khẩu), nhân viên kiểm tra đúng thì cấp cho bạn một thẻ phòng (token). Sau đó bạn dùng thẻ này ra vào thang máy, phòng gym… mà không cần xuất trình giấy tờ lại.

## Kiến trúc 4 lớp

```
auth/
├── api/routes.py                     ←(nhận request HTTP)
├── application/
│   ├── login.py                      ←  (quyết định đăng nhập thế nào)
│   └── ports/credential_checker.py   ←  (interface) — nói: tôi cần ai đó kiểm tra mật khẩu
├── domain/                           ← (trống) — auth không có thực thể riêng
└── infrastructure/
    └── repository_credential_checker.py ← Kho nguyên liệu (tra cứu user thật)
```

## Luồng đăng nhập — từng bước

```
POST /auth/login  {username: "sinhvien01", password: "demo-password"}
        │
        ▼
[api/routes.py] Kiểm tra: có username/password chưa? Thiếu → báo lỗi 400
        │
        ▼
[LoginUseCase.execute]
   Bước 1: Gọi checker.check(username, password)
            → Sai mật khẩu? → UnauthorizedError (401) "Sai tài khoản hoặc mật khẩu"
   Bước 2: Gọi checker.find_user(username)
            → Không thấy user? → UnauthorizedError (401) (cùng thông điệp, để không tiết lộ sai ở bước nào)
   Bước 3: Gọi issue_token(user.id)
            → Nhận token (chuỗi ký tự đặc biệt, có hạn 24h)
        │
        ▼
Trả về: 200 {"token": "...", "user_id": "u-001", "role": "student"}
```

## Tài khoản demo

Hiện có 2 tài khoản mẫu (tự động tạo khi khởi động):
- `sinhvien01` / `demo-password` (sinh viên)
- `admin01` / `demo-password` (quản trị viên)

## Cách dùng token

Sau khi đăng nhập, mọi request cần đăng nhập phải kèm header:

```
Authorization: Bearer <token_vừa_nhận>
```

Token được kiểm tra bằng hàm `verify_token()` trong `platform/security/auth.py`.

## Khi code theo

- **Thêm chức năng đăng nhập mới** (ví dụ: đăng nhập bằng email): viết use case mới trong `application/`, khai báo port mới nếu cần, cài trong `infrastructure/`
- **Đổi nguồn lưu user** (từ RAM sang database): chỉ sửa `infrastructure/`, không đụng `application/` hay `api/`
- **Test**: fake `CredentialChecker` (giả lập), không cần database thật


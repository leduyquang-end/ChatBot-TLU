# auth/ 

## Mục đích

Cho phép người dùng đăng nhập bằng tài khoản/mật khẩu, nhận về "thẻ ra vào" (token) để dùng các chức năng khác mà không phải đăng nhập lại mỗi lần.

Giống như quầy tiếp tân của khách sạn: bạn xuất trình giấy tờ (tài khoản/mật khẩu), nhân viên kiểm tra đúng thì cấp cho bạn một thẻ phòng (token). Sau đó bạn dùng thẻ này ra vào thang máy, phòng gym… mà không cần xuất trình giấy tờ lại. Khi thẻ sắp hết hạn, bạn đưa thẻ ra quầy để đổi thẻ mới (refresh) — chỉ cần thẻ, không cần xuất trình giấy tờ lần nữa.

## Kiến trúc 4 lớp

```
auth/
├── api/routes.py                        ←(nhận request HTTP — 3 endpoint)
├── application/
│   ├── login.py                         ←  (đăng nhập → cấp token + phiên)
│   ├── refresh.py                       ←  (đổi token mới bằng phiên)
│   ├── logout.py                        ←  (thu hồi phiên)
│   └── ports/
│       ├── credential_checker.py        ←  (hợp đồng) tôi cần ai kiểm tra mật khẩu
│       ├── token_issuer.py              ←  (hợp đồng) tôi cần ai cấp token
│       └── refresh_token_store.py       ←  (hợp đồng) tôi cần ai lưu phiên
├── domain/refresh_token.py              ←  Phiên refresh + luật "hết hạn"
└── infrastructure/
    ├── repository_credential_checker.py ← Kho nguyên liệu (tra cứu user thật)
    ├── hmac_token_issuer.py             ← Ký token thật (HMAC)
    └── in_memory_refresh_token_store.py ← Kho phiên trong RAM (singleton)
```

## Hai loại token

| Loại | Thời hạn | Dùng để |
|------|----------|---------|
| **Access token** (`token`) | 24 giờ | Gọi API cần đăng nhập — kèm header `Authorization: Bearer <token>` |
| **Refresh token** (`refresh_token`) | 30 ngày (đổi qua `REFRESH_TOKEN_TTL_HOURS`) | Đổi lấy access token mới qua `POST /auth/refresh`, không cần nhập lại mật khẩu |

## Luồng đăng nhập — từng bước

```
POST /auth/login  {username: "sinhvien01", password: "demo-password"}
        │
        ▼
[api/routes.py] Kiểm tra: có username/password chưa? Thiếu → báo lỗi 400
        │
        ▼
[LoginUseCase.execute]
   Bước 1: checker.check(username, password)   → Sai? UnauthorizedError (401)
   Bước 2: checker.find_user(username)         → Không thấy? UnauthorizedError (401)
   Bước 3: token_issuer.issue(user.id)         → access token (24h)
   Bước 4: store.create(user.id)               → refresh token (phiên 30 ngày)
        │
        ▼
Trả về: 200 {"token": "...", "refresh_token": "...", "user_id": "u-001", "role": "student"}
```

## Luồng refresh — đổi thẻ mới không cần mật khẩu

```
POST /auth/refresh  {refresh_token: "<chuỗi_nhận_được_khi_đăng_nhập>"}
        │
        ▼
[RefreshTokenUseCase.execute]
   1. store.find(raw)            → Không có? 401 "Phiên đăng nhập đã hết hạn"
   2. session.is_expired(now)    → Hết hạn? thu hồi + 401
   3. users.find_by_id(...)      → User bị xóa? thu hồi + 401
   4. Xoay phiên: revoke phiên cũ + tạo phiên mới + cấp access token mới
        │
        ▼
Trả về: 200 {"token": "...", "refresh_token": "<mới>", "user_id": "...", "role": "..."}
```

**Xoay phiên (rotation):** chuỗi refresh cũ dùng lại là chết ngay — phòng trường hợp chuỗi bị đánh cắp.

## Luồng đăng xuất

```
POST /auth/logout  {refresh_token: "<chuỗi>"}
        │
        ▼
[LogoutUseCase.execute]  → store.revoke(raw) nếu còn phiên
        │
        ▼
Trả về: 200 {"revoked": true}   (chuỗi lạ cũng 200, revoked: false — idempotent)
```

Sau đăng xuất: không refresh được nữa (401). Access token cũ vẫn sống tới khi hết hạn 24h — nếu muốn cắt ngay, phải kiểm tra blacklist ở mọi request (xem `infrastructure/README.md`).

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
- **Đổi kho phiên refresh** (RAM sang Redis): viết class mới cài `RefreshTokenStore`, ghép lại trong `api/routes.py` — không sửa use case
- **Chạy nhiều worker Gunicorn**: kho phiên hiện là singleton trong RAM nên mỗi worker một kho riêng → đổi sang Redis/DB
- **Test**: fake `CredentialChecker`, `RefreshTokenStore`… không cần database thật

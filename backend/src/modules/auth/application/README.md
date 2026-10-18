# auth/application/ — Lớp nghiệp vụ (use case)

## Vai trò

Đây là nơi chứa **toàn bộ nghiệp vụ** của đăng nhập. Lớp này:

- **Không biết gì về HTTP** — không import Flask, không đọc `request`, không `jsonify`
- Không biết dữ liệu nằm ở đâu (DB, RAM…) — chỉ biết "hợp đồng" `CredentialChecker`
- Làm việc thuần với Python: nhận tham số → xử lý → trả kết quả hoặc ném lỗi

Giống như **bếp trưởng**: khách gọi món (quầy order nhận), bếp trưởng quyết định làm thế nào — nhưng bếp trưởng không trực tiếp đứng quầy, cũng không tự đi hái rau.


## Quy tắc cho lớp application
- Vai trò của lớp này: nơi chứa nghiệp vụ, không biết gì về HTTP.
- Cấu trúc một use case: class tên ...UseCase, có hàm execute, phụ thuộc được truyền qua constructor.
- Điều được phép và không được phép.
- Cách phân chia kiểm tra dữ liệu thô (route) và kiểm tra nghiệp vụ (use case).
- Cách xử lý lỗi bằng exception nghiệp vụ.
- Quy tắc về kiểu trả về, đặt tên, kiểm thử, kèm ví dụ đúng và sai.

## Cấu trúc một Use Case

Một use case luôn có 3 thứ:

```python
class TênNghiệpVụUseCase:                    # 1. Tên lớp: ...UseCase
    def __init__(self, checker: Port, ...):  # 2. Phụ thuộc truyền qua constructor
        self._checker = checker

    def execute(self, tham_so) -> KieuTraVe: # 3. Hàm execute — chạy nghiệp vụ
        ...
```

File hiện có:

- **`login.py`** — `LoginUseCase` + `LoginResult` (kiểu trả về): đăng nhập → cấp access token + refresh token
- **`refresh.py`** — `RefreshTokenUseCase` + `RefreshResult`: dùng refresh token đổi token mới (xoay phiên)
- **`logout.py`** — `LogoutUseCase` + `LogoutResult`: thu hồi refresh token (idempotent)
- **`ports/credential_checker.py`** — `CredentialChecker` (hợp đồng)
- **`ports/token_issuer.py`** — `TokenIssuerPort` (hợp đồng)
- **`ports/refresh_token_store.py`** — `RefreshTokenStore` (hợp đồng)

## Luồng trong `LoginUseCase.execute()`

```
execute(username, password)
   │
   ├─ 1. Kiểm tra phòng hờ: rỗng? → UnauthorizedError
   ├─ 2. checker.check(username, password)  → False? UnauthorizedError
   ├─ 3. checker.find_user(username)        → None? UnauthorizedError
   ├─ 4. token_issuer.issue(user.id)        → access token
   └─ 5. store.create(user.id)              → refresh token (phiên)
```

## Luồng trong `RefreshTokenUseCase.execute(refresh_token)`

```
execute(raw)
   │
   ├─ 1. store.find(raw)              → None? UnauthorizedError (401)
   ├─ 2. session.is_expired(now)      → True? revoke + UnauthorizedError
   ├─ 3. users.find_by_id(...)        → None (user bị xóa)? revoke + UnauthorizedError
   └─ 4. Xoay phiên: revoke cũ → store.create → token_issuer.issue → RefreshResult
```

**Tại sao thu hồi khi fail ở bước 2-3?** Phiên không còn dùng được thì giữ trong kho chỉ tốn bộ nhớ (và là mục tiêu dò tìm) — dọn ngay.

## Luồng trong `LogoutUseCase.execute(refresh_token)`

```
execute(raw)
   │
   ├─ raw rỗng hoặc không tìm thấy → LogoutResult(revoked=False)   ← không lỗi!
   └─ tìm thấy → store.revoke(raw) → LogoutResult(revoked=True)
```

**Idempotent:** đăng xuất gọi lại bao nhiêu lần cũng thành công — hành động an toàn không được báo lỗi.

**3 phụ thuộc truyền qua constructor:**

| Port | Việc làm | Dùng bởi |
|------|----------|----------|
| `CredentialChecker` | Kiểm tra mật khẩu + tìm user | Login |
| `TokenIssuerPort` | Cấp access token (application không biết cách ký) | Login, Refresh |
| `RefreshTokenStore` | Tạo/tìm/thu hồi phiên refresh | Login, Refresh, Logout |
| `UserRepository` (module user) | Tìm user theo id — kiểm tra user còn tồn tại, lấy role | Refresh |

**Tại sao mọi lỗi đăng nhập đều cùng một thông điệp "Sai tài khoản hoặc mật khẩu"?**
Để không tiết lộ: người dùng sai ở bước nào (sai username? sai password?). Hacker không dò được từng phần.

**Tại sao lỗi refresh đều là "Phiên đăng nhập đã hết hạn"?**
Không tiết lộ: chuỗi gửi lên là chưa từng tồn tại, đã bị thu hồi, đã hết hạn hay user bị xóa — tất cả cùng một câu trả lời.

## Phân chia kiểm tra: route vs use case

| Kiểm tra | Ở đâu | Ví dụ | Lỗi |
|----------|--------|-------|-----|
| **Dữ liệu thô** | Route (`api/routes.py`) | Thiếu field, sai kiểu (`password` là số), rỗng sau strip | `ValidationError` → 400 |
| **Nghiệp vụ** | Use case (`application/`) | Mật khẩu sai, tài khoản không tồn tại, chưa đủ quyền… | `UnauthorizedError` → 401, `ForbiddenError` → 403… |

Ví dụ phân chia:

```
Route:  thiếu password hoặc password không phải string  → 400 (client gửi sai)
Use case: password đúng nhưng sai                        → 401 (client gửi đúng kiểu, sai giá trị)
```

## Xử lý lỗi bằng exception nghiệp vụ

- Ném exception từ `src/shared/common/errors.py`: `UnauthorizedError`, `NotFoundError`, `ValidationError`…
- **Không** trả tuple `(None, "lỗi")`, **không** trả dict lỗi từ use case
- Route không cần try/catch — `main.py` bắt `AppError` và trả JSON + HTTP status

```python
# Đúng
raise UnauthorizedError("Sai tài khoản hoặc mật khẩu")

# Sai — use case tự trả JSON/HTTP
return {"error": "sai mật khẩu"}, 401
```

## Quy tắc kiểu trả về, đặt tên, kiểm thử

**Kiểu trả về:**

- Luôn trả dataclass có kiểu rõ (ví dụ `LoginResult`), không trả `dict` chung chung
- dataclass `frozen=True` (bất biến)

**Đặt tên:**

- Lớp: `...UseCase` (ví dụ `LoginUseCase`, `RefreshTokenUseCase`, `LogoutUseCase`)
- Method: `execute(...)` — chỉ 1 method chính
- Kiểu trả về: `...Result`

**Kiểm thử:**

- Test trong `tests/unit/modules/auth/application/`
- Truyền **fake** thỏa port — không cần DB/API thật

## Ví dụ đúng / sai

### Đúng

```python
class LoginUseCase:
    def __init__(
        self,
        checker: CredentialChecker,
        token_issuer: TokenIssuerPort,    # mọi phụ thuộc qua constructor
    ) -> None:
        self._checker = checker
        self._token_issuer = token_issuer

    def execute(self, username: str, password: str) -> LoginResult:
        if not self._checker.check(username, password):
            raise UnauthorizedError("Sai tài khoản hoặc mật khẩu")
        ...
        token = self._token_issuer.issue(user.id)
        return LoginResult(token=..., user_id=..., role=...)
```

### Sai

```python
# Sai 1: import Flask — use case biết HTTP
from flask import request
data = request.get_json()

# Sai 2: import platform/infrastructure — dính hạ tầng
from src.platform.security.auth import issue_token

# Sai 3: tự đi lấy dữ liệu — không qua constructor
def execute(self, username, password):
    repo = InMemoryUserRepository()      # tạo thẳng trong execute

# Sai 4: trả dict lỗi thay vì ném exception
if not ok:
    return {"error": "sai mật khẩu"}

# Sai 5: logic nghiệp vụ nằm trong route
@bp.post("/login")
def login():
    if user.password != data["password"]:   # ❌ so sánh mật khẩu ở route
        ...
```

## Khi code theo

1. Use case mới → file mới trong thư mục này, class `...UseCase`, method `execute`
2. Phụ thuộc mới → khai báo port trong `ports/`, truyền qua constructor
3. Viết test fake port cùng lúc với code


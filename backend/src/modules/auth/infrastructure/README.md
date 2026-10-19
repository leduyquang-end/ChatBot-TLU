# auth/infrastructure/ — Cắm hạ tầng thật cho auth

Mỗi file cài 1 port từ `application/ports/`. Application **không** import file này — chỉ api (Composition Root) ghép.

## File

### `repository_credential_checker.py`

Cài `CredentialChecker`:

- `check()` → `repository.check_password(username, password)`
- `find_user()` → `repository.find_by_username(username)`
- Repository mặc định: `get_user_repository()` (in-memory, seed user demo)

### `hmac_token_issuer.py`

Cài `TokenIssuerPort`:

- `issue(user_id)` → gọi `issue_token(user_id)` từ `platform/security/auth.py`

### `in_memory_refresh_token_store.py`

Cài `RefreshTokenStore` — lưu phiên refresh trong RAM:

- `create(user_id)` → `secrets.token_urlsafe(32)` (chuỗi bí mật 256 bit) + tính `expires_at = now + REFRESH_TOKEN_TTL_HOURS`
- `find(raw)` → tra trong dict, không thấy → `None`
- `revoke(raw)` → `pop` khỏi dict, chuỗi lạ thì vô hại (idempotent)
- `now_fn` cho phép test ghim thời gian (không cần chờ hết hạn thật)

**Singleton `get_refresh_token_store()`** — giống `get_user_repository()`: phiên phải sống qua nhiều request nên không tạo lại mỗi lần gọi.

> Hạn chế: RAM của 1 worker ≠ RAM của worker khác. Chạy Gunicorn nhiều worker hoặc cần chia sẻ phiên → thay bằng Redis/DB (viết class mới cài `RefreshTokenStore`, không sửa use case).

> Access token vẫn là HMAC tự kiểm hạn — đăng xuất thu hồi refresh token chứ không "chết ngay" access token. Muốn cắt ngay: thêm blacklist tra trong `verify_token()` (xem `src/platform/security/auth.py`).

## Luồng ghép (ở api/routes.py)

```
LoginUseCase(
    checker=RepositoryCredentialChecker(),   # cài CredentialChecker
    token_issuer=HmacTokenIssuer(),          # cài TokenIssuerPort
    store=get_refresh_token_store(),         # cài RefreshTokenStore (singleton)
)

RefreshTokenUseCase(
    store=get_refresh_token_store(),
    token_issuer=HmacTokenIssuer(),
    users=get_user_repository(),             # cài UserRepository (module user)
)

LogoutUseCase(store=get_refresh_token_store())
```

## Khi code theo

**Đổi token sang JWT library khác:** viết class mới cài `TokenIssuerPort`, đổi trong `api/routes.py` — **không sửa** `login.py`.

**Đổi kho phiên sang Redis:** viết class mới cài `RefreshTokenStore` (giữ nguyên TTL, `secrets`), thay `get_refresh_token_store()` trong `api/routes.py` — **không sửa** `refresh.py`, `logout.py`, `login.py`.

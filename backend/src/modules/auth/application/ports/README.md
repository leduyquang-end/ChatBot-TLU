# auth/application/ports/ — Hợp đồng (interface)

Đây là nơi application khai báo "tôi cần ai làm những việc này" — không biết và không quan tâm người cài làm bằng gì (DB, API, RAM…).

## File

### `credential_checker.py`

```python
class CredentialChecker(Protocol):
    def check(self, username: str, password: str) -> UserRecord | None: ...
```

`UserRecord` (trong `user_lookup.py`) là Protocol chỉ có `id` + `role` — auth **không import entity** của module user.

### `user_lookup.py`

```python
class UserLookup(Protocol):
    def find_by_id(self, user_id: str) -> UserRecord | None: ...
```

### `token_issuer.py`

```python
class TokenIssuerPort(Protocol):
    def issue(self, user_id: str) -> str: ...
```

### `refresh_token_store.py`

```python
class RefreshTokenStore(Protocol):
    def create(self, user_id: str) -> RefreshToken: ...
    def find(self, raw_token: str) -> RefreshToken | None: ...
    def revoke(self, raw_token: str) -> None: ...
```

Lưu ý: use case **không tự sinh** chuỗi bí mật (application không biết cách sinh an toàn) — để `create()` của store lo.

## Nguyên tắc

- Port = `Protocol` với docstring mô tả hành vi
- Port **không** import infrastructure hay platform (import `domain/` thì được — domain là của chính module)
- Muốn đổi implementation → viết class mới thỏa method, truyền vào use case qua constructor

## Sơ đồ ghép

```
LoginUseCase ─── cần ──▶ CredentialChecker    ◀── cài ── RepositoryCredentialChecker
              ─── cần ──▶ TokenIssuerPort      ◀── cài ── HmacTokenIssuer
              ─── cần ──▶ RefreshTokenStore    ◀── cài ── InMemoryRefreshTokenStore

RefreshTokenUseCase ── cần ──▶ RefreshTokenStore ◀── cài ── InMemoryRefreshTokenStore
                     ── cần ──▶ TokenIssuerPort   ◀── cài ── HmacTokenIssuer
                     ── cần ──▶ UserRepository     ◀── cài ── InMemoryUserRepository (module user)

LogoutUseCase ─────── cần ──▶ RefreshTokenStore   ◀── cài ── InMemoryRefreshTokenStore
```

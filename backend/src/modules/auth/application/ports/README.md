# auth/application/ports/ — Hợp đồng (interface)

Đây là nơi application khai báo "tôi cần ai làm những việc này" — không biết và không quan tâm người cài làm bằng gì (DB, API, RAM…).

## File

### `credential_checker.py`

```python
class CredentialChecker(Protocol):
    def check(self, username: str, password: str) -> bool: ...
    def find_user(self, username: str) -> User | None: ...
```

### `token_issuer.py`

```python
class TokenIssuerPort(Protocol):
    def issue(self, user_id: str) -> str: ...
```

## Nguyên tắc

- Port = `Protocol` với docstring mô tả hành vi
- Port **không** import infrastructure hay platform
- Muốn đổi implementation → viết class mới thỏa method, truyền vào use case qua constructor

## Sơ đồ ghép

```
LoginUseCase ── cần ──▶ CredentialChecker ◀── cài ── RepositoryCredentialChecker
              ── cần ──▶ TokenIssuerPort    ◀── cài ── HmacTokenIssuer
```

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

## Luồng ghép (ở api/routes.py)

```
LoginUseCase(
    checker=RepositoryCredentialChecker(),   # cài CredentialChecker
    token_issuer=HmacTokenIssuer(),          # cài TokenIssuerPort
)
```

## Khi code theo

**Đổi token sang JWT library khác:** viết class mới cài `TokenIssuerPort`, đổi trong `api/routes.py` — **không sửa** `login.py`.

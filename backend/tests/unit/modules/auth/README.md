# unit/modules/auth/ — Test module auth

| Thư mục con | Test cho |
|-------------|----------|
| `api/` | Endpoint `/auth/login`, `/auth/refresh`, `/auth/logout` (4 bước: nhận → validate → use case → trả kết quả) |
| `application/` | `LoginUseCase`, `RefreshTokenUseCase`, `LogoutUseCase` với fake port |
| `domain/` | `RefreshToken`: luật hết hạn, bất biến |
| `infrastructure/` | `InMemoryRefreshTokenStore`: create/find/revoke, singleton |

Chạy riêng: `python -m pytest tests/unit/modules/auth -q`

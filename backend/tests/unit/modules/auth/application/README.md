# unit/modules/auth/application/ — Test LoginUseCase

## File

### `test_login.py`

Test use case thuần với **fake port** (không cần DB, không ký token thật):

- `FakeChecker` — cài `CredentialChecker`, cấu hình được: `valid` (mật khẩu đúng?), `user` (tìm thấy user?)
- `FakeTokenIssuer` — cài `TokenIssuerPort`, trả `fake-token-{user_id}` và ghi lại `issued_for`

| Test | Kiểm tra |
|------|----------|
| `test_login_thanh_cong_tra_ve_login_result` | Thành công → `LoginResult` đúng token/user_id/role; issuer nhận đúng user_id |
| `test_sai_mat_khau_nem_unauthorized` | Sai mật khẩu → `UnauthorizedError` (401) |
| `test_user_khong_ton_tai_nem_unauthorized` | User không tồn tại → `UnauthorizedError` |
| `test_username_rong_nem_unauthorized` | Username rỗng/khoảng trắng → `UnauthorizedError` |
| `test_password_rong_nem_unauthorized` | Password rỗng → `UnauthorizedError` |
| `test_khong_tiet_lo_buoc_sai_tai_thong_diep` | Mọi fail cùng một thông điệp |

Chạy: `python -m pytest tests/unit/modules/auth/application -q`

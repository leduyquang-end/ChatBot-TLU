# unit/modules/auth/api/ — Test endpoint login

## File

### `test_routes.py`

Test `/auth/login` qua Flask test client (không cần server thật):

| Test | Kiểm tra |
|------|----------|
| `test_login_thieu_username` | Thiếu username → 400 `VALIDATION_ERROR` |
| `test_login_thieu_password` | Thiếu password → 400 `VALIDATION_ERROR` |
| `test_login_password_khong_phai_string` | Password là số (không phải string) → 400 |
| `test_login_sai_mat_khau` | Sai mật khẩu → 401 `UNAUTHORIZED` |
| `test_login_thanh_cong` | Đăng nhập đúng (sinhvien01/demo-password) → 200, có token |

## Quy tắc endpoint (đã verify)

- 4 bước: nhận dữ liệu → kiểm tra thô → gọi use case → trả kết quả
- Thiếu field bắt buộc → `ValidationError` (400)
- Route **không** chứa logic nghiệp vụ — mọi việc để ở `LoginUseCase`

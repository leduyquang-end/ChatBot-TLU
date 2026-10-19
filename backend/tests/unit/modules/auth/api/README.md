# unit/modules/auth/api/ — Test endpoint auth

## File

### `test_routes.py`

Test qua Flask test client (không cần server thật):

| Test | Kiểm tra |
|------|----------|
| `test_login_thieu_username` | Thiếu username → 400 `VALIDATION_ERROR` |
| `test_login_thieu_password` | Thiếu password → 400 `VALIDATION_ERROR` |
| `test_login_password_khong_phai_string` | Password là số (không phải string) → 400 |
| `test_login_sai_mat_khau` | Sai mật khẩu → 401 `UNAUTHORIZED` |
| `test_login_thanh_cong` | Đăng nhập đúng → 200, có `token` + `refresh_token` |
| `test_refresh_thieu_refresh_token` | Thiếu `refresh_token` → 400 |
| `test_refresh_phien_khong_hop_le` | Chuỗi lạ → 401 |
| `test_refresh_thanh_cong_xoay_phien` | Login → refresh → 200, refresh_token mới khác cũ |
| `test_logout_thieu_refresh_token` | Thiếu `refresh_token` → 400 |
| `test_logout_khong_phai_string` | `refresh_token` là số → 400 |
| `test_logout_thanh_cong_va_phien_het_hieu_luc` | Logout → 200 `revoked=true`; refresh chuỗi cũ → 401 |
| `test_logout_phien_khong_ton_tai_van_200` | Chuỗi lạ → 200 `revoked=false` (idempotent) |

## Quy tắc endpoint (đã verify)

- 4 bước: nhận dữ liệu → kiểm tra thô → gọi use case → trả kết quả
- Thiếu field bắt buộc → `ValidationError` (400)
- Route **không** chứa logic nghiệp vụ — mọi việc để ở use case
- Test refresh/logout dùng **chuỗi thật lấy từ `/auth/login`** — không hardcode token

# unit/modules/auth/application/ — Test Login, Refresh, Logout

Mọi test đều chạy với **fake port** (không cần DB, không ký token thật):

- `FakeChecker` — cài `CredentialChecker`, cấu hình được: `valid` (mật khẩu đúng?), `user` (tìm thấy user?)
- `FakeTokenIssuer` — cài `TokenIssuerPort`, trả `fake-token-{user_id}` và ghi lại `issued_for`
- `FakeStore` — cài `RefreshTokenStore`, tạo phiên `rt-{n}` trong RAM, ghi lại `revoked`/`created_for`
- `FakeUsers` — cài `UserRepository` (chỉ cần `find_by_id`)

## File

### `test_login.py`

| Test | Kiểm tra |
|------|----------|
| `test_login_thanh_cong_tra_ve_login_result` | Thành công → `LoginResult` đúng token/user_id/role; issuer nhận đúng user_id |
| `test_login_tao_phien_refresh` | Login tạo phiên refresh, store nhận đúng user_id |
| `test_sai_mat_khau_nem_unauthorized` | Sai mật khẩu → `UnauthorizedError` (401) |
| `test_user_khong_ton_tai_nem_unauthorized` | User không tồn tại → `UnauthorizedError` |
| `test_username_rong_nem_unauthorized` | Username rỗng/khoảng trắng → `UnauthorizedError` |
| `test_password_rong_nem_unauthorized` | Password rỗng → `UnauthorizedError` |
| `test_khong_tiet_lo_buoc_sai_tai_thong_diep` | Mọi fail cùng một thông điệp |

### `test_refresh.py`

| Test | Kiểm tra |
|------|----------|
| `test_refresh_thanh_cong_xoay_phien` | Thành công → token mới, phiên mới khác phiên cũ, phiên cũ bị thu hồi |
| `test_refresh_phien_khong_ton_tai_nem_unauthorized` | Chuỗi lạ → 401, không thu hồi gì |
| `test_refresh_phien_het_han_thu_hoi_va_nem_unauthorized` | Phiên hết hạn → dọn khỏi kho + 401 |
| `test_refresh_user_bi_xoa_thu_hoi_va_nem_unauthorized` | User bị xóa → thu hồi phiên + 401 |
| `test_refresh_chuoi_rong_nem_unauthorized` | Chuỗi rỗng/khoảng trắng → 401 |
| `test_khong_tiet_lo_ly_do_tai_thong_diep` | Không tồn tại / hết hạn / user xóa → cùng một thông điệp |

### `test_logout.py`

| Test | Kiểm tra |
|------|----------|
| `test_logout_thanh_cong_thu_hoi_phien` | Thành công → `revoked=True`, phiên biến mất |
| `test_logout_phien_khong_ton_tai_van_thanh_cong` | Idempotent → `revoked=False`, không lỗi |
| `test_logout_lan_hai_khong_sai_nua` | Logout lần 2 → `revoked=False` |
| `test_logout_chuoi_rong_tra_false` | Chuỗi rỗng → `revoked=False` |

Chạy: `python -m pytest tests/unit/modules/auth/application -q`

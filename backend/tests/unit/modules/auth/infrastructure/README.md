# unit/modules/auth/infrastructure/ — Test kho phiên refresh

## File

### `test_in_memory_refresh_token_store.py`

Test `InMemoryRefreshTokenStore` với `now_fn` ghim thời gian (không chờ hết hạn thật):

| Test | Kiểm tra |
|------|----------|
| `test_create_tra_phien_dung_han_va_tim_duoc` | Tạo phiên → đúng hạn, `find` trả về |
| `test_create_lan_hai_tao_chuoi_khac_nhau` | Mỗi lần tạo ra chuỗi bí mật khác nhau |
| `test_find_chuoi_la_tra_none` | Chuỗi lạ → `None` |
| `test_revoke_xoa_phien_va_revoke_lai_van_an_toan` | Thu hồi xong → mất; thu hồi lần 2 vô hại |
| `test_store_khong_tu_het_han_lam_het_han_la_nghiep_vu_cua_domain` | Quá hạn store vẫn `find` được — quyết định "hết hạn" là của `RefreshToken.is_expired` |
| `test_singleton_tra_cung_mot_object` | `get_refresh_token_store()` trả cùng một object |

Chạy: `python -m pytest tests/unit/modules/auth/infrastructure -q`

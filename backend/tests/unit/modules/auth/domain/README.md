# unit/modules/auth/domain/ — Test RefreshToken

## File

### `test_refresh_token.py`

Test entity thuần — không fake gì cả (domain không phụ thuộc hạ tầng):

| Test | Kiểm tra |
|------|----------|
| `test_chua_het_han_truoc_moc_het_han` | Trước `expires_at` → chưa hết hạn |
| `test_het_han_dung_tai_moc_het_han` | Đúng `expires_at` → đã hết hạn (mốc đóng) |
| `test_het_han_sau_moc_het_han` | Sau `expires_at` → đã hết hạn |
| `test_phien_bat_bien_khong_sua_duoc` | Gán thuộc tính → `FrozenInstanceError` |

Chạy: `python -m pytest tests/unit/modules/auth/domain -q`

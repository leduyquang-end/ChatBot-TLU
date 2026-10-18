# user/api/ — "Quầy order" của phòng user

## File chính

### `routes.py`

Blueprint `user`, tiền tố `/user`:

| Endpoint | Method | Việc làm |
|----------|--------|----------|
| `/user/me` | GET | Đọc Bearer token → trả hồ sơ user hiện tại |

Đăng ký Blueprint trong `src/main.py`. Validate/parse mỏng, lỗi → ném `AppError`.

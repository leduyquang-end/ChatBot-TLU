# auth/api/ — "Quầy order" của phòng đăng nhập

## Mục đích

Đây là nơi nhận yêu cầu đăng nhập từ người dùng (qua HTTP), kiểm tra thô dữ liệu, rồi chuyển cho "bếp trưởng" (use case) xử lý. **Không chứa logic nghiệp vụ** — chỉ làm "quầy order" mỏng.

# Quy tắc cho lớp API

- Mỗi endpoint nằm trong routes.py, dùng Blueprint.
- Theo đúng 4 bước: nhận dữ liệu → kiểm tra thô → gọi use case → trả kết quả.
- Không chứa logic nghiệp vụ trong route.
- Thiếu field bắt buộc → raise ValidationError (400).
- Blueprint mới phải đăng ký trong src/main.py.

Sai:
    if user.password != data["password"]: ...

Đúng:
    result = LoginUseCase(...).execute(...)
    
## File chính

### `routes.py`

Chứa một Blueprint (Flask Blueprint = "quầy order" riêng cho nhóm chức năng này, có tiền tố `/auth`).

| Endpoint | Method | Việc làm |
|----------|--------|----------|
| `/auth/login` | POST | Nhận `{username, password}` → trả `{token, refresh_token, user_id, role}` |
| `/auth/refresh` | POST | Nhận `{refresh_token}` → trả token + phiên mới (xoay phiên) |
| `/auth/logout` | POST | Nhận `{refresh_token}` → thu hồi phiên, trả `{revoked}` |

`_read_refresh_token()` là hàm chung cho 2 endpoint sau: kiểm tra `refresh_token` có phải string và không rỗng không — thiếu/sai → `ValidationError` (400).

## Cách hoạt động

Mọi endpoint đều theo đúng 4 bước:

1. Nhận JSON từ request
2. Kiểm tra thô: field bắt buộc có chưa? Thiếu/sai kiểu → ném `ValidationError` (400)
3. Gọi use case (bếp trưởng) để xử lý — logic nghiệp vụ không nằm ở đây
4. Trả kết quả về cho người dùng

Nếu là refresh/logout thất bại nghiệp vụ (401), use case tự ném `UnauthorizedError` — route không try/catch, `main.py` trả JSON + mã HTTP.

## Quy tắc khi viết endpoint mới

Mọi endpoint trong ứng dụng đều theo mẫu này:

```python
@bp.post("/xxx")
def xxx():
    data = request.get_json(silent=True) or {}   # 1. Nhận dữ liệu
    ...  # 2. Kiểm tra thô → ValidationError nếu sai
    result = SomeUseCase(...).execute(...)       # 3. Gọi use case
    return jsonify(...)                          # 4. Trả kết quả
```

Đăng ký Blueprint mới trong `src/main.py`.

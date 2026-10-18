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
| `/auth/login` | POST | Nhận `{username, password}` → trả `{token, user_id, role}` |

## Cách hoạt động

1. Nhận JSON từ request
2. Kiểm tra: có username và password chưa? Thiếu → ném `ValidationError` (trả về 400)
3. Gọi `LoginUseCase` (bếp trưởng) để xử lý đăng nhập
4. Trả kết quả về cho người dùng

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

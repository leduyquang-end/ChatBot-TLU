# auth/domain/ — Luật nghiệp vụ cốt lõi của auth

## Mục đích

Giữ các khái niệm và luật nghiệp vụ cốt lõi, không biết về Flask, DB hay hạ tầng nào.

Auth **không có thực thể của riêng mình** — phần đăng nhập dùng chung `User` của module `user` (`src/modules/user/domain/user.py`). File duy nhất ở đây là `RefreshToken` vì "phiên refresh" là khái niệm riêng của auth.

## File

### `refresh_token.py`

```python
@dataclass(frozen=True)
class RefreshToken:
    token: str          # chuỗi bí mật client giữ để đổi token mới
    user_id: str        # phiên này thuộc về ai
    issued_at: datetime # khi nào tạo
    expires_at: datetime # khi nào hết hạn

    def is_expired(self, now: datetime) -> bool: ...
```

- **Bất biến (frozen):** tạo xong không sửa được — muốn có phiên mới thì tạo phiên mới (đúng nghĩa "phiên", không cập nhật dở dang)
- **So sánh theo giá trị:** 2 object giống hệt mọi trường là một phiên
- **Luật "hết hạn" nằm trong object:** `is_expired(now)` — tại đúng mốc `expires_at` là đã hết hạn (mốc đóng). Use case chỉ hỏi, không tự tính `now > expires_at` ở ngoài

## Quy tắc cho lớp domain

- Vai trò của lớp này: giữ khái niệm và luật nghiệp vụ cốt lõi, không biết về Flask, DB hay hạ tầng nào.
- Entity và value object: entity có id và thay đổi theo thời gian, value object so sánh theo giá trị và nên bất biến.
- Bảo vệ luật nghiệp vụ: luật nằm bên trong object, thay đổi trạng thái qua hàm có tên nghiệp vụ (ví dụ `is_expired`), không tính toán rải rác ở nơi khác.
- Exception nghiệp vụ: dùng exception từ `shared/common/errors.py` (`UnauthorizedError`…), tầng API trả về mã HTTP.
- Không import Flask, không import infrastructure, không đọc biến môi trường.

## Khi code theo

- Xuất hiện khái niệm mới của auth (ví dụ `LoginAttempt` ghi lần thử đăng nhập, chặn brute-force) → tạo entity ở đây, luật nghiệp vụ (ví dụ "5 lần sai thì khóa") viết thành method trong object.
- Đừng đưa logic tính toán của domain vào use case hay route — domain test được độc lập, không cần fake gì cả.

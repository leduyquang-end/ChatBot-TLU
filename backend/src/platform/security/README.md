# security/ — "Hệ thống khóa cửa" của chương trình

## Mục đích

Chứa các công cụ bảo mật dùng chung: mã hóa mật khẩu, tạo và kiểm tra "thẻ ra vào" (token), kiểm tra quyền hạn.

## File chính

### `auth.py`

Đây là "tủ khóa" của toàn ứng dụng. Có các công cụ sau:

| Hàm | Vai trò | Giải thích đơn giản |
|-----|---------|----------------------|
| `hash_password` | Mã hóa mật khẩu | Biến "123456" thành chuỗi ký tự không đọc được ("a3f8…"), lưu vào kho. Ai đó ăn cắp kho dữ liệu cũng không đọc được mật khẩu thật |
| `verify_password` | Kiểm tra mật khẩu | So sánh mật khẩu người dùng nhập với chuỗi đã mã hóa — dùng cách so sánh an toàn (không lộ thời gian) để hacker không dò được |
| `issue_token` | Cấp "thẻ ra vào" | Sau khi đăng nhập thành công, cấp một chuỗi đặc biệt (token). Người dùng giữ thẻ này để khỏi phải đăng nhập lại mỗi lần |
| `verify_token` | Kiểm tra "thẻ ra vào" | Khi người dùng gửi thẻ đến, chương trình kiểm tra: thẻ có đúng không? đã hết hạn chưa? Sai hoặc hết hạn → từ chối |
| `require_role` | Kiểm tra quyền hạn | Ví dụ: chỉ "quản trị viên" (admin) mới được làm việc X |
| `sanitize_input` | Làm sạch dữ liệu đầu vào | Loại bỏ ký tự có thể gây hại trước khi gửi câu hỏi cho AI |

## Cách "thẻ ra vào" (token) hoạt động

1. Người dùng đăng nhập thành công → server tạo token dạng: `user_id.het_han.ky_ten_duy_nhat`
2. Token này được "ký" bằng một bí mật gọi là `APP_SECRET` — giống như con dấu riêng của trường
3. Mỗi lần gọi API, người dùng gửi kèm token trong header `Authorization: Bearer …`
4. Server dùng `APP_SECRET` để verify token có bị làm giả không

**Lưu ý quan trọng:** `APP_SECRET` phải được thay đổi khi lên môi trường thật (production). Nếu không đổi, ai đó có thể tự tạo thẻ giả mạo.

## Ghi chú kỹ thuật

- **Đồng hồ token:** `issue_token`/`verify_token` dùng `time.time()` (đồng hồ tường epoch) — nhất quán giữa mọi worker/process/máy. (Trước đây dùng `os.times().elapsed` = 0.0 cố định trên Windows → token không bao giờ hết hạn.)
- **So sánh chữ ký:** dạng bytes qua `hmac.compare_digest` — chuỗi không phải ASCII không làm ném `TypeError` (trước là lỗi 500).
- **Mật khẩu:** PBKDF2-SHA256 200.000 vòng, salt 16 byte ngẫu nhiên; mật khẩu bị cắt ở 1024 ký tự (cả hash lẫn verify) để không lạm dụng CPU.
- **Thiếu `APP_SECRET`:** fallback secret dev + cảnh báo một lần `event=security.default_secret` (AGENT.md 11.1 — chỉ đọc từ môi trường). Secret toàn khoảng trắng cũng bị coi là thiếu.
- **`APP_SECRET` quá ngắn** (< 16 ký tự): vẫn dùng nhưng cảnh báo một lần `event=security.weak_secret` (dễ bị dò để giả chữ ký).
- `sanitize_input`: lọc ký tự điều khiển (giữ `\n`, `\t`), cắt đúng `max_length`, bỏ khoảng trắng sót do cắt.

# platform/ — "Hệ thống kỹ thuật" của tòa nhà

Đây là nơi chứa các công cụ **dùng chung cho tất cả** phòng ban, không thuộc phòng ban nào riêng.

Giống như trong một công ty:
- **Hệ thống camera** (logging) — ghi lại mọi chuyện xảy ra
- **Hệ thống chìa khóa** (security) — ai được vào phòng nào

## Thư mục con

| Thư mục | Vai trò |
|---------|---------|
| `logging/` | Camera an ninh — ghi lại sự kiện để khi có sự cố xem lại được |
| `security/` | Khóa và chìa khóa — mã hóa mật khẩu, cấp/thăm dò "thẻ ra vào" (token) |

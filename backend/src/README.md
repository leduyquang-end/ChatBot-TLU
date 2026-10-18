# Thư mục src/ — "Bộ não" của chương trình

Đây là nơi chứa toàn bộ code chính của backend. Nếu backend là một tòa nhà văn phòng thì `src/` là **tầng làm việc** — mọi tính năng đều nằm ở đây.

## File quan trọng nhất: `main.py`

File `main.py` giống như **lễ tân của tòa nhà**. Khi chương trình chạy, việc đầu tiên là gọi file này để:

1. Đọc biến môi trường (`.env`) — giống như đọc "sổ tay cấu hình" (ví dụ: địa chỉ máy chủ, mã khóa API)
2. Cấu hình ghi log (ghi lại sự kiện xảy ra)
3. Đăng ký các "phòng ban" (gọi là blueprint trong Flask — Flask là thư viện Python để xây web server)
4. Thêm trang kiểm tra sức khỏe `/health` — để biết server có đang chạy không

## Thư mục con

| Thư mục | Vai trò trong ví dụ đời thường |
|---------|--------------------------------|
| `modules/` | Các **phòng ban**: ai làm đăng nhập, ai trả lời chatbot, ai quản lý thông tin người dùng |
| `platform/` | **Hệ thống kỹ thuật** chung: camera an ninh (logging), khóa cửa (security) |
| `shared/` | **Đồ dùng chung** cho mọi phòng: bảng chỉ dẫn lỗi, sổ địa chỉ cấu hình |

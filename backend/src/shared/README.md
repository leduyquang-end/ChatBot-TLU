# shared/ — "Đồ dùng chung" cho mọi phòng ban

Đây là nơi chứa những thứ **mọi phòng ban đều cần dùng**, nhưng không thuộc phòng ban nào riêng.

Giống như trong một văn phòng chung: máy in, điều hòa, bảng chỉ dẫn — ai cũng dùng, nhưng không phải của phòng kế toán hay phòng nhân sự.

## Thư mục con

| Thư mục | Vai trò |
|---------|---------|
| `common/` | Bảng chỉ dẫn lỗi — định nghĩa các loại lỗi mà chương trình ném ra (ví dụ: "sai mật khẩu", "không tìm thấy") |
| `config/` | Sổ tay cấu hình — đọc biến môi trường (`.env`) để biết địa chỉ máy chủ, mã khóa… |
| `database/` | Nơi kết nối cơ sở dữ liệu (hiện chưa dùng — đang lưu tạm trong RAM) |
| `events/` | Nơi xử lý sự kiện nội bộ (hiện chưa dùng) |

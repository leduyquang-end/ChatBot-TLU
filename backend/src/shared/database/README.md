# database/ — Nơi kết nối cơ sở dữ liệu (chưa dùng)

## Mục đích

Hiện tại chương trình **chưa dùng** cơ sở dữ liệu thật — thông tin lưu tạm trong bộ nhớ (RAM), nên khi tắt chương trình là mất.

Folder này được chuẩn bị sẵn cho tương lai: khi cần lưu dữ liệu vĩnh viễn (MySQL, PostgreSQL…), code kết nối sẽ nằm ở đây.

## Khi nào cần dùng

Khi muốn:
- Lưu lịch sử hội thoại của sinh viên (hiện mất khi restart)
- Có nhiều tài khoản người dùng thật (hiện chỉ có 2 tài khoản demo)

## Cách mở rộng

1. Viết code kết nối DB trong folder này
2. Trong `modules/*/infrastructure/`, viết "repository" mới thay cho bản in-memory
3. **Không sửa** `application/` — chỉ thay phần implementation (cách làm): như đổi tủ lạnh mới mà không thay thực đơn nhà hàng

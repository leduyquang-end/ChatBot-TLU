# auth/domain/ — (Trống)

## Mục đích

Auth **không có thực thể riêng** — dùng `User` của module `user` (`src/modules/user/domain/user.py`).

Chỉ tạo file ở đây khi xuất hiện khái niệm riêng của auth (ví dụ: `RefreshToken` cho gia hạn token, `LoginAttempt` cho ghi lần thử đăng nhập).


Vai trò: giữ các khái niệm và luật nghiệp vụ cốt lõi, không biết về Flask, DB hay hạ tầng nào.
Entity và value object: entity có id và thay đổi theo thời gian, value object so sánh theo giá trị và nên bất biến.
Bảo vệ luật nghiệp vụ: luật nằm bên trong object, thay đổi trạng thái qua hàm có tên nghiệp vụ như order.cancel(), không gán trực tiếp thuộc tính.
Exception nghiệp vụ: định nghĩa riêng trong domain, chuyển sang mã HTTP ở tầng API.
Kiểm thử, đặt tên, ví dụ đúng và sai.
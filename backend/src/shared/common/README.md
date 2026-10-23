# common/ — "Bảng chỉ dẫn lỗi" của chương trình

## Mục đích

Chương trình cần một cách chung (thống nhất) để báo lỗi. File này định nghĩa các loại lỗi mà cả ứng dụng đều dùng chung.

Giống như biển báo giao thông: ai nhìn "DỪNG" cũng biết phải dừng lại, không cần giải thích từng lần.

## File chính

### `errors.py`

Chứa lớp cơ sở `AppError` và các lớp con. Mỗi loại lỗi có **mã lỗi** (code) và **mã HTTP** (mã trạng thái gửi về trình duyệt):

| Lỗi | HTTP | Khi nào xảy ra |
|-----|------|-----------------|
| `ValidationError` | 400 | Dữ liệu người dùng gửi lên sai (ví dụ: để trống mật khẩu) |
| `UnauthorizedError` | 401 | Chưa đăng nhập hoặc token sai/hết hạn |
| `ForbiddenError` | 403 | Đăng nhập rồi nhưng không đủ quyền (ví dụ: sinh viên muốn xóa dữ liệu trường) |
| `NotFoundError` | 404 | Không tìm thấy thứ được yêu cầu (ví dụ: user không tồn tại) |
| `ExternalServiceError` | 503 | Dịch vụ bên ngoài lỗi (AI, Chroma, Neo4j) |
| `NoRelevantContextError` | 200 | Không có tài liệu nào phù hợp để trả lời (xem ADR-09) |
| `ConfigError` | 500 | Thiếu hoặc sai cấu hình khi khởi động chương trình |
| `InternalError` | 500 | Lỗi không mong đợi — đã ghi log, người dùng chỉ thấy thông báo chung |

## Cách hoạt động

Trong `src/main.py`, có một "bộ xử lý lỗi tập trung": khi bất kỳ đâu trong chương trình ném (raise) một lỗi thuộc `AppError`, nó sẽ tự động chuyển thành JSON trả về cho người dùng với định dạng:

```json
{"error": {"code": "UNAUTHORIZED", "message": "Cần đăng nhập"}}
```

Người dùng không cần biết chi tiết kỹ thuật — chỉ cần biết mã lỗi và thông điệp.

# database/ — Nơi kết nối cơ sở dữ liệu

## Mục đích

Chứa code kết nối cơ sở dữ liệu dùng chung. Hiện hỗ trợ **SQLite** (thư viện chuẩn Python, không cần cài thêm) — sẵn để lưu lịch sử hội thoại, tài khoản thật thay vì RAM.

## File chính

### `connection.py`

| Hàm | Việc làm |
|-----|----------|
| `connect(url)` | Mở connection theo URL `sqlite:///<đường_dẫn>` (tự tạo thư mục cha). Cơ sở khác (MySQL, PostgreSQL…) → ném `ConfigError` rõ ràng |
| `get_connection()` | Mở connection theo `Settings.database_url` (`DATABASE_URL` trong `.env`) |
| `db_connection()` | Dùng trong `with` — tự đóng connection |

Mỗi lần gọi trả connection mới (sqlite3 không thread-safe). Connection bật `row_factory = sqlite3.Row` (đọc theo tên cột) và `PRAGMA foreign_keys = ON`.

Ví dụ:

```python
from src.shared.database import db_connection

with db_connection() as conn:
    row = conn.execute("SELECT 1 AS ok").fetchone()
    conn.commit()
```

## Khi nào cần dùng

- Lưu lịch sử hội thoại của sinh viên (hiện mất khi restart)
- Có nhiều tài khoản người dùng thật (hiện chỉ có 2 tài khoản demo)

## Cách mở rộng

1. Hỗ trợ cơ sở khác: thêm scheme trong `_parse()`/`connect()` + driver tương ứng (ví dụ `psycopg`) trong folder này
2. Trong `modules/*/infrastructure/`, viết "repository" mới thay cho bản in-memory (ví dụ `SqlUserRepository`)
3. **Không sửa** `application/` — chỉ thay phần implementation (cách làm): như đổi tủ lạnh mới mà không thay thực đơn nhà hàng

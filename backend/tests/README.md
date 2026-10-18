# tests/ — Nơi "kiểm tra" code

## Mục đích

Test = viết code kiểm tra xem code chính có **hoạt động đúng** không. Giống như bài kiểm tra cuối kỳ — nếu code "học bài" đúng thì pass, sai thì fail.

## Cách chạy

```bash
cd backend
python -m pytest tests/unit -q          # unit test (nhanh, không cần dịch vụ)
python -m pytest tests/integration -q   # integration test (cần Chroma/Neo4j thật)
python -m pytest -q                     # tất cả
```

## Cấu trúc

| Thư mục | Mục đích |
|---------|----------|
| `unit/` | Test thuần — dùng fake (giả lập), chạy offline, không cần gì ngoài |
| `integration/` | Test tích hợp — cần dịch vụ thật (dự phòng) |
| `e2e/` | Test đầu cuối — test cả luồng từ HTTP (dự phòng) |

Cấu trúc `tests/unit/` **phản chiếu** cấu trúc `src/`:

```
src/modules/chat/application/chat_pipeline.py
tests/unit/modules/chat/application/test_chat_pipeline.py
```

## Quy ước

- Unit test **không** gọi AI/Chroma/Neo4j thật — dùng fake (giả lập) cài port (xem `test_chat_pipeline.py`)
- Đặt tên `test_<hành_vi>_<kết_quả>`
- Mỗi lần sửa `application/` hoặc `domain/` → chạy `pytest tests/unit -q` trước khi commit

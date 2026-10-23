# scripts/ — Các lệnh chạy tay

Đây là nơi chứa các lệnh bạn chạy trực tiếp từ terminal (không qua web). Hiện có 1 lệnh chính:

## `ingest_tlu.py` — Nạp tài liệu vào kho (QT-02)

```bash
python backend/scripts/ingest_tlu.py data             # từ repo root (khuyến nghị)
cd backend
python scripts/ingest_tlu.py              # mặc định: <repo>/data/source
python scripts/ingest_tlu.py path/to/dir  # thư mục tùy chọn
```

Lưu ý: file `.doc` (Word 97-2003) chỉ đọc được khi máy có Microsoft Word (Windows) — file hỏng sẽ vào `documents_failed` của báo cáo.

### Lệnh này làm gì?

Giống như **thủ thư xử lý sách mới**:

```
Tài liệu thô (md, docx, pdf...) trong data/source
  → Đọc nội dung (loaders)
  → Làm sạch + cắt nhỏ (cleaning, chunking)
  → Biến thành vector (embed) → lưu vào ChromaDB
  → AI trích xuất thực thể/quan hệ → lưu vào Neo4j
  → In ra báo cáo JSON (bao nhiêu file ok, bao nhiêu chunk, entity...)
```

### Khi code theo

Script chỉ là "điều phối" — import pipeline từ `src/`, không viết logic nghiệp vụ trong này.

Chạy trực tiếp với Python (không cần Docker) — chỉ cần `.env` hợp lệ + Chroma/Neo4j đang chạy.

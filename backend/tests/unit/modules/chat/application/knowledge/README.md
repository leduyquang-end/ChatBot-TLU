# unit/modules/chat/application/knowledge/ - Test pipeline nạp tri thức

| File | Test cho |
|------|----------|
| `test_chunking.py` | `chunking.py` — cắt đoạn, metadata |
| `test_cleaning.py` | `cleaning.py` — chuẩn hóa, bỏ tiêu đề lặp, lọc chữ Trung |
| `test_dedup.py` | `dedup.py` — gộp thực thể theo cosine/tên |
| `test_table_processing.py` | `table_processing.py` — điền ô gộp, bỏ dòng tổng, gộp theo mã |
| `test_loaders.py` | `loaders.py` — đọc PDF/DOCX/XLSX/HTML |
| `test_pipeline.py` | Pipeline chạy đủ bước (file rỗng, resume, lỗi file, trích xuất, embedder lỗi) |

Không cần Chroma/Neo4j thật - vector_store/graph_writer là fake.

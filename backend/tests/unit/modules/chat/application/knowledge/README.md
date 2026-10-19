# unit/modules/chat/application/knowledge/ — Test pipeline nạp tri thức

| File | Test cho |
|------|----------|
| `test_pipeline_units.py` | Các hàm con: chunking, cleaning, dedup… (pure function) |
| `test_pipeline_empty.py` | Pipeline với thư mục rỗng / không có file hợp lệ → report đúng |

Không cần Chroma/Neo4j thật — vector_store/graph_writer là fake.

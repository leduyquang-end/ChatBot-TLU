# chat/application/knowledge/ — Pipeline nạp tri thức (QT-02)

## Mục đích

Biến tài liệu thô (`data/source/`: md, docx, pdf…) thành: chunk trong **ChromaDB** + thực thể/quan hệ trong **Neo4j**.

Giống như **thủ thư** xử lý sách mới mua về:
1. Mở sách ra, đọc (load)
2. Loại bỏ phần thừa (clean)
3. Cắt thành từng đoạn nhỏ (chunk) để tra cứu sau cho nhanh
4. Ghi vào sổ mục lục (ChromaDB)
5. Trích xuất các khái niệm, mối liên hệ (entities, relations) và ghi vào bản đồ khái niệm (Neo4j)

## File và vai trò

| File | Việc làm |
|------|----------|
| `loaders.py` | Đọc file theo phần mở rộng → text thuần |
| `cleaning.py` | Làm sạch text (thừa khoảng trắng, ký tự xấu…) |
| `chunking.py` | Cắt text thành chunk ~`chunk_size` ký tự, overlap `chunk_overlap` |
| `table_processing.py` | Xử lý bảng trong tài liệu |
| `dedup.py` | Gộp entity trùng (theo `dedup_threshold`) |
| `pipeline.py` | **`KnowledgeIngestPipeline`** — điều phối tất cả + `IngestReport` |

## Luồng `pipeline.run(source_dir)`

```
duyệt mọi file trong source_dir
   → load_document()
   → clean + chunk (nhiều chunk / file)
   → embed → vector_store.add(chunks)          → Chroma
   → LLM trích JSON {entities, relations}      (8 loại: MonHoc, NganhHoc, HocPhi…)
   → merge_entities (dedup)
   → graph_writer.write(entities, relations)   → Neo4j
   → IngestReport {documents_ok, failed, chunk_count, entity_count, ...}
```

## Chạy

```bash
python scripts/ingest_tlu.py [thư mục]   # từ backend/, mặc định <repo>/data/source
```

## Khi code theo

**Thêm định dạng file mới:** xử lý trong `loaders.py`.

**Thay cách chunk:** `chunking.py` (giữ nguyên interface với pipeline).

Logic ở đây phần lớn là **pure function** → test được không cần DB (xem `tests/.../knowledge/`).

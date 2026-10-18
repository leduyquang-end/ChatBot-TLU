# chat/application/ — Logic nghiệp vụ của chat

## File chính

### `chat_pipeline.py` — `ChatPipeline` (đọc kỹ nhất)

Đây là "bếp trưởng" điều phối toàn luồng hỏi đáp. Constructor nhận 5 port + settings (kỹ thuật gọi là **Dependency Injection** — "bếp trưởng" không tự đi lấy kho nguyên liệu, mà được "giao" sẵn khi tạo):

| Port | Việc làm |
|------|----------|
| `router` | Gán mode tìm kiếm cho câu hỏi |
| `vector_retrieval` | Tìm chunk trong ChromaDB |
| `graph_retrieval` | Tìm node/edge trong Neo4j |
| `answer_generator` | Sinh text từ prompt |
| `conversation_store` | Lưu/đọc lịch sử hội thoại |

Hai method chính:

- `ask(user_id, conversation_id, question) -> dict` — luồng QT-01 (xem README cha)
- `history(user_id, conversation_id) -> list[dict]` — trả lịch sử (user khác → `[]`)

`_retrieve(question, mode)` — truy xuất theo mode:

| Mode | Gọi gì |
|------|--------|
| `None` | Không truy xuất (context rỗng) |
| `Vector` | vector only |
| `Graph` | graph only |
| `Hybrid` | cả hai, gộp chunks |

**Nguyên tắc:** pipeline chỉ biết port — không import Chroma/Groq/Qwen trực tiếp.

## Thư mục con

| Thư mục | Mục đích |
|---------|----------|
| `knowledge/` | Pipeline nạp tài liệu vào Chroma + Neo4j (QT-02) |
| `ports/` | Interface cho mọi hạ tầng mà chat cần |

## Khi code theo

**Thêm bước xử lý** (ví dụ re-rank): thêm method/port, gọi trong `ask()` — giữ `ask()` dễ đọc.

**Test:** truyền fake thỏa port (xem `tests/unit/.../test_chat_pipeline.py`).

# chat/ — Phòng trả lời câu hỏi (quan trọng nhất)

## Mục đích

Đây là "trái tim" của chatbot: nhận câu hỏi tiếng Việt của sinh viên → tìm trong tài liệu của trường → sinh trả lời. Không có tài liệu → nói rõ "không có thông tin", không bịa (theo ADR-09).

Giống như **thư viện viên** của trường: khi sinh viên hỏi, họ đi tìm sách/trong kho tài liệu. Tìm được thì đọc theo đúng tài liệu; không tìm được thì nói "tài liệu này thư viện chưa có, bạn hỏi phòng khác nhé" — **không** bịa ra để trả lời cho có.

## Kiến trúc 4 lớp

```
chat/
├── api/routes.py                 ← Quầy order (POST /chat/ask, GET /chat/history)
├── application/
│   ├── chat_pipeline.py          ← CHÍNH: bếp trưởng điều phối toàn luồng
│   ├── knowledge/                ← Bộ phận nạp tài liệu vào kho (QT-02)
│   └── ports/                    ← Hợp đồng: router, retrieval, answer…
├── domain/                       ← Thực đơn: prompt, Conversation, RetrievalMode…
└── infrastructure/               ← Kho nguyên liệu: Chroma, Neo4j, Groq, Qwen…
```

## Luồng hỏi đáp — "Hành trình một câu hỏi" (QT-01)

```
POST /chat/ask {question: "Học phí ngành CNTT năm 2025 bao nhiêu?"}
   │
   ├─ 1. verify_token → user_id            (chưa đăng nhập → 401)
   ├─ 2. sanitize_input(question)          (làm sạch câu hỏi)
   │
   ▼
ChatPipeline.ask()
   ├─ 3. Lấy/tạo Conversation (lịch sử hội thoại)
   ├─ 4. router.classify(question)         (AI phân loại: cần tìm ở đâu?)
   │        → Vector | Graph | Hybrid | None
   │        (Groq Llama-3.3; lỗi → mặc định Vector — ADR-08)
   ├─ 5. Truy xuất theo mode:
   │        Vector → tìm trong ChromaDB (kho vector)
   │        Graph  → tìm trong Neo4j (kho đồ thị)
   │        Hybrid → tìm cả hai, gộp kết quả
   ├─ 6. NoInfoPolicy: điểm tốt nhất < ngưỡng (0.15) hoặc rỗng
   │        → trả "Không có thông tin", KHÔNG gọi AI sinh trả lời (ADR-09)
   │      Ngược lại:
   │        build_prompt (5 phần) → Qwen sinh trả lời
   ├─ 7. Lưu turn vào Conversation
   └─ 8. Trả {answer, mode, conversation_id, sources[]}
```

## Bộ phận lớn

| Đường dẫn | Vai trò |
|-----------|---------|
| `application/chat_pipeline.py` | Điều phối — **đọc đầu tiên** |
| `application/ports/` | 4 hợp đồng: Router, Retrieval (vector/graph), AnswerGenerator, ConversationStore |
| `application/knowledge/` | Nạp tài liệu: load → clean → chunk → dedup → nạp Chroma/Neo4j |
| `domain/prompt.py` | Prompt 5 phần + `NO_INFO_MESSAGE` |
| `domain/retrieval_mode.py` | Enum 4 mode + parse an toàn (sai → Vector) |
| `domain/no_info.py` | Quy tắc "không có thông tin" |
| `domain/conversation.py` | Lịch sử hội thoại |
| `infrastructure/` | Chroma, Neo4j, Groq, Qwen, embedder, conversation store |

## Khi code theo

**Sửa luồng hỏi:** `chat_pipeline.py`.

**Đổi AI/vector DB:** viết class mới cài port trong `infrastructure/`, ghép trong `api/routes.py` (`_build_pipeline()`) — không đụng pipeline.

**Thêm mode mới:** thêm value vào `RetrievalMode` + nhánh trong `_retrieve()`.

**Test:** fake các port (xem `tests/unit/modules/chat/application/test_chat_pipeline.py`).

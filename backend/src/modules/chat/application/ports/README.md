# chat/application/ports/ — Hợp đồng (interface) của chat

Mỗi file = 1 contract; infrastructure cài, application chỉ gọi.

| File | Interface | Method |
|------|-----------|--------|
| `router.py` | `RouterPort` | `classify(question) -> RetrievalMode` — luôn trả mode hợp lệ; lỗi → để fallback ở implementation (Vector) |
| `retrieval.py` | `VectorRetrievalPort` | `retrieve(question, fetch_k, top_k) -> RetrievedContext` |
| | `GraphRetrievalPort` | `retrieve(question, alpha, fetch_k) -> RetrievedContext` |
| `answer_generator.py` | `AnswerGeneratorPort` | `generate(prompt) -> str` |
| | `EmbedderPort` | `embed(texts) -> list[list[float]]` |
| `conversation_store.py` | `ConversationStorePort` | `get_or_create`, `save` |

## Khi code theo

Cần hạ tầng mới? **Tạo port trước** (file mới hoặc thêm method), viết implementation trong `infrastructure/`, ghép trong `api/routes.py`.

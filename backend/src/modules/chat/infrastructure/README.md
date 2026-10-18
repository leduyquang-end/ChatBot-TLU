# chat/infrastructure/ — Cắm hạ tầng thật cho chat

Mỗi file cài 1 port từ `application/ports/`. Thay thế = viết class mới, không sửa application.

## Bảng file

| File | Cài port | Việc làm |
|------|----------|----------|
| `hf_embedder.py` | `EmbedderPort` | Sentence-Transformers `bkai-foundation-models/vietnamese-bi-encoder` (768 chiều) |
| `chroma_retrieval.py` | `VectorRetrievalPort` | Embed câu hỏi → truy vấn collection `tlu_chunks` → `RetrievedContext`; cũng có method ghi chunk (dùng khi ingest) |
| `neo4j_graph_retrieval.py` | `GraphRetrievalPort` | Truy vấn graph (alpha fusion); **`Neo4jGraphWriter`** — ghi entity/relation khi ingest |
| `groq_router_client.py` | `RouterPort` | Gọi Groq Llama-3.3-70B phân loại mode; **bắt mọi lỗi → Vector** (ADR-08), parse label lạ → Vector |
| `qwen_answer_client.py` | `AnswerGeneratorPort` | Gọi Qwen3-235B (DashScope compatible API) sinh trả lời |
| `memory_conversation_store.py` | `ConversationStorePort` | `dict` trong RAM (singleton `_conversation_store` ở api) |

## Quy tắc chung

- Nhận `Settings` trong constructor — không đọc env trực tiếp
- Timeout/retry theo `request_timeout_seconds`, `max_retries`
- LLM/DB lỗi → ném `ExternalServiceError` (503) hoặc fallback theo ADR

## Khi code theo

1. Viết class mới cài port (method đúng tên/ký hiệu)
2. Ghép vào `_build_pipeline()` trong `api/routes.py`
3. Test riêng với mock HTTP — không đụng `chat_pipeline.py`

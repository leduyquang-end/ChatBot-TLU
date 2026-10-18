# chat/api/ — Quầy order của chat

## File chính

### `routes.py` — Blueprint `chat`, prefix `/chat`

| Endpoint | Method | Việc làm |
|----------|--------|----------|
| `/chat/ask` | POST | Hỏi đáp — body `{question, conversation_id?}` |
| `/chat/history` | GET | Lịch sử theo `?conversation_id=...` |

## Việc làm chính

1. `_require_user()` — bắt header `Authorization: Bearer …`, gọi `verify_token()` → user_id (sai token → 401)
2. Validate câu hỏi: rỗng / dài quá `question_max_length` → ném `ValidationError`
3. `_build_pipeline()` — **nơi ghép các concrete class** (đây là Composition Root — nơi duy nhất biết "bếp trưởng" dùng kho nguyên liệu nào):

```python
ChatPipeline(
    router=GroqRouterClient(settings),
    vector_retrieval=ChromaVectorRetrieval(settings, embedder),
    graph_retrieval=Neo4jGraphRetrieval(...),
    answer_generator=QwenAnswerClient(settings),
    conversation_store=InMemoryConversationStore(),
    settings=settings,
)
```

4. Gọi `pipeline.ask(...)` / `pipeline.history(...)`, trả JSON

## Khi code theo

Endpoint mới: thêm route, tái sử `_require_user()`; mọi logic nghiệp vụ để trong `application/`.

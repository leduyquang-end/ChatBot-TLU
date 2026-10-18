# chat/domain/ — Mô hình thuần của chat

Đây là "thực đơn" — chỉ chứa thông tin và quy tắc thuần Python, **không** phụ thuộc Flask, Chroma, hay LLM nào.

## File

| File | Nội dung |
|------|----------|
| `prompt.py` | `build_prompt()` — prompt **5 phần** (Vai trò / Quy tắc / Lịch sử / Tài liệu / Câu hỏi); `NO_INFO_MESSAGE`; format context + citation |
| `retrieval_mode.py` | Enum `RetrievalMode` = Vector \| Graph \| Hybrid \| None; `from_label()` — label lạ → **Vector** (ADR-08) |
| `no_info.py` | `NoInfoPolicy` — rỗng hoặc `best_score() < threshold` → False (ADR-09/10) |
| `retrieval_result.py` | `RetrievedChunk`, `RetrievedContext`, `GraphContext` — kết quả truy xuất; có `is_empty()`, `best_score()`, `citation()` |
| `conversation.py` | `Conversation` — `add_turn()`, `history(max_turns)` (giữ N lượt cuối) |

## Quy tắc

- Chỉ import từ Python stdlib + domain cùng module — **không** Flask/Chroma/LLM
- Prompt phải giữ đúng 5 phần; sửa prompt → sửa `prompt.py`, chạy test `test_prompt.py`

## Khi code theo

Thêm khái niệm mới (ví dụ Source): dataclass trong `retrieval_result.py` hoặc file mới, rồi dùng ở application.

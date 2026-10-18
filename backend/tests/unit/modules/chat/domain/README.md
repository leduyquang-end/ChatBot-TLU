# unit/modules/chat/domain/ — Test thuần domain

| File | Test cho |
|------|----------|
| `test_prompt.py` | `build_prompt()` đủ 5 phần; `NO_INFO_MESSAGE` có nội dung từ chối |
| `test_retrieval_mode.py` | `RetrievalMode.from_label()` — label đúng/sai (sai → Vector, ADR-08) |
| `test_no_info.py` | `NoInfoPolicy` — rỗng/điểm thấp → False; điểm ≥ ngưỡng → True |

Chạy: `python -m pytest tests/unit/modules/chat/domain -q`

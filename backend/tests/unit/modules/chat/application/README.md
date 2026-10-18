# unit/modules/chat/application/ — Test ChatPipeline

## File chính

### `test_chat_pipeline.py` — test luồng hỏi đáp bằng **fake port**

Không gọi AI/Chroma thật — dùng fake (giả lập):

- `make_settings()` — Settings với giá trị test
- `FakeRouter` / `FakeVector` / `FakeGraph` / `FakeAnswer` — cài port, trả kết quả dựng sẵn

Các case chính:

- Trả lời bình thường (context có điểm cao) → `FakeAnswer` sinh text
- Context rỗng / điểm thấp → trả `NO_INFO_MESSAGE`, **không** gọi answer generator (ADR-09)
- Mode `None` → không truy xuất
- Lưu turn vào conversation

## Mẫu để viết test mới

```python
class FakeXxx:  # cài port liên quan
    def method(...): return ket_qua_dung

def test_moi_truong_mo_ta_ket_qua():
    pipeline = ChatPipeline(router=FakeRouter(...), ...)
    ket_qua = pipeline.ask(...)
    assert ...
```

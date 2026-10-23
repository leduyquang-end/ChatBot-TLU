# events/ — Nơi xử lý sự kiện nội bộ

## Mục đích

Khi có gì đó xảy ra, chương trình "bắn tin" cho các bộ phận khác biết để xử lý (ví dụ: ghi log đăng nhập, thông báo khi nạp tri thức xong) — **không gọi chéo trực tiếp giữa các module**.

## File chính

### `bus.py` — `EventBus`

| Hàm | Việc làm |
|-----|----------|
| `subscribe(EventType, handler)` | Đăng ký nghe sự kiện theo đúng loại (đăng ký trùng bị bỏ qua) |
| `publish(event)` | Gửi sự kiện đến mọi handler của đúng loại; trả về số handler đã gọi |
| `unsubscribe(EventType, handler)` | Bỏ đăng ký (gọi lặp lại không lỗi) |
| `get_event_bus()` | Bus dùng chung toàn ứng dụng (singleton, thread-safe) |

- Handler lỗi bị bắt riêng → ghi `event=events.handler_failed`, không làm hỏng handler khác hay người bắn.
- Thread-safe: pub/sub từ nhiều request cùng lúc an toàn.

### `types.py` — sự kiện dùng chung (frozen dataclass)

| Sự kiện | Khi nào bắn |
|---------|-------------|
| `UserLoggedIn(user_id, role)` | Đăng nhập thành công |
| `UserPasswordChanged(user_id)` | Đổi mật khẩu thành công |
| `KnowledgeIngested(chunks, entities, relations, duration_seconds)` | Nạp tri thức xong (chỉ số liệu, không kèm nội dung tài liệu) |

Ví dụ:

```python
from src.shared.events import UserLoggedIn, get_event_bus

get_event_bus().subscribe(UserLoggedIn, lambda e: logger.info("event=audit.login user=%s", e.user_id))
get_event_bus().publish(UserLoggedIn(user_id="u-001", role="student"))
```

## Nơi bắn / nơi nghe

| Sự kiện | Bắn ở đâu | Nghe ở đâu |
|---------|-----------|------------|
| `UserLoggedIn` | `auth/application/login.py` (đăng nhập thành công) | `platform/logging/audit.py` |
| `UserPasswordChanged` | `user/application/change_password.py` (đổi mật khẩu thành công) | `platform/logging/audit.py` |
| `KnowledgeIngested` | `chat/application/knowledge/pipeline.py` (cuối `run()`) | `platform/logging/audit.py` |

`register_audit_handlers(bus)` được gọi ở composition root: `src/main.py` (web) và
`scripts/ingest_tlu.py` (nạp tri thức) — gọi lặp lại an toàn vì `subscribe` bỏ qua handler trùng.

## Trạng thái

Đã nối: auth, user (đổi mật khẩu) và knowledge bắn sự kiện; audit ghi log
(`audit.user.logged_in`, `audit.user.password_changed`, `audit.knowledge.ingested`) —
chỉ kèm id/số liệu, không kèm nội dung tài liệu hay mật khẩu.

# user/application/ports/ — "Hợp đồng" repository user

`user_repository.py` — `UserRepository(Protocol)`:

```python
def find_by_id(self, user_id: str) -> User | None: ...
```

Mọi implementation (in-memory, SQL…) phải có method này. Application chỉ gọi qua port — không biết dữ liệu nằm ở đâu.

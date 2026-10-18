# unit/ — Test thuần (chạy offline)

Test thuần — chạy offline, không cần dịch vụ gì. Hiện có **21 test**.

```bash
python -m pytest tests/unit -q
```

| Thư mục con | Test cho |
|-------------|----------|
| `modules/` | Test các module (hiện có: `chat`) |
| `shared/` | Test config + hệ thống lỗi |

Thêm test mới: tạo file `test_*.py` gương đúng đường dẫn với file trong `src/`.

# config/ — "Sổ tay cấu hình" của chương trình

## Mục đích

Chương trình cần biết rất nhiều thứ: mã khóa API để gọi AI, địa chỉ máy chủ ChromaDB, mật khẩu Neo4j… Thay vì viết cứng các giá trị này vào code (nguy hiểm nếu ai đó đọc được source), ta lưu chúng trong file `.env` và đọc ra khi chương trình chạy.

Giống như sổ điện thoại để ở quầy lễ tân: khi cần gọi ai, mở ra xem số — không cần nhớ.

## File chính

### `settings.py`

Ba việc chính:

1. **`Settings`** — một "hộp chứa" tất cả cấu hình, mỗi ô là một giá trị (địa chỉ, mã khóa, số nguyên…)
2. **`Settings.from_env()`** — đọc biến môi trường từ file `.env` và điền vào "hộp". Thiếu biến bắt buộc → ném `ConfigError` ngay (chương trình dừng, báo rõ thiếu gì)
3. **`get_settings()`** — trả về "hộp" đã điền, có **ghi nhớ** (cache) — đọc `.env` một lần, dùng nhiều lần

## Các biến quan trọng

| Biến | Bắt buộc? | Ý nghĩa |
|------|-----------|---------|
| `GROQ_API_KEY` | Có | Mã khóa gọi Groq (AI phân loại câu hỏi) |
| `QWEN_API_KEY` | Có | Mã khóa gọi Qwen (AI sinh trả lời) |
| `HF_TOKEN` | Có | Mã khóa tải model nhúng (biến câu hỏi thành số) |
| `CHROMA_URL` | Có | Địa chỉ ChromaDB (kho vector) |
| `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | Có | Thông tin kết nối Neo4j (kho đồ thị) |
| `APP_PORT` | Không | Cổng chạy server (mặc định 8000) |
| `LOG_LEVEL` | Không | Mức độ chi tiết log (mặc định INFO) |

**Khi code theo:** Không đọc `os.environ` trực tiếp ở nơi khác — luôn dùng `get_settings()` để đảm bảo mọi giá trị đều qua một cửa sổ kiểm tra.

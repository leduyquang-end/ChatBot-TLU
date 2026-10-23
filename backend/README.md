# Backend là gì? (backend/)

**Backend** là "phần não" phía server của chatbot. Khi sinh viên gõ câu hỏi trên trang web, backend là nơi nhận câu hỏi, tìm trong kho tài liệu của trường, rồi trả lời lại.

Hãy tưởng tượng backend như **quầy tiếp thị của một trường đại học**:
- Sinh viên bước đến (gửi câu hỏi)
- Nhân viên quầy (backend) đi tìm sổ sách/tài liệu
- Trả lời đúng theo tài liệu, hoặc nói "tôi không có thông tin này, bạn hỏi chỗ khác"

## Cách chạy chương trình

```bash
cd backend
pip install -r requirements.txt          # cài thư viện cần thiết
python -m src.main                       # chạy server theo APP_PORT (mặc định 8000)
```

Chạy kiểm thử (test — kiểm tra code có hoạt động đúng không):

```bash
python -m pytest tests/unit -q
```

## Thư mục con là gì?

| Thư mục | Giải thích đơn giản |
|---------|----------------------|
| `src/` | Toàn bộ "bộ não" — nơi viết code chính |
| `scripts/` | Các lệnh chạy tay (ví dụ: nạp tài liệu vào kho) |
| `tests/` | Nơi "kiểm tra" code có hỏng không |

## Nên đọc code theo thứ tự nào?

1. `src/main.py` — điểm bắt đầu, như cánh cửa chính vào tòa nhà
2. `src/modules/` — các "phòng ban" (đăng nhập, chat, người dùng)
3. `src/platform/` + `src/shared/` — "hệ thống kỹ thuật" chung cho cả tòa nhà

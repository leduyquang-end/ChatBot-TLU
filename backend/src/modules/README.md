# modules/ — Các "phòng ban" của ứng dụng

Mỗi folder trong `modules/` là một **phòng ban** đảm nhận một nhóm chức năng riêng:

- `auth/` — phòng đăng nhập (kiểm tra tài khoản, cấp quyền ra vào)
- `user/` — phòng quản lý thông tin cá nhân sinh viên
- `chat/` — phòng trả lời câu hỏi (phòng lớn nhất, quan trọng nhất)

## Kiến trúc 4 lớp — "Mỗi phòng ban có 4 bộ phận"

Để code dễ bảo trì, mỗi phòng ban chia thành **4 tầng**, giống như một nhà hàng:

```
api/            → Quầy order (nhận yêu cầu từ khách, trả kết quả)
application/    → Bếp trưởng (quyết định làm gì, gọi món gì)
domain/         → Thực đơn (thông tin thuần: tên món, giá, thành phần)
infrastructure/ → Kho nguyên liệu (nơi lấy dữ liệu thật: cơ sở dữ liệu, AI…)
```

**Quy tắc quan trọng:** Quầy order chỉ nói chuyện với Bếp trưởng. Bếp trưởng chỉ nói chuyện với Thực đơn và các "hợp đồng" (port). Kho nguyên liệu tự lo phần của nó, không ai được bước vào tùy tiện.

### Ví dụ minh họa

Khi bạn gọi món "Cà phê sữa" (đặt câu hỏi cho chatbot):
1. **Quầy order** (`api/`) ghi lại yêu cầu, kiểm tra bạn có phiếu (token) không
2. **Bếp trưởng** (`application/`) quyết định: cần tra sữa ở đâu, cà phê ở đâu
3. **Thực đơn** (`domain/`) nói: cà phê sữa gồm gì, giá bao nhiêu
4. **Kho nguyên liệu** (`infrastructure/`) đi lấy sữa từ tủ lạnh (ChromaDB), cà phê từ ngăn kéo (Neo4j)

Lợi ích: nếu ngày mai bạn đổi tủ lạnh mới (thay ChromaDB), chỉ cần đổi `infrastructure/` — bếp trưởng và quầy order **không cần biết**, không cần sửa.

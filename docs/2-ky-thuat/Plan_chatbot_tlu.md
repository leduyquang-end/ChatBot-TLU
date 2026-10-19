# Kế hoạch triển khai chatbot TLU

| Mục | Giá trị |
|-----|---------|
| Dự án | ChatBot (Trường Đại học Thủy Lợi) |
| Phiên bản | 1.0 - 2026-10-13 |
| Trạng thái | Nháp, chờ xác nhận các câu hỏi mở ở mục 10 |
| Đặc tả liên quan | `docs/2-ky-thuat/flows/QT1_hoi_dap_sinh_vien.md`, `docs/2-ky-thuat/flows/QT2_cap_nhat_tri_thuc.md` |

## 1. Mục tiêu

Xây dựng chatbot để sinh viên hỏi đáp bằng tiếng Việt về quy định, học phí, ngành học, học bổng và thủ tục của Trường Đại học Thủy Lợi. Câu trả lời chỉ dựa trên tài liệu của trường. Khi không có thông tin, chatbot nói rõ là không có và gợi ý liên hệ.

Kết quả cuối cùng gồm hai phần:

- Quy trình nạp và cập nhật tri thức (QT-02), chạy bởi quản trị viên dữ liệu.
- Quy trình hỏi đáp của sinh viên (QT-01), chạy trên giao diện web.

## 2. Phạm vi

**Trong phạm vi:**

- Nạp tài liệu từ trang web trường, file DOCX/PDF, bảng XLSX.
- Hai kho tri thức: kho tìm theo nội dung (ChromaDB) và kho thực thể và quan hệ (Neo4j).
- Bộ định tuyến chọn cách tìm, truy xuất, dựng prompt, sinh câu trả lời, lưu lịch sử hội thoại.
- Giao diện chat trên Flask.
- Kiểm thử và ghi nhật ký.

**Ngoài phạm vi (làm sau khi có xác nhận):**

- Chuyển câu hỏi sang nhân viên hỗ trợ (chưa có kênh, xem Q-04 trong QT-01).
- Lịch nạp tự động (GD-02 trong QT-02).
- Giao diện quản trị dữ liệu (Q-11 trong QT-02).
- Ứng dụng di động.

## 3. Nguyên tắc kiến trúc

Dự án là modulith, có các quy ước sau:

- Mỗi tính năng là một module trong `src/modules/`, chia 4 lớp `api`, `application`, `domain`, `infrastructure` (theo module `user`).
- Module không import trực tiếp lớp bên trong module khác. Giao tiếp qua một cổng công khai (port) do module đích định nghĩa.
- Client của hạ tầng bên ngoài (ChromaDB, Neo4j, Groq, Qwen API, Hugging Face) đặt ở `src/platform/`, hoặc trong `infrastructure` của module nếu chỉ module đó dùng.
- Cấu hình, khóa API và kiểu lỗi dùng chung đặt ở `src/shared/`.
- Lệnh chạy nạp dữ liệu thủ công đặt ở `scripts/`.
- Test đặt ở `tests/unit`, `tests/integration`, `tests/e2e`.

**Phân bổ đề xuất:**

| Thành phần | Vị trí |
|------------|--------|
| Route Flask cho chat và lịch sử | `src/modules/chat/api/` |
| Bộ định tuyến, truy xuất, dựng prompt, sinh câu trả lời | `src/modules/chat/application/` |
| Thực thể hội thoại, quy tắc chọn cách tìm | `src/modules/chat/domain/` |
| Client ChromaDB, Neo4j, LLM, embedding | `src/modules/chat/infrastructure/` hoặc `src/platform/` |
| Pipeline nạp tri thức (làm sạch, chia đoạn, trích thực thể, gộp trùng) | `src/modules/chat/application/knowledge/` (xem Q-03 mục 10) |
| Lệnh chạy nạp thủ công | `scripts/ingest_tlu.py` (hoặc tên tương đương) |
| Khóa API, đường dẫn kho | `src/shared/config/` |
| Logging | `src/platform/logging/` |

Ghi chú: module `chat` đã có trong cấu trúc, nhưng chưa rõ bên trong có code hay không. Cần xem trước khi bắt đầu Giai đoạn 1.

## 4. Các giai đoạn

Thứ tự là Giai đoạn 0 → 1 → 2 → 3 → 4 → 5. Giai đoạn 2 và 3 có thể làm song song sau khi Giai đoạn 1 xong.

### Giai đoạn 0: Chuẩn bị

**Việc cần làm:**

- Tạo `AGENTS.md` ở thư mục gốc, mô tả cấu trúc module, quy ước 4 lớp và lệnh chạy test.
- Tạo `README.md` ở thư mục gốc.
- Đọc `modules/chat/` hiện tại, ghi lại những gì đã có và chưa có.
- Đặt đặc tả QT-01 và QT-02 vào `docs/3-san-pham/flows/`.
- Trả lời các câu hỏi mở ưu tiên cao ở mục 10.
- Dựng môi trường: ChromaDB, Neo4j, và khóa API cho Groq, Qwen, Hugging Face.

**Hoàn thành khi:**

- `AGENTS.md` và `README.md` đã commit.
- Các dịch vụ ChromaDB và Neo4j chạy được trên máy phát triển.
- Có khóa API hợp lệ cho cả ba dịch vụ, lưu trong cấu hình, không nằm trong mã nguồn.

### Giai đoạn 1: Nền tảng dùng chung

**Việc cần làm:**

- Cấu hình: đọc khóa API, địa chỉ ChromaDB, Neo4j và các tham số (`chunk_size`, `overlap`, `fetch_k`, `top_k`, α) từ biến môi trường, đặt trong `src/shared/config/`.
- Kiểu lỗi dùng chung trong `src/shared/common/`: lỗi không có quyền, lỗi không tìm thấy, lỗi dịch vụ bên ngoài, lỗi định dạng.
- Client cho ChromaDB và Neo4j trong `src/platform/` hoặc `infrastructure`, có xử lý khi kết nối lỗi.
- Client cho Groq, Qwen API và Hugging Face trong `infrastructure`, có giới hạn thời gian chờ và thử lại.
- Logging có mức độ, không ghi nội dung câu hỏi nhạy cảm (xem mục 7).

**Hoàn thành khi:**

- Unit test cho cấu hình và các kiểu lỗi đều pass.
- Integration test kết nối được ChromaDB và Neo4j.
- Client LLM trả lỗi rõ ràng khi khóa sai hoặc hết hạn mức.

### Giai đoạn 2: Nạp tri thức (QT-02)

Đây là phần làm trước vì chatbot không có dữ liệu thì không trả lời được.

**2.1 Thu thập và làm sạch (A1, A2)**

- Đọc file DOCX, PDF, XLSX và trang web của trường.
- Loại khoảng trắng thừa, ký tự không có nghĩa, tiêu đề và chân trang lặp.
- Tách bảng XLSX thành file riêng.
- Xử lý file lỗi: bỏ qua và ghi tên vào báo cáo (E1 trong QT-02).

**2.2 Chia đoạn (A3)**

- Văn bản: chia theo điều khoản, dùng Recursive Character Chunking với `chunk_size = 800`, `overlap = 120`. Trước khi làm, phải xác định đơn vị là ký tự hay token (Q-12 trong QT-02).
- Bảng: gộp các dòng cùng mã định danh thành một khối. Điền ô gộp từ ô phía trên. Bỏ dòng tổng và chú thích.
- Mỗi đoạn có metadata: tên tài liệu, loại, tiêu đề mục (văn bản); tên sheet, tiêu đề cột (bảng).

**2.3 Nhánh vector (A4.1)**

- Nhúng mỗi đoạn bằng `bkai-foundation-models/vietnamese-bi-encoder`, 768 chiều.
- Lưu vào ChromaDB, không ghi trùng khi chạy lại.

**2.4 Nhánh đồ thị (A4.2)**

- Xác định loại thực thể: chạy Llama-3.3-70B một lần trên 500 câu hỏi để lấy danh từ hay gặp. Danh sách ban đầu: môn học, ngành học, học phí, học bổng, học kỳ, bộ môn, đối tượng, thủ tục.
- Trích thực thể và quan hệ bằng Qwen3-235B-A22B, với prompt tiếng Việt gồm vai trò, danh sách loại, quy tắc, định dạng đầu ra và ví dụ.
- Khử trùng lặp hai giai đoạn: theo tên chính xác, rồi theo cosine ≥ 0.92. Giữ thực thể có mô tả dài hơn. Chuyển quan hệ về thực thể được giữ. Bỏ cặp quan hệ trùng.
- Nạp vào Neo4j bằng Cypher MERGE. Chạy lại không tạo bản ghi trùng.

**2.5 Báo cáo**

- Sau mỗi đợt nạp: số tài liệu, số đoạn, số thực thể, số quan hệ, số lần gộp, số lỗi (GD-04 trong QT-02).

**Hoàn thành khi:**

- Unit test cho làm sạch, chia đoạn, gộp bảng, khử trùng lặp đều pass.
- Chạy `scripts/` trên tập tài liệu mẫu, kiểm tra AC-01 đến AC-05 của QT-02.
- Chạy lại cùng tài liệu không tạo bản ghi trùng.

### Giai đoạn 3: Trả lời sinh viên (QT-01, phần xử lý)

**3.1 Bộ định tuyến (B2)**

- Llama-3.3-70B qua Groq, prompt few-shot tiếng Việt, trả về JSON với một trong bốn nhãn: Vector, Đồ thị, Kết hợp, Không truy xuất.
- Đầu ra sai định dạng hoặc nhãn lạ: dùng Vector (E1 trong QT-01, BR-03).
- Test với bộ câu hỏi mẫu, gồm cả câu chào hỏi và câu ngoài phạm vi.

**3.2 Truy xuất (B3)**

- Vector: tìm cosine lấy 10 ứng viên (`fetch_k = 10`), chọn 5 đoạn bằng MMR (`top_k = 5`).
- Đồ thị: trích thực thể từ câu hỏi, tìm node theo từ khóa và theo ngữ nghĩa, điểm = α·semantic + (1−α)·keyword với α ∈ [0.6, 0.8], lấy cạnh vào và ra của node được chọn.
- Kết hợp: chạy cả hai, gộp ngữ cảnh.
- Không truy xuất: ngữ cảnh rỗng.

**3.3 Dựng prompt và sinh câu trả lời (B4, B5)**

- Prompt gồm vai trò, quy tắc (chỉ dựa trên tài liệu, không bịa, trả lời bằng tiếng Việt), câu hỏi, tri thức truy xuất được và lịch sử hội thoại.
- Qwen3-235B-A22B qua API.
- Nếu không có tri thức phù hợp: không gọi mô hình sinh câu trả lời, trả thông báo cố định kèm gợi ý liên hệ (E2, BR-02). Điều này tránh được việc mô hình tự bịa khi không có tài liệu.

**3.4 Lịch sử hội thoại (B6)**

- Lưu các lượt hỏi đáp theo cuộc trò chuyện. Thời hạn lưu và cách xóa chưa rõ (Q-07 trong QT-01), nên tạm lưu theo cấu hình có thể thay đổi.

**Hoàn thành khi:**

- Unit test cho từng bước pass. Test bộ định tuyến với bộ câu hỏi mẫu cho tỷ lệ chọn đúng ở mức chấp nhận được (ngưỡng do người yêu cầu xác định).
- Kiểm tra AC-01 đến AC-05 của QT-01 ở mức dịch vụ (chưa có giao diện).

### Giai đoạn 4: Giao diện và API

**Việc cần làm:**

- Route Flask trong `modules/chat/api/`: gửi câu hỏi, lấy lịch sử cuộc trò chuyện.
- Giao diện chat tối thiểu: ô nhập, nút gửi, hiển thị câu trả lời và lịch sử. Các thành phần cụ thể chờ xác nhận (Q-08 trong QT-01).
- Kiểm tra đăng nhập theo GD-01 của QT-01 (AC-05).

**Hoàn thành khi:**

- Integration test cho API pass.
- Sinh viên đăng nhập và hỏi được, hỏi tiếp được trong cùng cuộc trò chuyện.

### Giai đoạn 5: Kiểm thử chấp nhận và vận hành

**Việc cần làm:**

- E2E test theo AC-01 đến AC-05 của QT-01 và QT-02.
- Thử với bộ câu hỏi thực tế do người yêu cầu cung cấp (Q-08 trong QT-01).
- Kiểm tra log: không lưu thông tin cá nhân, không lưu khóa API.
- Cập nhật `README.md`, `AGENTS.md`, và mục 15 của QT-01, QT-02 với đường dẫn `path:line` đã kiểm chứng.

**Hoàn thành khi:**

- Tất cả AC của QT-01 và QT-02 đạt, hoặc có ghi chú lý do được người yêu cầu chấp nhận.
- Đặc tả QT-01 và QT-02 được cập nhật lên phiên bản mới nếu có thay đổi.

## 5. Lịch trình và người phụ trách

Chưa có mốc thời gian và người phụ trách. Các cột này cần điền khi có xác nhận.

| Giai đoạn | Người phụ trách | Bắt đầu | Kết thúc |
|-----------|-----------------|---------|----------|
| 0. Chuẩn bị | | | |
| 1. Nền tảng | | | |
| 2. Nạp tri thức | | | |
| 3. Trả lời | | | |
| 4. Giao diện | | | |
| 5. Kiểm thử và vận hành | | | |

## 6. Phụ thuộc

| Phụ thuộc | Ảnh hưởng nếu không sẵn sàng |
|-----------|-------------------------------|
| Tài liệu của trường | Không nạp được tri thức, chatbot không có gì để trả lời (Giai đoạn 2) |
| Khóa API Groq, Qwen, Hugging Face | Không chạy được bộ định tuyến, trích thực thể và sinh câu trả lời |
| Hạ tầng ChromaDB và Neo4j | Không lưu và truy xuất được tri thức |
| Bộ câu hỏi thực tế để nghiệm thu | Không đánh giá được chất lượng trả lời |

## 7. Rủi ro

| Rủi ro | Mức | Cách giảm thiểu |
|--------|-----|-----------------|
| `chunk_size = 800` có thể là token, vượt giới hạn 256 token của mô hình embedding, làm đoạn bị cắt | Cao | Xác định đơn vị trước Giai đoạn 2 (Q-12). Nếu là token, chọn lại kích thước phù hợp |
| Mô hình sinh câu trả lời bịa thông tin khi tài liệu không đủ | Cao | Quy tắc trong prompt, ngưỡng điểm truy xuất để quyết định có gọi mô hình hay không, kiểm thử với câu hỏi ngoài phạm vi |
| Trích thực thể sai hoặc không ổn định | Trung bình | Kiểm tra mẫu thủ công sau mỗi đợt nạp, ghi đầu ra thô để so sánh |
| Khử trùng lặp gộp nhầm hai thực thể khác nhau | Trung bình | Ngưỡng 0.92 cần kiểm chứng trên dữ liệu thực, ghi nhật ký các lần gộp |
| Hết hạn mức hoặc độ trễ của Groq và Qwen API | Trung bình | Thử lại có giới hạn, thông báo lỗi rõ cho người dùng (Q-04 trong QT-01) |
| Lộ khóa API | Cao | Chỉ đọc từ biến môi trường, không đưa vào mã nguồn hay log |
| Chi phí API tăng khi có nhiều người dùng | Trung bình | Chưa có ước lượng. Cần đo sau Giai đoạn 3 |
| Dữ liệu cá nhân trong câu hỏi bị lưu trong log | Trung bình | Không ghi nội dung câu hỏi vào log mức thông tin, chờ xác nhận Q-06 |

## 8. Nghiệm thu tổng thể

Dự án được coi là hoàn thành khi:

- Tất cả tiêu chí AC của QT-01 và QT-02 đạt, hoặc có lý do được người yêu cầu chấp nhận.
- Có tài liệu hướng dẫn chạy nạp thủ công và chạy ứng dụng, trong `README.md`.
- Có `AGENTS.md` để người và AI khác làm việc đúng quy ước.
- Các câu hỏi mở ưu tiên cao ở mục 10 đã có câu trả lời.

## 9. Việc cần làm ngay

1. Trả lời Q-01, Q-07 và Q-09 trong QT-01 và QT-02 (người yêu cầu, phân quyền, đăng nhập sinh viên).
2. Xác định `chunk_size` là ký tự hay token (Q-12 trong QT-02).
3. Xem bên trong `src/modules/chat/` để biết đã có code gì.
4. Tạo `AGENTS.md` và `README.md`.
5. Lấy khóa API cho Groq, Qwen, Hugging Face.

## 10. Câu hỏi mở cần trả lời

| Mã | Nội dung | Ảnh hưởng | Cần ai trả lời |
|----|----------|-----------|----------------|
| P-01 | Plan này dùng để triển khai kỹ thuật hay trình bày lộ trình? | Mức chi tiết mục 4 và 5 | Người yêu cầu |
| P-02 | Có mốc thời gian mục tiêu không? | Mục 5 | Người yêu cầu |
| P-03 | Pipeline nạp tri thức nằm trong `chat` hay tách thành module `knowledge`? | Vị trí mã ở mục 3 và Giai đoạn 2 | Người yêu cầu và đội kỹ thuật |
| P-04 | Có ai khác ngoài người yêu cầu cùng phát triển không? | Mục 5 | Người yêu cầu |
| P-05 | Ngưỡng chấp nhận cho bộ định tuyến và chất lượng câu trả lời là bao nhiêu? | Tiêu chí hoàn thành Giai đoạn 3 và 5 | Người yêu cầu |
| P-06 | Có môi trường staging hay chỉ chạy trên máy phát triển? | Giai đoạn 0 và 5 | Đội kỹ thuật |

## Lịch sử thay đổi

| Phiên bản | Ngày | Thay đổi |
|-----------|------|----------|
| 1.0 | 2026-10-13 | Tạo mới từ đặc tả QT-01 và QT-02 (v1.1) và cấu trúc dự án |
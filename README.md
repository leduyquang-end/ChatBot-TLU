# ChatBot TLU

Chatbot hỏi đáp bằng tiếng Việt cho sinh viên Trường Đại học Thủy Lợi. Chatbot trả lời dựa trên tài liệu của trường. Khi tài liệu không có thông tin, chatbot nói rõ là không có và gợi ý liên hệ, không tự trả lời theo kiến thức chung.

> **Trạng thái:** đang triển khai. Xem [kế hoạch triển khai](docs/2-ky-thuat/ke-hoach-chatbot-tlu.md) và [kiến trúc](docs/2-ky-thuat/kien-truc-chatbot-tlu.md).

---

## Mục lục

1. [Mục tiêu và phạm vi](#1-mục-tiêu-và-phạm-vi)
2. [Đối tượng sử dụng](#2-đối-tượng-sử-dụng)
3. [Cách hệ thống hoạt động](#3-cách-hệ-thống-hoạt-động)
4. [Dữ liệu và kho tri thức](#4-dữ-liệu-và-kho-tri-thức)
5. [Cấu trúc thư mục](#5-cấu-trúc-thư-mục)
6. [Yêu cầu hệ thống](#6-yêu-cầu-hệ-thống)
7. [Cấu hình](#7-cấu-hình)
8. [Cài đặt](#8-cài-đặt)
9. [Nạp tri thức](#9-nạp-tri-thức)
10. [Chạy ứng dụng](#10-chạy-ứng-dụng)
11. [Kiểm thử](#11-kiểm-thử)
12. [Quy ước phát triển](#12-quy-ước-phát-triển)
13. [Bảo mật và quyền riêng tư](#13-bảo-mật-và-quyền-riêng-tư)
14. [Giới hạn đã biết](#14-giới-hạn-đã-biết)
15. [Câu hỏi thường gặp](#15-câu-hỏi-thường-gặp)
16. [Tài liệu liên quan](#16-tài-liệu-liên-quan)
17. [Liên hệ](#17-liên-hệ)

---

## 1. Mục tiêu và phạm vi

Mục tiêu: giúp sinh viên tra cứu nhanh các quy định, học phí, ngành học, học bổng và thủ tục của trường bằng cách hỏi tự nhiên.

**Trong phạm vi hiện tại:**

- Nạp tài liệu của trường từ trang web, file DOCX, PDF và bảng XLSX.
- Hai kho tri thức: một kho tìm theo nội dung và một kho thực thể với quan hệ giữa chúng.
- Trả lời câu hỏi tiếng Việt, có nhớ ngữ cảnh trong cùng cuộc trò chuyện.
- Ứng dụng web hỏi đáp độc lập cho sinh viên; giao diện tĩnh được Nginx phục vụ riêng và gọi Flask API qua `/api`.
- Ghi nhật ký các sự kiện chính.

**Ngoài phạm vi hiện tại:**

- Chuyển câu hỏi cho nhân viên hỗ trợ. Chưa có kênh chuyển tiếp (xem Q-04 trong QT-01).
- Nạp tri thức tự động theo lịch. Hiện chạy thủ công theo đợt (GD-02 trong QT-02).
- Giao diện quản trị dữ liệu. Hiện chạy bằng lệnh (Q-11 trong QT-02).
- Ứng dụng di động.

---

## 2. Đối tượng sử dụng

| Vai trò | Làm gì với hệ thống |
|---------|---------------------|
| **Sinh viên** | Đặt câu hỏi trên giao diện chat, đọc câu trả lời, hỏi tiếp trong cùng cuộc trò chuyện |
| **Quản trị viên dữ liệu** | Đưa tài liệu nguồn vào, chạy quy trình nạp tri thức, xem báo cáo sau mỗi đợt nạp |
| **Cán bộ phòng ban** | Vai trò chưa rõ trong quy trình (Q-03 trong QT-02). Có thể là nguồn tài liệu |
| **Lập trình viên** | Phát triển và bảo trì hệ thống. Đọc `AGENTS.md` và tài liệu kỹ thuật trước khi sửa mã |

---

## 3. Cách hệ thống hoạt động

Hệ thống có hai luồng độc lập, gặp nhau ở hai kho tri thức.

```
  Luồng nạp (offline, theo đợt)           Luồng hỏi đáp (online, mỗi câu hỏi)
  ─────────────────────────────           ───────────────────────────────────
  Tài liệu nguồn                          Sinh viên gửi câu hỏi
        ↓                                        ↓
  Làm sạch                                Bộ chọn cách tìm
        ↓                                        ↓
  Chia đoạn                               Truy xuất ──────┐
        ↓                                        ↓        │
  ┌─────┴──────┐                          Dựng prompt      │
  ↓            ↓                                ↓          │
  Nhúng vector  Trích thực thể             Sinh câu trả lời │
  ↓            ↓                                ↓          │
  Kho nội dung  Gộp trùng                  Hiển thị      ←──┘
                ↓                                             
                Kho thực thể và quan hệ  ──────────────────────┘
```

### 3.1 Luồng nạp tri thức (offline)

Được thực hiện bởi quản trị viên dữ liệu. Mỗi đợt nạp gồm các bước sau.

**Bước 1. Thu thập và làm sạch.**

- Đọc tài liệu từ trang web của trường, file DOCX, PDF, và bảng XLSX.
- Bỏ khoảng trắng thừa, ký tự không mang nghĩa, tiêu đề và chân trang lặp lại.
- Tách các bảng XLSX thành file riêng để xử lý theo cách khác.
- File không đọc được: bỏ qua, ghi tên file vào báo cáo.

**Bước 2. Chia đoạn.**

- **Văn bản (DOCX, PDF):** chia theo điều khoản, dùng Recursive Character Chunking. Tham số hiện tại: kích thước 800, chồng lấn 120. Đơn vị (ký tự hay token) chưa xác định (Q-12 trong QT-02).
- **Bảng (XLSX):**
  - Xóa dòng trống.
  - Điền ô trống do gộp ô bằng giá trị ở ô phía trên.
  - Bỏ dòng tổng cộng, tiêu đề nhóm, chú thích.
  - Gộp các dòng có cùng mã định danh thành một khối, để mỗi khối mô tả đủ một thực thể.
  - Mỗi sheet có nhóm khối riêng.
- Mỗi đoạn được gắn metadata:
  - Văn bản: tên tài liệu, loại tài liệu, tiêu đề chương hoặc mục.
  - Bảng: tên sheet, tiêu đề cột.

**Bước 3. Nhánh vector.**

- Nhúng mỗi đoạn thành vector 768 chiều bằng `bkai-foundation-models/vietnamese-bi-encoder`, qua Hugging Face.
- Mô hình này giới hạn 256 token mỗi đầu vào.
- Lưu vector và metadata vào ChromaDB.

**Bước 4. Nhánh đồ thị.**

- **4.1. Xác định loại thực thể.** Dùng Llama-3.3-70B trên 500 câu hỏi thường gặp của sinh viên để tìm các danh từ hay xuất hiện. Danh sách ban đầu: môn học, ngành học, học phí, học bổng, học kỳ, bộ môn, đối tượng, thủ tục. Bước này chạy một lần, không lặp lại mỗi đợt nạp (GD-03 trong QT-02).
- **4.2. Trích thực thể và quan hệ.** Gửi đoạn cho Qwen3-235B-A22B qua API cùng prompt tiếng Việt gồm: vai trò, danh sách loại thực thể, quy tắc xác định, định dạng đầu ra, và ví dụ.
- **4.3. Khử trùng lặp, hai giai đoạn.**
  - Giai đoạn 1: gộp các thực thể có tên trùng nhau.
  - Giai đoạn 2: gộp các thực thể có độ tương đồng ngữ nghĩa cosine ≥ 0.92.
  - Khi gộp: giữ thực thể có mô tả dài hơn, chuyển toàn bộ quan hệ về thực thể được giữ, bỏ cặp quan hệ trùng (cùng nguồn và đích), giữ cặp có nhiều thông tin và độ tin cậy cao hơn.
- **4.4. Nạp vào Neo4j.** Dùng Cypher MERGE. Chạy lại trên cùng tài liệu không tạo bản trùng.

**Bước 5. Báo cáo.** Sau mỗi đợt nạp, hệ thống tổng hợp số tài liệu, đoạn, thực thể, quan hệ, số lần gộp trùng, và số lỗi. Kênh nhận báo cáo chưa xác định (Q-10 trong QT-02).

### 3.2 Luồng hỏi đáp (online)

Chạy mỗi khi sinh viên gửi câu hỏi.

**Bước 1. Tiếp nhận.** Giao diện Flask nhận câu hỏi và chuyển vào pipeline. Câu hỏi để trống hoặc chỉ có ký tự đặc biệt sẽ được yêu cầu nhập lại (GD-02 trong QT-01).

**Bước 2. Chọn cách tìm (router).**

- Dùng Llama-3.3-70B qua Groq với prompt few-shot tiếng Việt.
- Trả về JSON chứa một trong bốn nhãn:

| Nhãn | Khi nào dùng | Ví dụ loại câu hỏi |
|------|--------------|--------------------|
| **Vector** | Định nghĩa, quy định chi tiết | "Điều kiện xét học bổng là gì?" |
| **Đồ thị** | Quan hệ, điều kiện tiên quyết, liên kết giữa các mục | "Học phần nào phải học trước môn X?" |
| **Kết hợp** | Câu hỏi phức tạp, cần suy luận nhiều bước | "Sinh viên ngành X học lại môn nào thì được miễn học phí?" |
| **Không truy xuất** | Giao tiếp thông thường | "Xin chào" |

- Nếu đầu ra không đúng JSON hoặc nhãn không thuộc bốn nhãn trên: dùng nhánh **Vector**. Hệ thống luôn có câu trả lời.

**Bước 3. Truy xuất.**

- **Vector:**
  - Tìm theo cosine similarity, lấy 10 ứng viên (`fetch_k = 10`).
  - Chọn 5 đoạn bằng MMR (Maximal Marginal Relevance), cân bằng giữa mức liên quan và độ đa dạng (`top_k = 5`).
- **Đồ thị:**
  - Trích thực thể từ câu hỏi bằng Llama-3.3-70B.
  - Tìm node theo từ khóa: điểm = tổng số lần từ khóa xuất hiện trong tên hoặc mô tả của node.
  - Tìm node theo ngữ nghĩa: cosine giữa vector câu hỏi và vector của node (từ tên và mô tả).
  - Điểm tổng: `score(n) = α · semantic(n) + (1 − α) · keyword(n)`, với α ∈ [0.6, 0.8] để ưu tiên ngữ nghĩa.
  - Với mỗi node được chọn, lấy toàn bộ cạnh đi ra và đi vào, kèm mô tả quan hệ.
- **Kết hợp:** chạy cả Vector và Đồ thị, gộp ngữ cảnh từ hai nguồn.
- **Không truy xuất:** bỏ qua bước này, ngữ cảnh rỗng.

**Bước 4. Kiểm tra có thông tin hay không.**

- Nếu truy xuất không có kết quả phù hợp, không gọi mô hình sinh câu trả lời. Trả về thông báo cố định: chatbot chưa có thông tin, sinh viên nên liên hệ đơn vị phù hợp (Q-03 trong QT-01 chưa chốt tên đơn vị).
- Ngưỡng để quyết định "không có thông tin" chưa xác định (A-03 trong kiến trúc).

**Bước 5. Dựng prompt.** Prompt gồm: vai trò của mô hình, các quy tắc (chỉ dựa trên tài liệu, không bịa, trả lời bằng tiếng Việt), câu hỏi hiện tại, tri thức truy xuất được, và lịch sử hội thoại.

**Bước 6. Sinh câu trả lời.** Qwen3-235B-A22B qua API. Chọn mô hình này vì tài liệu nguồn dẫn benchmark tiếng Việt trong Qwen3 Technical Report, Bảng 33. Cần kiểm chứng lại trước khi cam kết (ADR-03 trong kiến trúc).

**Bước 7. Trả kết quả và lưu lịch sử.** Câu trả lời hiển thị trên giao diện. Lượt hỏi đáp được lưu vào lịch sử để dùng cho các câu hỏi tiếp theo. Nơi lưu và thời hạn lưu chưa xác định (Q-07 trong QT-01).

### 3.3 Xử lý lỗi

| Tình huống | Hệ thống làm gì | Người dùng thấy gì |
|------------|-----------------|--------------------|
| Router trả về sai định dạng | Dùng nhánh Vector | Không thấy lỗi, câu trả lời vẫn đến |
| Tài liệu không có thông tin phù hợp | Không gọi mô hình sinh câu trả lời | Thông báo chưa có thông tin, gợi ý liên hệ |
| Câu hỏi rỗng | Không tìm kiếm | Yêu cầu nhập lại |
| Dịch vụ LLM không phản hồi | Chưa rõ (Q-04 trong QT-01) | Chưa rõ |
| Kho dữ liệu không truy cập được | Chưa rõ (Q-04 trong QT-01) | Chưa rõ |
| File tài liệu không đọc được khi nạp | Bỏ qua file, ghi vào báo cáo | Thấy tên file trong báo cáo nạp |
| Ghi kho bị lỗi giữa chừng khi nạp | Chưa rõ (Q-06 trong QT-02) | Chưa rõ |

---

## 4. Dữ liệu và kho tri thức

### 4.1. Kho tìm theo nội dung (ChromaDB)

- Lưu các đoạn văn bản đã chia.
- Mỗi đoạn có vector 768 chiều và metadata.
- Metadata với văn bản: tên tài liệu, loại tài liệu, tiêu đề chương hoặc mục.
- Metadata với bảng: tên sheet, tiêu đề cột.

### 4.2. Kho thực thể và quan hệ (Neo4j)

- **Node:** thực thể có tên, mô tả, loại thực thể, và vector nhúng từ tên và mô tả.
- **Cạnh:** quan hệ có nguồn, đích, mô tả, và độ tin cậy.
- Loại thực thể ban đầu: MonHoc, NganhHoc, HocPhi, HocBong, HocKy, BoMon, DoiTuong, ThuTuc. Danh sách có thể mở rộng (Q-09 trong QT-02).
- Ghi bằng Cypher MERGE. Cập nhật gia tăng, không dựng lại toàn bộ đồ thị.

### 4.3. Lịch sử hội thoại

- Lưu theo cuộc trò chuyện để dùng cho câu hỏi tiếp theo.
- Nơi lưu, thời hạn, và cách xóa chưa xác định (A-02 trong kiến trúc).

---

## 5. Cấu trúc thư mục

```
ChatBot/
├── AGENT.md                Quy ước cho người và AI làm việc trên mã nguồn
├── README.md               File này
├── .env.example            Mẫu biến môi trường
├── docker-compose.yml      backend + frontend + ChromaDB + Neo4j
├── docs/                   Tài liệu dự án
│   ├── 1-tong-quan/
│   ├── 2-ky-thuat/
│   │   └── flows/
│   ├── 3-san-pham/
│   ├── 4-van-hanh/
│   ├── 5-mau/
│   ├── 6-design/
│   └── 7-ghi-chu/
├── backend/                Flask API + pipeline nạp tri thức
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── scripts/            Lệnh chạy thủ công (ingest_tlu.py)
│   ├── src/
│   │   ├── modules/        auth, chat, user
│   │   ├── platform/       logging, security
│   │   └── shared/         common, config, database, events
│   └── tests/              unit, integration, e2e
└── frontend/               Giao diện chat
    ├── Dockerfile          nginx
    ├── nginx.conf          tệp tĩnh + proxy /api/* → backend
    └── public/
        ├── index.html      cấu trúc màn hình
        ├── css/style.css   giao diện và responsive
        └── js/             app.js, api.js, store.js, ui.js, config.js
```

### 5.1. Quy ước trong `src/modules/`

Mỗi module chia 4 lớp:

| Lớp | Chứa gì | Ví dụ với module `chat` |
|-----|---------|------------------------|
| `api` | Route HTTP, kiểm tra đầu vào, định dạng đầu ra | Route gửi câu hỏi, lấy lịch sử |
| `application` | Điều phối các bước: router, truy xuất, dựng prompt, sinh câu trả lời | Bộ chọn cách tìm |
| `domain` | Khái niệm nghiệp vụ, quy tắc thuần túy | Bốn nhãn cách tìm, quy tắc "không có thông tin" |
| `infrastructure` | Kết nối dịch vụ bên ngoài | Client ChromaDB, Neo4j, Groq, Qwen |

Quy tắc giao tiếp:

- Module không import trực tiếp lớp bên trong module khác.
- Khi module cần dữ liệu từ module khác, dùng cổng công khai do module đích định nghĩa.
- Client dịch vụ dùng chung đặt trong `src/platform/`. Client chỉ một module dùng thì đặt trong `infrastructure` của module đó.

Vị trí pipeline nạp tri thức chưa chốt: trong `modules/chat/application/knowledge/` hoặc module `knowledge` riêng (P-03 trong kế hoạch).

### 5.2. Quy ước frontend

- `public/index.html`: cấu trúc HTML và các `id` mà controller sử dụng. Khi đổi `id`, cập nhật đồng thời `public/js/app.js`.
- `public/css/style.css`: màu sắc, bố cục, responsive và trạng thái focus; không đặt xử lý API tại đây.
- `public/js/app.js`: điều phối sự kiện và luồng màn hình; không gọi `fetch()` trực tiếp.
- `public/js/api.js`: toàn bộ giao tiếp HTTP, header xác thực, timeout và lỗi mạng.
- `public/js/store.js`: lưu trạng thái trình duyệt và chuẩn hóa response trước khi giao cho giao diện.
- `public/js/ui.js`: tạo thành phần DOM; nội dung từ người dùng/backend phải được hiển thị an toàn.
- `public/js/config.js`: một nơi khai báo endpoint, tên trường request/response, nhãn chế độ tìm, giới hạn và khóa lưu trữ.
- Giao diện hiện là ứng dụng web hỏi đáp độc lập theo bố cục hội thoại toàn trang: lịch sử bên trái trên desktop, ngăn kéo lịch sử trên thiết bị nhỏ và vùng chat chính ở trung tâm.
- Phạm vi hiện tại chỉ gồm phát triển và chạy website riêng; chưa triển khai nhúng vào website khác.
- Không đổi hợp đồng API khi tùy chỉnh giao diện. HTML và các module API tách biệt để có thể thay đổi thiết kế mà không sửa backend nếu request/response không đổi.

Hợp đồng backend hiện dùng:

| Luồng | Request | Response |
|-------|---------|----------|
| Đăng nhập | `POST /api/auth/login`: `username`, `password` | `token`, `user_id`, `role` |
| Xác minh phiên | `GET /api/user/me`: `Authorization: Bearer <token>` | `id`, `username`, `full_name`, `role` |
| Hỏi đáp | `POST /api/chat/ask`: `question`, `conversation_id` | `answer`, `mode`, `conversation_id`, `sources` |
| Lịch sử | `GET /api/chat/history?conversation_id=...` | `conversation_id`, `turns` gồm `role`, `content` |

Khi tải lại trang, frontend gọi `/api/user/me` để xác minh token và vai trò từ backend; chỉ tài khoản có vai trò `student` mới được vào giao diện hỏi đáp. Nếu backend đổi đường dẫn hoặc tên trường, trước tiên cập nhật `config.js` và hàm chuẩn hóa trong `store.js`; chỉ sửa controller hoặc HTML nếu cấu trúc dữ liệu mới làm thay đổi hành vi/màn hình. Giữ nguyên request/response backend khi chỉ thay đổi giao diện. Phục vụ `frontend/public/` qua HTTP thay vì mở HTML bằng `file://`, vì trang dùng JavaScript modules. `MOCK.ENABLED` chỉ dùng để thử giao diện độc lập; phản hồi mock phân loại một số chủ đề để kiểm tra luồng nhưng không phải dữ liệu chính thức và không có nguồn trích dẫn. Tắt mock khi kiểm tra API thật.

Kiểm tra vai trò trong frontend chỉ điều khiển giao diện, không thay thế phân quyền phía máy chủ. Hiện `/api/chat/ask` và `/api/chat/history` kiểm tra token nhưng chưa kiểm tra vai trò `student`; backend cần bổ sung kiểm tra này trước khi coi AC-05 của QT-01 được bảo đảm.

Lịch sử hội thoại phía backend hiện lưu trong RAM. Backend chạy một Gunicorn worker để các request trong cùng thời gian hoạt động nhìn thấy cùng lịch sử; lịch sử vẫn mất khi backend khởi động lại. Frontend chỉ lưu danh sách tên và mã cuộc trò chuyện trên trình duyệt, không lưu nội dung lịch sử.

---

## 6. Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|------------|---------|
| Ngôn ngữ và runtime | [Điền: phiên bản] |
| ChromaDB | Đang chạy, có địa chỉ truy cập |
| Neo4j | Đang chạy, có địa chỉ và tài khoản |
| Groq | Khóa API, còn hạn mức |
| Qwen API | Khóa API, còn hạn mức |
| Hugging Face | Token truy cập để tải `bkai-foundation-models/vietnamese-bi-encoder` |
| Hệ điều hành | [Điền] |
| Phần cứng | [Điền: nếu có GPU cho embedding hay không] |

---

## 7. Cấu hình

Mọi khóa API và địa chỉ dịch vụ đặt trong biến môi trường, không đưa vào mã nguồn hay commit lên repo.

### 7.1. Biến môi trường

| Biến | Bắt buộc | Mục đích |
|------|:--------:|----------|
| `GROQ_API_KEY` | Có | Khóa Groq cho router và trích thực thể từ câu hỏi |
| `QWEN_API_KEY` | Có | Khóa Qwen API cho trích thực thể khi nạp và sinh câu trả lời |
| `HF_TOKEN` | Có | Token Hugging Face để tải mô hình embedding |
| `CHROMA_URL` | Có | Địa chỉ ChromaDB |
| `NEO4J_URI` | Có | Địa chỉ Neo4j |
| `NEO4J_USER` | Có | Tài khoản Neo4j |
| `NEO4J_PASSWORD` | Có | Mật khẩu Neo4j |

[Điền: tên biến thực tế nếu khác với bảng trên.]

### 7.2. Tham số thuật toán

Các tham số này nên đặt trong cấu hình (`src/shared/config/`), không hard-code.

| Tham số | Giá trị đề xuất | Dùng ở đâu |
|---------|-----------------|------------|
| `chunk_size` | 800 (đơn vị chưa rõ, Q-12 trong QT-02) | Chia đoạn văn bản |
| `overlap` | 120 | Chia đoạn văn bản |
| `embedding_dim` | 768 | Vector |
| `embedding_max_tokens` | 256 | Giới hạn đầu vào của mô hình embedding |
| `fetch_k` | 10 | Số ứng viên trước khi chọn bằng MMR |
| `top_k` | 5 | Số đoạn đưa vào prompt |
| `alpha` | 0.6 đến 0.8 | Tỷ trọng ngữ nghĩa so với từ khóa khi chấm điểm đồ thị |
| `dedup_threshold` | 0.92 | Ngưỡng cosine để gộp thực thể trùng |
| `no_info_threshold` | Chưa xác định (A-03 trong kiến trúc) | Ngưỡng để trả lời "không có thông tin" |

---

## 8. Cài đặt

Các bước dưới đây cần bổ sung khi có mã nguồn.

```bash
# 1. Lấy mã nguồn
git clone [Điền: địa chỉ repo]
cd ChatBot

# 2. Tạo môi trường và cài phụ thuộc
[Điền: lệnh]

# 3. Tạo file cấu hình từ mẫu
[Điền: lệnh copy file mẫu, ví dụ .env.example]

# 4. Điền khóa API và địa chỉ dịch vụ vào file cấu hình
```

**Kiểm tra nhanh sau khi cài:**

- ChromaDB trả lời tại `CHROMA_URL`.
- Neo4j nhận kết nối tại `NEO4J_URI`.
- Groq và Qwen trả lời một yêu cầu đơn giản với khóa đã cấu hình.
- Tải được mô hình embedding từ Hugging Face.

---

## 9. Nạp tri thức

Chạy thủ công theo đợt, do quản trị viên dữ liệu thực hiện.

### 9.1. Chuẩn bị

1. Đặt tài liệu nguồn vào thư mục [Điền: thư mục đầu vào].
2. Kiểm tra các dịch vụ đang chạy (ChromaDB, Neo4j).
3. Kiểm tra khóa API còn hạn mức.

### 9.2. Chạy

```bash
# [Điền: lệnh chạy script trong scripts/]
```

### 9.3. Kết quả

Sau khi chạy xong, kiểm tra báo cáo:

- Số tài liệu đã nhận và số file bị lỗi.
- Số đoạn văn bản và số khối từ bảng.
- Số thực thể và quan hệ đã ghi vào Neo4j.
- Số lần gộp trùng lặp.

### 9.4. Chạy lại

Chạy lại trên cùng tài liệu không tạo bản trùng trong Neo4j nhờ MERGE. Với ChromaDB, [Điền: cách tránh trùng đoạn khi chạy lại].

---

## 10. Chạy ứng dụng

```bash
# [Điền: lệnh chạy Flask, cổng, địa chỉ truy cập]
```

Mở trình duyệt tại [Điền: địa chỉ], đăng nhập bằng tài khoản sinh viên, và gửi câu hỏi thử.

---

## 11. Kiểm thử

| Loại | Phạm vi | Yêu cầu |
|------|---------|---------|
| **Unit** | Làm sạch, chia đoạn, gộp bảng, khử trùng lặp, router, dựng prompt | Không cần dịch vụ ngoài |
| **Integration** | Kết nối ChromaDB, Neo4j, các client LLM | Cần dịch vụ thật đang chạy |
| **E2E** | Luồng hỏi đáp đầy đủ theo tiêu chí AC trong QT-01 và QT-02 | Cần cả hai kho có dữ liệu |

```bash
# Unit
[Điền: lệnh]

# Integration
[Điền: lệnh]

# E2E
[Điền: lệnh]
```

**Tiêu chí nghiệm thu** nằm trong mục 12 của hai file đặc tả:

- [QT-01](docs/2-ky-thuat/flows/QT-01-hoi-dap-sinh-vien.md): AC-01 đến AC-05.
- [QT-02](docs/2-ky-thuat/flows/QT-02-cap-nhat-tri-thuc-chatbot.md): AC-01 đến AC-05.

---

## 12. Quy ước phát triển

- Đọc `AGENTS.md` trước khi sửa mã. File này mô tả quy ước module, lớp, và lệnh kiểm thử.
- Đặt đặc tả quy trình mới trong `docs/2-ky-thuat/flows/`, đặt tên theo `QT-<nn>-<ten-ngan>.md`.
- Khi thay đổi đặc tả, tăng số phiên bản và thêm dòng vào mục "Lịch sử thay đổi". Không ghi đè bản cũ.
- Mọi thay đổi về kiến trúc cần cập nhật `kien-truc-chatbot-tlu.md`.
- Không đưa khóa API, mật khẩu, hay dữ liệu cá nhân vào mã nguồn hoặc commit.

[Điền: quy ước commit, nhánh, và review nếu có]

---

## 13. Bảo mật và quyền riêng tư

- **Khóa API:** chỉ đọc từ biến môi trường. Không ghi vào log.
- **Log:** không ghi nội dung câu hỏi ở mức thông tin. Quyết định cụ thể chờ xác nhận (Q-06 trong QT-01).
- **Phân quyền:**
  - Sinh viên chỉ hỏi đáp, không thấy dữ liệu nạp tri thức.
  - Chỉ quản trị viên dữ liệu được chạy quy trình nạp (GD-01 trong QT-02, Q-07 trong QT-02 chưa chốt cách kiểm tra).
  - Người chưa đăng nhập không được hỏi đáp (GD-01 trong QT-01, Q-09 trong QT-01 chưa chốt).
- **Dữ liệu gửi đi:** câu hỏi và đoạn tài liệu được gửi tới Groq và Qwen API. Cần người yêu cầu xác nhận việc này phù hợp với quy định của trường.

---

## 14. Giới hạn đã biết

- `chunk_size` có thể là token. Nếu vậy sẽ vượt giới hạn 256 token của mô hình embedding, làm đoạn bị cắt khi nhúng. Cần xác định trước khi nạp dữ liệu thật (Q-12 trong QT-02).
- Chưa có số liệu về độ trễ và chi phí API.
- Chất lượng router và câu trả lời chưa được đo bằng bộ câu hỏi chuẩn (P-05 trong kế hoạch).
- Mô hình ngôn ngữ dựa trên tài liệu nguồn. Thông tin cũ trong tài liệu sẽ được trả lời như cũ cho đến khi nạp lại.
- Chưa có kênh chuyển câu hỏi cho người thật.

---

## 15. Câu hỏi thường gặp

**Chatbot có trả lời được mọi câu hỏi không?**
Không. Chatbot chỉ trả lời dựa trên tài liệu đã nạp. Câu hỏi nằm ngoài tài liệu sẽ nhận thông báo không có thông tin.

**Tại sao chatbot không trả lời theo kiến thức chung?**
Đây là lựa chọn của người yêu cầu để tránh thông tin sai về quy định của trường (GD-03 trong QT-01).

**Tôi vừa cập nhật tài liệu trên trang web của trường, chatbot có biết không?**
Chưa. Cần chạy lại quy trình nạp tri thức. Hiện chưa có lịch tự động.

**Tại sao cùng một câu hỏi đôi khi có câu trả lời hơi khác nhau?**
Mô hình sinh câu trả lời có tính ngẫu nhiên. Cùng nội dung tài liệu nhưng cách diễn đạt có thể khác. [Điền: nếu đã cố định tham số sinh, ví dụ temperature.]

**Lịch sử hội thoại của tôi có được lưu không?**
Có, để dùng cho câu hỏi tiếp theo trong cùng cuộc trò chuyện. Thời hạn lưu và cách xóa đang được xác định (Q-07 trong QT-01).

---

## 16. Tài liệu liên quan

| Tài liệu | Nội dung |
|----------|----------|
| [Kế hoạch triển khai](docs/2-ky-thuat/ke-hoach-chatbot-tlu.md) | Giai đoạn, phụ thuộc, rủi ro, câu hỏi mở |
| [Kiến trúc](docs/2-ky-thuat/kien-truc-chatbot-tlu.md) | Sơ đồ thành phần, quyết định kỹ thuật (ADR) |
| [QT-01: Sinh viên hỏi đáp](docs/2-ky-thuat/flows/QT-01-hoi-dap-sinh-vien.md) | Luồng hỏi đáp, lỗi, tiêu chí nghiệm thu |
| [QT-02: Nạp và cập nhật tri thức](docs/2-ky-thuat/flows/QT-02-cap-nhat-tri-thuc-chatbot.md) | Luồng nạp, lỗi, tiêu chí nghiệm thu |
| [AGENTS.md](AGENTS.md) | Quy ước cho người và AI làm việc trên mã nguồn |

---

## 17. Liên hệ

| Vai trò | Người | Cách liên hệ |
|---------|-------|--------------|
| Người yêu cầu | [Điền] | [Điền] |
| Phụ trách kỹ thuật | [Điền] | [Điền] |
| Quản trị viên dữ liệu | [Điền] | [Điền] |

---

*Phiên bản README: 1.0, ngày 2026-10-13.*

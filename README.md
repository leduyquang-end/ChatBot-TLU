# ChatBot TLU

Chatbot hỏi đáp bằng tiếng Việt cho sinh viên Trường Đại học Thủy Lợi. Chatbot trả lời dựa trên tài liệu của trường. Khi tài liệu không có thông tin, chatbot nói rõ là không có và gợi ý liên hệ, không tự trả lời theo kiến thức chung.

> **Trạng thái:** đang triển khai. Xem [kế hoạch triển khai](docs/2-ky-thuat/Plan_chatbot_tlu.md) và [kiến trúc](docs/2-ky-thuat/Kien_truc_chatbot_tlu.md).

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
- Giao diện web (HTML/CSS/JS, phục vụ bởi nginx) gọi API backend qua `/api`.
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
└── frontend/               Giao diện web
    ├── Dockerfile          nginx
    ├── nginx.conf          tệp tĩnh + proxy /api/* → backend
    └── public/
        ├── index.html      khung trang (đăng nhập, chat, hồ sơ, quản trị)
        ├── styles.css      giao diện responsive
        ├── api.js          gọi API + tự làm mới token
        └── app.js          điều khiển giao diện
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

---

## 6. Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|------------|---------|
| Ngôn ngữ và runtime | Python 3.11; Node.js 18+ chỉ cần khi kiểm tra cú pháp giao diện |
| Docker | Docker Desktop / Docker Engine + Docker Compose v2 |
| ChromaDB | Chạy bằng Docker Compose, cổng nội bộ `8000` (máy host `8001`) |
| Neo4j | Chạy bằng Docker Compose, `bolt://localhost:7687`, giao diện `http://localhost:7474` |
| Groq | Khóa API, còn hạn mức |
| Qwen / OpenRouter | Khóa API, còn hạn mức |
| Hugging Face | Token là tùy chọn; mô hình `bkai-foundation-models/vietnamese-bi-encoder` là công khai |
| Hệ điều hành | Windows 10/11, Linux hoặc macOS có Docker |
| Phần cứng | Tối thiểu 4 GB RAM trống cho stack; không cần GPU (torch bản CPU trong image) |

---

## 7. Cấu hình

Mọi khóa API và địa chỉ dịch vụ đặt trong biến môi trường, không đưa vào mã nguồn hay commit lên repo.

### 7.1. Biến môi trường

| Biến | Bắt buộc | Mục đích |
|------|:--------:|----------|
| `GROQ_API_KEY` | Có | Khóa Groq cho router và trích thực thể từ câu hỏi |
| `QWEN_API_KEY` | Có | Khóa Qwen/OpenRouter cho trích thực thể khi nạp và sinh câu trả lời |
| `HF_TOKEN` | Không | Token Hugging Face; giá trị mẫu `your-...` được coi như chưa cấu hình |
| `APP_SECRET` | Có khi chạy thật | Khóa ký access/refresh token, tối thiểu 32 ký tự ngẫu nhiên |
| `APP_PORT` | Không | Cổng API trên máy host (mặc định `8010`) |
| `FRONTEND_PORT` | Không | Cổng giao diện trên máy host (mặc định `8080`) |
| `CHROMA_URL` | Có | Địa chỉ ChromaDB (`http://localhost:8001` khi chạy ngoài Docker) |
| `NEO4J_URI` | Có | Địa chỉ Neo4j (`bolt://localhost:7687`) |
| `NEO4J_USER` | Có | Tài khoản Neo4j |
| `NEO4J_PASSWORD` | Có | Mật khẩu Neo4j |
| `QWEN_BASE_URL` | Không | Base URL tương thích OpenAI; mặc định DashScope |
| `ANSWER_MODEL` | Không | Tên model sinh câu trả lời, nhiều model cách nhau dấu phẩy để fallback |

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

```bash
# 1. Lấy mã nguồn
git clone <địa-chỉ-repo> ChatBot
cd ChatBot

# 2. Tạo môi trường Python và cài phụ thuộc
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows PowerShell
# source .venv/bin/activate    # Linux / macOS
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd ..

# 3. Tạo file cấu hình từ mẫu
# Windows PowerShell:
Copy-Item .env.example .env
# Linux / macOS:
# cp .env.example .env

# 4. Điền khóa API và địa chỉ dịch vụ trong .env
#    Sinh APP_SECRET (bắt buộc khi chạy thật):
python -c "import secrets; print(secrets.token_urlsafe(48))"

# 5. Khởi động ChromaDB + Neo4j
docker compose up -d chroma neo4j
docker compose ps
```

**Kiểm tra nhanh sau khi cài:**

- `docker compose ps` báo `chroma` và `neo4j` ở trạng thái `healthy`.
- Neo4j mở được tại `http://localhost:7474` bằng tài khoản trong `.env`.
- Groq và Qwen/OpenRouter trả lời một yêu cầu đơn giản với khóa đã cấu hình.
- Lần hỏi đầu tiên sẽ tải mô hình embedding (vài trăm MB) và có thể chậm hơn các lần sau.

---

## 9. Nạp tri thức

Chạy thủ công theo đợt, do quản trị viên dữ liệu thực hiện.

### 9.1. Chuẩn bị

1. Đặt tài liệu nguồn trong `data/` (ví dụ `data/Chương trình đào tạo/`, `data/Sổ tay sinh viên/`). Pipeline quét đệ quy và tự bỏ qua các thư mục `processed/`.
2. Kiểm tra ChromaDB và Neo4j đang chạy: `docker compose ps`.
3. Kiểm tra khóa API còn hạn mức trong `.env`.

### 9.2. Chạy

```bash
# Build image backend (ingest dùng chung image chatbot-tlu:latest)
docker compose build backend

# Nạp toàn bộ data/ trong container; tự khởi động Chroma/Neo4j nếu chưa chạy
docker compose --profile ingest run --rm ingest
```

Lệnh trên mount `./data` vào `/app/data` để ghi được log vào `*/processed/extract_log.jsonl`.

### 9.3. Kết quả

Theo dõi log của lệnh ingest; cuối mỗi tài liệu có dòng tổng kết số đoạn, số thực thể, số quan hệ và số lần gộp trùng. Log resume nằm tại `data/<thư-mục>/processed/extract_log.jsonl`.

### 9.4. Chạy lại

Chạy lại trên cùng tài liệu không tạo bản trùng:

- ChromaDB dùng ID ổn định `sha256(tên file + nội dung đoạn)` và `upsert`.
- Neo4j dùng `MERGE` cho thực thể và quan hệ.

Tài liệu đã bị xóa khỏi `data/` **không** tự động bị xóa khỏi hai kho; cần xóa thủ công nếu muốn loại bỏ hoàn toàn.

---

## 10. Chạy ứng dụng

```bash
# Chạy toàn bộ stack (backend + frontend + Chroma + Neo4j)
docker compose up -d --build

# Xem trạng thái và log
docker compose ps
docker compose logs -f backend
```

- Giao diện: `http://localhost:8080` (đổi bằng `FRONTEND_PORT`).
- API trực tiếp: `http://localhost:8010/health` (đổi bằng `APP_PORT`); nginx chuyển `/api/*` trên cổng 8080 sang backend và bỏ tiền tố `/api`.
- Đăng nhập demo: `sinhvien01 / demo-password` (sinh viên) hoặc `admin01 / demo-password` (quản trị).
- Lần hỏi đầu tiên có thể chậm do tải mô hình embedding; timeout đã đặt 300 giây.

Chạy backend ngoài Docker để phát triển API (UI trong container không gọi được backend trên host):

```powershell
cd backend
$env:PYTHONIOENCODING="utf-8"
.venv\Scripts\python.exe -m src.main
```

Dừng stack nhưng giữ dữ liệu: `docker compose down`. **Không dùng `docker compose down -v`** trừ khi muốn xóa cả kho tri thức và cache mô hình.

---

## 11. Kiểm thử

| Loại | Phạm vi | Yêu cầu |
|------|---------|---------|
| **Unit** | Làm sạch, chia đoạn, gộp bảng, khử trùng lặp, router, dựng prompt | Không cần dịch vụ ngoài |
| **Integration** | Kết nối ChromaDB, Neo4j, các client LLM | Cần dịch vụ thật đang chạy |
| **E2E** | Luồng hỏi đáp đầy đủ theo tiêu chí AC trong QT-01 và QT-02 | Cần cả hai kho có dữ liệu |

```bash
# Chạy từ thư mục backend, dùng đúng venv của dự án
cd backend

# Unit: không cần dịch vụ ngoài
.venv\Scripts\python.exe -m pytest tests/unit -q

# Integration: cần Chroma + Neo4j đang chạy và .env hợp lệ
.venv\Scripts\python.exe -m pytest tests/integration -q

# Lint
.venv\Scripts\python.exe -m ruff check src tests scripts

# E2E: chưa có bộ tự động; chạy stack rồi kiểm tra thủ công qua UI
# (đăng nhập, hỏi đáp, xem nguồn, lịch sử, đổi mật khẩu)
```

Trên Linux/macOS thay `.venv\Scripts\python.exe` bằng `.venv/bin/python`.

**Tiêu chí nghiệm thu** nằm trong mục 12 của hai file đặc tả:

- [QT-01](docs/2-ky-thuat/flows/QT1_hoi_dap_sinh_vien.md): AC-01 đến AC-05.
- [QT-02](docs/2-ky-thuat/flows/QT2_cap_nhat_tri_thuc.md): AC-01 đến AC-05.

---

## 12. Quy ước phát triển

- Đọc `AGENT.md` trước khi sửa mã. File này mô tả quy ước module, lớp, và lệnh kiểm thử.
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

- Backend chạy **một gunicorn worker** vì phiên đăng nhập, người dùng và lịch sử hội thoại đang lưu trong RAM. Khởi động lại backend sẽ mất các dữ liệu này; không scale ngang được cho đến khi chuyển sang Redis/DB dùng chung.
- Toàn bộ kho tri thức và cache mô hình nằm trong Docker volume. `docker compose down -v` sẽ xóa chúng và phải nạp lại từ đầu.
- Lần hỏi đầu tiên tải mô hình embedding; nếu mạng chậm có thể vượt timeout hoặc cần nạp sẵn cache.
- `chunk_size` có thể là token. Nếu vậy sẽ vượt giới hạn 256 token của mô hình embedding, làm đoạn bị cắt khi nhúng. Cần xác định trước khi nạp dữ liệu thật (Q-12 trong QT-02).
- Chưa có số liệu về độ trễ và chi phí API.
- Chất lượng router và câu trả lời chưa được đo bằng bộ câu hỏi chuẩn (P-05 trong kế hoạch).
- Mô hình ngôn ngữ dựa trên tài liệu nguồn. Thông tin cũ trong tài liệu sẽ được trả lời như cũ cho đến khi nạp lại.
- Nạp lại không tự xóa các đoạn/thực thể của tài liệu đã bị gỡ khỏi `data/`.
- Chưa có bộ test E2E tự động và chưa có kênh chuyển câu hỏi cho người thật.

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
| [Kế hoạch triển khai](docs/2-ky-thuat/Plan_chatbot_tlu.md) | Giai đoạn, phụ thuộc, rủi ro, câu hỏi mở |
| [Kiến trúc](docs/2-ky-thuat/Kien_truc_chatbot_tlu.md) | Sơ đồ thành phần, quyết định kỹ thuật (ADR) |
| [QT-01: Sinh viên hỏi đáp](docs/2-ky-thuat/flows/QT1_hoi_dap_sinh_vien.md) | Luồng hỏi đáp, lỗi, tiêu chí nghiệm thu |
| [QT-02: Nạp và cập nhật tri thức](docs/2-ky-thuat/flows/QT2_cap_nhat_tri_thuc.md) | Luồng nạp, lỗi, tiêu chí nghiệm thu |
| [AGENTS.md](AGENT.md) | Quy ước cho người và AI làm việc trên mã nguồn |

---

## 17. Liên hệ

| Vai trò | Người | Cách liên hệ |
|---------|-------|--------------|
| Người yêu cầu | [Điền] | [Điền] |
| Phụ trách kỹ thuật | [Điền] | [Điền] |
| Quản trị viên dữ liệu | [Điền] | [Điền] |

---

*Phiên bản README: 1.0, ngày 2026-10-13.*

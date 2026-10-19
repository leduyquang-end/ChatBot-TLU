# AGENTS.md

Hướng dẫn cho người và trợ lý AI làm việc trên mã nguồn dự án ChatBot TLU. Đọc toàn bộ file này trước khi sửa bất kỳ tệp nào.

> Phiên bản: 1.1 - 2026-10-13
> File này thay thế `CLAUDE.md`. Không tạo `CLAUDE.md` song song.
> Nguyên tắc ưu tiên: **nếu không chắc, hỏi hoặc ghi câu hỏi. Đừng đoán.**

---

## Mục lục

1. [Dự án làm gì](#1-dự-án-làm-gì)
2. [Thuật ngữ](#2-thuật-ngữ)
3. [Cấu trúc thư mục](#3-cấu-trúc-thư-mục)
4. [Quy ước module và lớp](#4-quy-ước-module-và-lớp)
5. [Module chat: luồng hỏi đáp](#5-module-chat-luồng-hỏi-đáp)
6. [Module nạp tri thức](#6-module-nạp-tri-thức)
7. [Dịch vụ bên ngoài](#7-dịch-vụ-bên-ngoài)
8. [Cấu hình và biến môi trường](#8-cấu-hình-và-biến-môi-trường)
9. [Xử lý lỗi](#9-xử-lý-lỗi)
10. [Logging](#10-logging)
11. [Bảo mật và quyền riêng tư](#11-bảo-mật-và-quyền-riêng-tư)
12. [Quy ước đặt tên](#12-quy-ước-đặt-tên)
13. [Kiểm thử](#13-kiểm-thử)
14. [Đặc tả và tài liệu](#14-đặc-tả-và-tài-liệu)
15. [Quy trình làm việc theo tình huống](#15-quy-trình-làm-việc-theo-tình-huống)
16. [Git và commit](#16-git-và-commit)
17. [Checklist trước khi nộp](#17-checklist-trước-khi-nộp)
18. [Việc không được làm mà không hỏi](#18-việc-không-được-làm-mà-không-hỏi)
19. [Khi không chắc](#19-khi-không-chắc)
20. [Câu hỏi mở đang chờ](#20-câu-hỏi-mở-đang-chờ)
21. [Tài liệu liên quan](#21-tài-liệu-liên-quan)

---

## 1. Dự án làm gì

Chatbot hỏi đáp bằng tiếng Việt cho sinh viên Trường Đại học Thủy Lợi. Chatbot chỉ trả lời dựa trên tài liệu của trường. Khi không có thông tin, chatbot nói rõ là không có và gợi ý liên hệ, không trả lời theo kiến thức chung.

Lý do quy tắc này tồn tại: sinh viên cần thông tin đúng về quy định, học phí, học bổng. Một câu trả lời bịa có thể gây thiệt hại thật.

Chi tiết xem [README](README.md) và [tổng quan](docs/1-tong-quan/tong-quan-chatbot-tlu.md).

---

## 2. Thuật ngữ

| Thuật ngữ          | Nghĩa trong dự án                                      | Ghi chú                                           |
| ------------------ | ------------------------------------------------------ | ------------------------------------------------- |
| Tri thức           | Nội dung từ tài liệu trường đã nạp                     | Gồm đoạn văn bản và thực thể/quan hệ              |
| Nạp tri thức       | Quy trình đưa tài liệu vào hai kho                     | Chạy theo đợt, thủ công                           |
| Đoạn (chunk)       | Một phần văn bản đã chia, có metadata                  | Văn bản chia theo điều khoản; bảng chia theo khối |
| Khối bảng          | Các dòng cùng mã định danh gộp lại                     | Mỗi khối mô tả một thực thể                       |
| Vector             | Biểu diễn số của đoạn, 768 chiều                       | Dùng để tìm theo nghĩa                            |
| Thực thể (entity)  | Node trong đồ thị: môn học, ngành, học phí...          | Có tên, mô tả, loại                               |
| Quan hệ (edge)     | Cạnh nối hai thực thể                                  | Có mô tả và độ tin cậy                            |
| Router             | Bước chọn cách tìm cho mỗi câu hỏi                     | Dùng Llama-3.3-70B qua Groq                       |
| Cách tìm           | Một trong bốn nhãn: Vector, Graph, Hybrid, None        | Xem mục 5.2                                       |
| MMR                | Thuật toán chọn đoạn vừa liên quan vừa đa dạng         | Maximal Marginal Relevance                        |
| MERGE              | Lệnh Cypher: tạo nếu chưa có, bỏ qua nếu đã có         | Giúp chạy lại không trùng                         |
| Port               | Interface do module đích định nghĩa để module khác gọi | Xem mục 4.3                                       |
| QT-nn              | Mã đặc tả quy trình                                    | Ví dụ QT-01 là hỏi đáp                            |
| GD-xx              | Giả định chưa được xác nhận                            | Ghi trong đặc tả                                  |
| Q-xx / P-xx / A-xx | Câu hỏi mở                                             | Mã khác nhau theo tài liệu                        |
| AC                 | Tiêu chí nghiệm thu                                    | Cho / Khi / Thì                                   |

---

## 3. Cấu trúc thư mục

```
ChatBot/
├── AGENTS.md                  File này
├── README.md                  Hướng dẫn cài đặt và chạy
├── .env.example               Mẫu biến môi trường (không chứa khóa thật) [Điền: nếu có]
├── docs/
│   ├── 1-tong-quan/           Tổng quan cho lãnh đạo và người mới
│   ├── 2-ky-thuat/            Kế hoạch, kiến trúc, đặc tả QT
│   │   ├── ke-hoach-chatbot-tlu.md
│   │   ├── kien-truc-chatbot-tlu.md
│   │   └── flows/
│   │       ├── QT-01-hoi-dap-sinh-vien.md
│   │       └── QT-02-cap-nhat-tri-thuc-chatbot.md
│   ├── 3-san-pham/            Mô tả sản phẩm
│   ├── 4-van-hanh/            Vận hành, sự cố, sao lưu
│   ├── 5-mau/                 Mẫu tài liệu (Template A)
│   ├── 6-design/              Thiết kế giao diện
│   └── 7-ghi-chu/             Ghi chú họp, quyết định nhỏ
├── scripts/                   Lệnh chạy thủ công
│   └── [Điền: tên script nạp tri thức]
├── src/
│   ├── modules/
│   │   ├── auth/              Xác thực
│   │   ├── chat/              Hỏi đáp chatbot (xem mục 5)
│   │   └── user/              Người dùng (mẫu chuẩn 4 lớp)
│   ├── platform/
│   │   ├── logging/           Cấu hình và tiện ích ghi log
│   │   └── security/          Xác thực token, băm mật khẩu, kiểm tra đầu vào
│   └── shared/
│       ├── common/            Kiểu lỗi, tiện ích dùng chung
│       ├── config/            Đọc và kiểm tra cấu hình
│       ├── database/          Kết nối cơ sở dữ liệu quan hệ
│       └── events/            Định nghĩa sự kiện dùng chung
└── tests/
    ├── unit/                  Mirror cấu trúc src/
    ├── integration/           Cần dịch vụ thật
    └── e2e/                   Luồng đầy đủ
```

**Quy tắc thư mục:**

- Không thêm thư mục ở cấp gốc mà không hỏi người phụ trách.
- Không đặt mã nguồn ngoài `src/` và `scripts/`.
- Không đặt file tạm, file sinh tự động, hay file có khóa trong repo.
- `tests/unit/` phải phản ánh cấu trúc `src/`. Ví dụ `src/modules/chat/domain/x.py` tương ứng `tests/unit/modules/chat/domain/test_x.py`.

---

## 4. Quy ước module và lớp

### 4.1. Bốn lớp

Mỗi module trong `src/modules/` có bốn lớp. Module `user` là mẫu chuẩn: khi thêm module mới hoặc lớp mới, sao chép cấu trúc từ `user`.

| Lớp              | Chứa gì                                                        | Ví dụ trong `chat`                                         |
| ---------------- | -------------------------------------------------------------- | ---------------------------------------------------------- |
| `api`            | Route HTTP, schema đầu vào và đầu ra, chuyển lỗi thành mã HTTP | Route `POST /chat/ask`, `GET /chat/history`                |
| `application`    | Các use case: gọi đúng thứ tự các bước, quản lý giao dịch      | `AskQuestionUseCase`, `LoadHistoryUseCase`                 |
| `domain`         | Thực thể nghiệp vụ, giá trị, quy tắc thuần túy                 | `RetrievalMode` (4 nhãn), `NoInfoPolicy`                   |
| `infrastructure` | Client và adapter cho dịch vụ bên ngoài                        | `ChromaVectorStore`, `Neo4jGraphStore`, `GroqRouterClient` |

### 4.2. Phụ thuộc được phép

```
api  →  application  →  domain
                ↓
          (port trong application)
                ↑
        infrastructure  (cài đặt port)
```

- `api` chỉ gọi `application`.
- `application` gọi `domain`, và gọi qua port. Không gọi trực tiếp `infrastructure`.
- `domain` không import từ lớp nào khác trong module, và không import thư viện HTTP hay cơ sở dữ liệu.
- `infrastructure` cài đặt port, có thể import `domain`.

### 4.3. Port

Port là interface do `application` định nghĩa. Ví dụ với module `chat`:

- `application/ports/retrieval.py` định nghĩa `RetrievalPort`, với phương thức nhận câu hỏi và trả về danh sách đoạn.
- `infrastructure/chroma_retrieval.py` cài đặt `RetrievalPort` bằng ChromaDB.
- `application` chỉ biết `RetrievalPort`, không biết ChromaDB tồn tại.

Lợi ích: thay đổi kho dữ liệu chỉ cần sửa `infrastructure`.

### 4.4. Giao tiếp giữa module

- Module A cần dữ liệu từ module B: module B phải cung cấp một cổng công khai (port hoặc service nội bộ được khai báo rõ).
- Không import `modules.B.infrastructure` hay `modules.B.application.internal` từ module A.
- Nếu cần sự kiện giữa các module, dùng `src/shared/events/`, không gọi chéo trực tiếp.

### 4.5. Client dùng chung

- Client dùng nhiều module (ví dụ client Neo4j nếu cả `chat` và `knowledge` dùng) đặt trong `src/platform/` hoặc `src/shared/database/`.
- Client chỉ một module dùng đặt trong `infrastructure` của module đó.

### 4.6. Khi thêm module mới

1. Sao chép cấu trúc `src/modules/user/` và xóa nội dung cũ.
2. Đặt tên module theo danh từ số ít, tiếng Anh, chữ thường: `chat`, `user`, `auth`.
3. Khai báo các port cần thiết trong `application/ports/`.
4. Viết unit test cho `domain` và `application` trước khi viết `infrastructure`.
5. Cập nhật mục 3 của file này và `README.md`.

---

## 5. Module chat: luồng hỏi đáp

Đặc tả: [QT-01](docs/2-ky-thuat/flows/QT1_hoi_dap_sinh_vien.md).

### 5.1. Các bước của một câu hỏi

| Bước | Lớp              | Việc làm                                                                 |
| ---- | ---------------- | ------------------------------------------------------------------------ |
| 1    | `api`            | Nhận câu hỏi. Từ chối nếu rỗng hoặc chỉ có ký tự đặc biệt                |
| 2    | `application`    | Gọi router để lấy cách tìm                                               |
| 3    | `application`    | Truy xuất theo cách tìm qua port                                         |
| 4    | `application`    | Kiểm tra có đoạn phù hợp không. Nếu không, trả thông báo cố định và dừng |
| 5    | `application`    | Dựng prompt từ domain (vai trò, quy tắc, câu hỏi, tri thức, lịch sử)     |
| 6    | `infrastructure` | Gọi mô hình sinh câu trả lời                                             |
| 7    | `application`    | Lưu lượt hỏi đáp vào lịch sử                                             |
| 8    | `api`            | Trả câu trả lời                                                          |

### 5.2. Bốn cách tìm

| Nhãn     | Dùng khi                                | Nhánh                                                         |
| -------- | --------------------------------------- | ------------------------------------------------------------- |
| `Vector` | Định nghĩa, quy định chi tiết           | Tìm cosine, lấy 10 ứng viên, chọn 5 bằng MMR                  |
| `Graph`  | Quan hệ, điều kiện tiên quyết, liên kết | Trích thực thể từ câu hỏi, chấm điểm node, lấy cạnh vào và ra |
| `Hybrid` | Câu hỏi phức tạp, suy luận nhiều bước   | Chạy `Vector` và `Graph`, gộp ngữ cảnh                        |
| `None`   | Giao tiếp thông thường                  | Không truy xuất                                               |

**Quy tắc router:**

- Đầu ra phải là JSON có một trong bốn nhãn trên.
- Nếu sai định dạng hoặc nhãn lạ, dùng `Vector`.
- Router không bao giờ làm hệ thống dừng lại. Mọi lỗi của router đều rơi về `Vector`.

### 5.3. Công thức và tham số

| Tham số             | Giá trị         | Ý nghĩa                                                        |
| ------------------- | --------------- | -------------------------------------------------------------- |
| `fetch_k`           | 10              | Số ứng viên trước MMR                                          |
| `top_k`             | 5               | Số đoạn vào prompt                                             |
| `alpha`             | 0.6 đến 0.8     | Tỷ trọng ngữ nghĩa: `score = α·semantic + (1−α)·keyword`       |
| `chunk_size`        | 800             | Đơn vị chưa rõ (Q-12 trong QT-02)                              |
| `overlap`           | 120             | Đoạn chồng lên nhau                                            |
| `dedup_threshold`   | 0.92            | Cosine tối thiểu để gộp thực thể                               |
| `no_info_threshold` | [Chưa xác định] | Ngưỡng điểm để trả "không có thông tin" (A-03 trong kiến trúc) |

Các tham số này đọc từ `src/shared/config/`. Không hard-code trong mã nghiệp vụ.

Đổi giá trị tham số: phải cập nhật tài liệu liên quan và ghi vào lịch sử thay đổi của file kiến trúc.

### 5.4. Prompt

Prompt phải có đủ năm phần, theo thứ tự:

1. Vai trò: trợ lý tra cứu thông tin của Trường Đại học Thủy Lợi.
2. Quy tắc:
   - Chỉ dùng thông tin trong phần "Tài liệu".
   - Không bịa, không thêm kiến thức chung.
   - Trả lời bằng tiếng Việt.
   - Nếu tài liệu không đủ, nói rõ và không suy đoán.
3. Lịch sử hội thoại (nếu có).
4. Tài liệu đã truy xuất, kèm tên tài liệu và mục để trích dẫn.
5. Câu hỏi hiện tại.

Không đưa khóa API hay thông tin cá nhân vào prompt.

### 5.5. Điều không được làm

- Không gọi mô hình sinh câu trả lời khi không có đoạn phù hợp (đây là quy tắc sản phẩm).
- Không cho prompt hướng mô hình dùng kiến thức chung.
- Không lưu câu hỏi vào log mức thông tin (xem mục 10).
- Không trả về thông tin của sinh viên khác trong lịch sử.

---

## 6. Module nạp tri thức

Đặc tả: [QT-02](docs/2-ky-thuat/flows/QT2_cap_nhat_tri_thuc.md).

Vị trí mã chưa chốt (P-03 trong kế hoạch). Ghi lại lựa chọn vào [7-ghi-chu](docs/7-ghi-chu/) khi quyết định.

### 6.1. Các bước

| Bước | Việc làm                                                         | Đầu ra                     |
| ---- | ---------------------------------------------------------------- | -------------------------- |
| 1    | Đọc tài liệu: trang web, DOCX, PDF, XLSX                         | Văn bản thô hoặc bảng      |
| 2    | Làm sạch: bỏ khoảng trắng, ký tự thừa, tiêu đề và chân trang lặp | Văn bản sạch               |
| 3    | Tách bảng XLSX thành file riêng                                  | File bảng                  |
| 4    | Chia đoạn văn bản theo điều khoản (`chunk_size`, `overlap`)      | Danh sách đoạn có metadata |
| 5    | Xử lý bảng: điền ô gộp, bỏ dòng tổng, gộp theo mã định danh      | Danh sách khối             |
| 6    | Nhúng đoạn và lưu vào ChromaDB                                   | Vector trong kho           |
| 7    | Trích thực thể và quan hệ bằng Qwen                              | Thực thể và quan hệ thô    |
| 8    | Gộp trùng hai giai đoạn                                          | Thực thể đã gộp            |
| 9    | Ghi vào Neo4j bằng MERGE                                         | Đồ thị đã cập nhật         |
| 10   | Tổng hợp báo cáo                                                 | Báo cáo đợt nạp            |

### 6.2. Quy tắc gộp trùng

- Giai đoạn 1: tên chính xác giống nhau thì gộp.
- Giai đoạn 2: cosine từ 0.92 trở lên thì gộp.
- Khi gộp: giữ thực thể có mô tả dài hơn. Chuyển toàn bộ quan hệ về thực thể được giữ.
- Cặp quan hệ trùng (cùng nguồn và đích): giữ cặp có nhiều thông tin và độ tin cậy cao hơn.
- Ghi nhật ký mọi lần gộp để kiểm tra sau.

### 6.3. Điều không được làm

- Không xóa dữ liệu cũ trong kho khi nạp, trừ khi có yêu cầu rõ ràng.
- Không chạy lại bước xác định loại thực thể (dùng 500 câu hỏi, chỉ một lần) trừ khi được yêu cầu.
- Không nạp tài liệu chưa được xác nhận nguồn chính thức.
- Không bỏ qua file lỗi mà không ghi vào báo cáo.

### 6.4. Chạy lại

- Chạy lại trên cùng tài liệu không được tạo bản trùng trong Neo4j.
- Với ChromaDB, [Điền: cách tránh trùng đoạn khi chạy lại, ví dụ dùng ID ổn định từ nội dung].

---

## 7. Dịch vụ bên ngoài

| Dịch vụ              | Dùng cho                                                  | Biến cấu hình                               | Giới hạn                       |
| -------------------- | --------------------------------------------------------- | ------------------------------------------- | ------------------------------ |
| Groq (Llama-3.3-70B) | Router, xác định loại thực thể, trích thực thể từ câu hỏi | `GROQ_API_KEY`                              | [Điền: hạn mức]                |
| Qwen3-235B-A22B      | Trích thực thể khi nạp, sinh câu trả lời                  | `QWEN_API_KEY`                              | [Điền: hạn mức]                |
| Hugging Face         | Tải `bkai-foundation-models/vietnamese-bi-encoder`        | `HF_TOKEN`                                  | Giới hạn 256 token mỗi đầu vào |
| ChromaDB             | Kho tìm theo nội dung                                     | `CHROMA_URL`                                | [Điền]                         |
| Neo4j                | Kho thực thể và quan hệ                                   | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` | [Điền]                         |

### 7.1. Quy tắc khi gọi dịch vụ

- Mọi lần gọi có thời gian chờ. Giá trị: [Điền: giây].
- Thử lại có giới hạn: tối đa [Điền] lần, khoảng chờ tăng dần.
- Chỉ thử lại với lỗi tạm thời (timeout, 429, 5xx). Lỗi xác thực (401, 403) thì dừng và báo.
- Ghi mã lỗi và thời gian. Không ghi nội dung câu hỏi, không ghi khóa.
- Không gọi dịch vụ trong vòng lặp không có giới hạn.
- Mỗi lần gọi là một cơ hội tốn tiền. Gom yêu cầu khi có thể.

### 7.2. Dịch vụ không sẵn sàng

| Dịch vụ  | Hành vi mong muốn                                 | Người dùng thấy                                           |
| -------- | ------------------------------------------------- | --------------------------------------------------------- |
| Groq     | Dùng nhánh `Vector` nếu router không trả lời      | Không thấy lỗi                                            |
| Qwen     | Trả thông báo tạm thời, không cố sinh câu trả lời | "Hệ thống đang bận, bạn thử lại sau" (chờ xác nhận, Q-04) |
| ChromaDB | Ghi log lỗi, trả thông báo tạm thời               | Chờ xác nhận (Q-04)                                       |
| Neo4j    | Chỉ dùng `Vector` cho đến khi phục hồi            | Không thấy lỗi nếu `Vector` đủ                            |

---

## 8. Cấu hình và biến môi trường

### 8.1. Nguyên tắc

- Mọi giá trị thay đổi theo môi trường đọc từ biến môi trường.
- Mọi giá trị mặc định nằm trong `src/shared/config/` kèm chú thích.
- Khi thiếu biến bắt buộc, ứng dụng dừng khi khởi động và báo tên biến thiếu. Không chạy với giá trị rỗng.
- Không đọc `os.environ` hay tương đương trực tiếp trong module nghiệp vụ.

### 8.2. Danh sách biến

| Biến              | Bắt buộc | Mặc định | Mô tả                    |
| ----------------- | :------: | -------- | ------------------------ |
| `GROQ_API_KEY`    |    Có    | Không    | Khóa Groq                |
| `QWEN_API_KEY`    |    Có    | Không    | Khóa Qwen API            |
| `HF_TOKEN`        |    Có    | Không    | Token Hugging Face       |
| `CHROMA_URL`      |    Có    | Không    | Địa chỉ ChromaDB         |
| `NEO4J_URI`       |    Có    | Không    | Địa chỉ Neo4j            |
| `NEO4J_USER`      |    Có    | Không    | Tài khoản Neo4j          |
| `NEO4J_PASSWORD`  |    Có    | Không    | Mật khẩu Neo4j           |
| `LOG_LEVEL`       |  Không   | `INFO`   | Mức log                  |
| `CHUNK_SIZE`      |  Không   | `800`    | Xem Q-12                 |
| `CHUNK_OVERLAP`   |  Không   | `120`    |                          |
| `FETCH_K`         |  Không   | `10`     |                          |
| `TOP_K`           |  Không   | `5`      |                          |
| `ALPHA`           |  Không   | `0.7`    | Trong khoảng 0.6 đến 0.8 |
| `DEDUP_THRESHOLD` |  Không   | `0.92`   |                          |

[Điền: thêm biến nếu có, ví dụ thời gian chờ, số lần thử lại.]

### 8.3. File mẫu

Có file `.env.example` ở gốc với các biến và giá trị giả. Không commit `.env` thật. Thêm `.env` vào `.gitignore`.

---

## 9. Xử lý lỗi

### 9.1. Kiểu lỗi chuẩn

Định nghĩa trong `src/shared/common/errors.py` [Điền: đường dẫn thật]:

| Lỗi                    | Khi nào               | Mã HTTP |
| ---------------------- | --------------------- | ------- |
| `ValidationError`      | Đầu vào sai           | 400     |
| `UnauthorizedError`    | Chưa đăng nhập        | 401     |
| `ForbiddenError`       | Không có quyền        | 403     |
| `NotFoundError`        | Không tìm thấy        | 404     |
| `ExternalServiceError` | Dịch vụ bên ngoài lỗi | 503     |
| `InternalError`        | Lỗi không mong đợi    | 500     |

### 9.2. Quy tắc

- Lớp `domain` và `application` ném lỗi nghiệp vụ, không ném lỗi HTTP.
- Lớp `api` chuyển lỗi nghiệp vụ thành mã HTTP.
- Lỗi từ thư viện bên ngoài phải được bọc thành `ExternalServiceError` ở `infrastructure`.
- Không bắt lỗi rồi bỏ qua mà không ghi log.
- Không hiển thị stack trace cho người dùng.

### 9.3. Thông báo cho sinh viên

- Thông báo thân thiện, tiếng Việt, không có thuật ngữ kỹ thuật.
- Không nói "lỗi Neo4j" hay "API timeout".
- Với trường hợp không có thông tin, dùng thông báo cố định (xem QT-01, E2).

---

## 10. Logging

### 10.1. Mức log

| Mức       | Dùng khi                                                                          |
| --------- | --------------------------------------------------------------------------------- |
| `DEBUG`   | Chi tiết để tìm lỗi khi phát triển. Không bật ở môi trường sản xuất               |
| `INFO`    | Sự kiện bình thường: khởi động, bắt đầu và kết thúc đợt nạp, số lượng đoạn đã ghi |
| `WARNING` | Bất thường nhưng hệ thống vẫn chạy: router trả sai định dạng, thử lại dịch vụ     |
| `ERROR`   | Lỗi cần xem: dịch vụ không phản hồi, ghi kho thất bại                             |

### 10.2. Nội dung được và không được ghi

**Được ghi:**

- Mã sự kiện (ví dụ `chat.router.fallback`, `ingest.batch.done`).
- Cách tìm đã chọn (nhãn).
- Số lượng đoạn, thực thể, quan hệ.
- Thời gian xử lý.
- Mã lỗi và tên dịch vụ.
- Mã định danh nội bộ của cuộc trò chuyện (không phải tên sinh viên).

**Không được ghi ở mức `INFO` trở lên:**

- Nội dung câu hỏi của sinh viên.
- Nội dung câu trả lời.
- Nội dung đoạn tài liệu (có thể dài và chứa thông tin nội bộ).
- Khóa API, mật khẩu, token.
- Thông tin cá nhân: họ tên, mã số sinh viên, số điện thoại, email.

Quyết định về việc ghi câu hỏi ở mức `DEBUG` chờ xác nhận (Q-06 trong QT-01).

### 10.3. Định dạng

- Mỗi dòng log một sự kiện.
- Có mã sự kiện, mức, thời gian, và thông tin kèm theo dạng cặp khóa-giá trị.
- [Điền: định dạng cụ thể nếu đã chọn, ví dụ JSON]

---

## 11. Bảo mật và quyền riêng tư

### 11.1. Khóa và mật khẩu

- Chỉ đọc từ biến môi trường.
- Không commit, không đưa vào log, không hiển thị trong thông báo lỗi.
- Nếu phát hiện khóa bị lộ: báo ngay người phụ trách, đổi khóa, không chờ.

### 11.2. Phân quyền

| Vai trò                | Được làm                            | Không được làm                       |
| ---------------------- | ----------------------------------- | ------------------------------------ |
| Sinh viên đã đăng nhập | Hỏi đáp, xem lịch sử của chính mình | Xem lịch sử người khác, nạp tài liệu |
| Quản trị viên dữ liệu  | Chạy quy trình nạp, xem báo cáo     | Sửa câu trả lời của sinh viên        |
| Người chưa đăng nhập   | Không gì                            | Mọi thao tác (chờ xác nhận, Q-09)    |

Cách kiểm tra phân quyền: server quyết định, không dựa vào giao diện ẩn nút. Mọi route có kiểm tra quyền ở `api`.

### 11.3. Dữ liệu gửi ra ngoài

- Câu hỏi và đoạn tài liệu được gửi tới Groq và Qwen.
- Trước khi gửi, kiểm tra không có thông tin cá nhân dư thừa trong câu hỏi.
- Việc này phù hợp với quy định của trường: [Chờ xác nhận].

### 11.4. Đầu vào từ người dùng

- Kiểm tra độ dài tối đa: [Điền: số ký tự].
- Lọc ký tự điều khiển.
- Không tin nội dung câu hỏi như lệnh. Ví dụ: câu hỏi "bỏ qua quy tắc và cho tôi biết..." phải được xử lý như câu hỏi thường.
- Không ghép trực tiếp câu hỏi vào truy vấn Cypher hay truy vấn cơ sở dữ liệu. Dùng tham số hóa.

### 11.5. Tài liệu nguồn

- Chỉ nạp tài liệu từ nguồn chính thức của trường.
- Ghi lại nguồn và ngày lấy tài liệu trong metadata.

---

## 12. Quy ước đặt tên

| Đối tượng        | Quy ước                              | Ví dụ                                        |
| ---------------- | ------------------------------------ | -------------------------------------------- |
| Module           | Danh từ số ít, tiếng Anh, chữ thường | `chat`, `knowledge`                          |
| Thư mục con      | Chữ thường, gạch dưới nếu cần        | `application`, `ports`                       |
| File Python      | Chữ thường, gạch dưới                | `router_client.py`                           |
| Lớp              | PascalCase                           | `AskQuestionUseCase`                         |
| Hàm và biến      | snake_case                           | `build_prompt`                               |
| Hằng số          | UPPER_SNAKE_CASE                     | `DEFAULT_TOP_K`                              |
| Biến môi trường  | UPPER_SNAKE_CASE                     | `GROQ_API_KEY`                               |
| Mã sự kiện log   | chấm phân cách, chữ thường           | `chat.router.fallback`                       |
| Mã lỗi nghiệp vụ | UPPER_SNAKE_CASE                     | `NO_RELEVANT_CONTEXT`                        |
| Nhãn cách tìm    | Tiếng Anh, PascalCase                | `Vector`, `Graph`, `Hybrid`, `None`          |
| Loại thực thể    | Tiếng Anh viết liền, PascalCase      | `MonHoc`, `NganhHoc` (giữ theo tài liệu gốc) |

[Điền: nếu dự án dùng Python, TypeScript, hay ngôn ngữ khác, điều chỉnh bảng trên theo quy ước của ngôn ngữ đó.]

**Ngôn ngữ trong code:**

- Tên biến, hàm, lớp: tiếng Anh.
- Chuỗi hiển thị cho sinh viên: tiếng Việt có dấu.
- Chú thích trong code: [Điền: tiếng Việt hoặc tiếng Anh, chọn một và giữ nhất quán].
- Tên miền nghiệp vụ trong tài liệu: tiếng Việt, ví dụ `HocPhi`, `ThuTuc`.

---

## 13. Kiểm thử

### 13.1. Phân loại

| Loại        | Vị trí               | Cần gì                                       | Chạy khi nào        |
| ----------- | -------------------- | -------------------------------------------- | ------------------- |
| Unit        | `tests/unit/`        | Không cần dịch vụ ngoài. Dùng mock hoặc fake | Mỗi lần sửa mã      |
| Integration | `tests/integration/` | ChromaDB, Neo4j đang chạy                    | Trước khi gộp nhánh |
| E2E         | `tests/e2e/`         | Cả hai kho có dữ liệu mẫu                    | Trước khi phát hành |

### 13.2. Lệnh

```bash
# Cài phụ thuộc
[Điền]

# Unit
[Điền]

# Integration (đảm bảo ChromaDB và Neo4j đang chạy)
[Điền]

# E2E
[Điền]

# Độ phủ
[Điền]
```

### 13.3. Quy tắc viết test

- Mỗi hàm trong `domain` có ít nhất một test cho trường hợp bình thường và một cho trường hợp lỗi.
- Mỗi tiêu chí AC trong QT-01 và QT-02 có ít nhất một test tương ứng. Đặt tên test theo mã AC, ví dụ `test_ac01_pdf_chunks_have_metadata`.
- Test phân quyền: có ít nhất một test người không có quyền bị từ chối.
- Test router: có ít nhất một test cho đầu ra sai định dạng, phải rơi về `Vector`.
- Test không gọi dịch vụ thật trong unit test. Dùng fake.
- Không để test phụ thuộc thứ tự chạy.
- Không để test phụ thuộc thời gian thực (dùng thời gian giả khi cần).

### 13.4. Dữ liệu test

- Bộ tài liệu mẫu đặt trong [Điền: đường dẫn, ví dụ `tests/fixtures/`].
- Bộ câu hỏi mẫu đặt trong [Điền].
- Không dùng dữ liệu thật của sinh viên trong test.

### 13.5. Đánh giá chất lượng câu trả lời

- Có bộ câu hỏi chuẩn với đáp án mong đợi. Vị trí: [Điền].
- Chạy trước và sau mỗi thay đổi lớn ở router, truy xuất, hoặc prompt.
- Ngưỡng chấp nhận: [Chờ xác nhận, P-05 trong kế hoạch].

---

## 14. Đặc tả và tài liệu

### 14.1. Đặc tả quy trình mới (QT-nn)

1. Đặt trong `docs/2-ky-thuat/flows/`.
2. Đặt tên `QT-<nn>-<ten-ngan>.md`. Số `<nn>` là số tiếp theo chưa dùng, hai chữ số.
3. Viết tiếng Việt. Tên khóa (vai trò, bảng, route, lớp) giữ tiếng Anh.
4. Dùng Template B trong `business-flow.md` làm khung. Nếu không có file đó, dùng cấu trúc của QT-01.
5. Mọi điều chưa biết ghi thành `GD-xx` hoặc `Q-xx`. Không tự suy đoán.
6. Mỗi thao tác ghi dữ liệu phải nói rõ: có thông báo không, ai nhận, có audit không.
7. Mỗi luồng chính có ít nhất ba luồng lỗi: không có quyền, không tìm thấy, dữ liệu sai.
8. Tiêu chí nghiệm thu dạng Cho / Khi / Thì. Có ít nhất một ca bị từ chối vì phân quyền.

### 14.2. Sửa đặc tả hiện có

- Không ghi đè nội dung cũ mà không tăng phiên bản.
- Tăng số phiên bản: nhỏ (1.0 → 1.1) cho sửa nhỏ, lớn (1.x → 2.0) khi đổi luồng chính.
- Thêm dòng vào "Lịch sử thay đổi" với phiên bản, ngày, và nội dung.

### 14.3. Khi đổi kiến trúc

- Cập nhật [kiến trúc](docs/2-ky-thuat/Kien_truc_chatbot_tlu.md).
- Nếu thay đổi làm đổi kế hoạch: cập nhật [kế hoạch](docs/2-ky-thuat/Plan_chatbot_tlu.md).
- Nếu thay đổi ảnh hưởng người dùng: cập nhật [tổng quan](docs/1-tong-quan/tong-quan-chatbot-tlu.md).
- Quyết định mới: thêm ADR với mã tiếp theo, ghi lý do và nguồn.

### 14.4. Ghi chú

- Ghi chú họp, quyết định nhỏ, và kết quả thử nghiệm đặt trong `docs/7-ghi-chú/`.
- Đặt tên theo ngày: `YYYY-MM-DD-<chu-de>.md`.

---

## 15. Quy trình làm việc theo tình huống

### 15.1. Thêm một câu trả lời mới cho sinh viên

Đây là việc đưa thêm tài liệu, không phải sửa code.

1. Kiểm tra tài liệu có từ nguồn chính thức không.
2. Chạy quy trình nạp (mục 6).
3. Kiểm tra báo cáo nạp.
4. Hỏi thử một câu liên quan. Xác nhận chatbot trả lời đúng.
5. Ghi vào ghi chú: ngày nạp, tên tài liệu, số đoạn.

### 15.2. Sửa một lỗi trả lời sai

1. Tái hiện: ghi câu hỏi, câu trả lời sai, và câu trả lời mong đợi.
2. Xác định nguyên nhân: tài liệu sai, truy xuất sai, router sai, hay prompt sai.
3. Viết test tái hiện lỗi trước khi sửa.
4. Sửa đúng nguyên nhân, không vá theo triệu chứng.
5. Chạy lại bộ câu hỏi chuẩn để kiểm tra không gây lỗi khác.

### 15.3. Thêm một tính năng mới

1. Viết hoặc cập nhật đặc tả QT trong `docs/2-ky-thuat/flows/`.
2. Xác định module thuộc về đâu. Nếu chưa rõ, hỏi.
3. Viết test cho tiêu chí AC.
4. Viết `domain` và `application` trước.
5. Viết `infrastructure` sau cùng.
6. Viết `api`.
7. Chạy toàn bộ test.
8. Cập nhật tài liệu liên quan (mục 14.3).

### 15.4. Thêm một dịch vụ bên ngoài mới

1. Hỏi người phụ trách trước. Đây là thay đổi kiến trúc.
2. Viết ADR mới trong kiến trúc, ghi lý do chọn dịch vụ và chi phí dự kiến.
3. Đặt port trong `application`.
4. Cài đặt trong `infrastructure`.
5. Thêm biến cấu hình, cập nhật mục 8.
6. Thêm vào bảng mục 7.

### 15.5. Sửa tham số thuật toán

1. Ghi lý do và giá trị cũ, giá trị mới.
2. Chạy bộ câu hỏi chuẩn trước và sau.
3. Cập nhật mục 5.3 hoặc 6 trong file này và kiến trúc.
4. Ghi vào lịch sử thay đổi.

### 15.6. Một dịch vụ bị lỗi trong sản xuất

1. Xem mục 7.2 để biết hành vi mong đợi.
2. Kiểm tra log: mã lỗi và thời điểm.
3. Nếu chatbot vẫn trả lời được (ví dụ dùng `Vector` khi Neo4j lỗi), theo dõi thêm, không cần dừng.
4. Nếu chatbot không trả lời được, báo người phụ trách ngay.
5. Ghi sự cố vào `docs/4-van-hanh/`.

### 15.7. Nạp lại toàn bộ tri thức

Chỉ làm khi thật sự cần, ví dụ đổi `chunk_size` hoặc đổi mô hình embedding.

1. Sao lưu hai kho trước.
2. Thông báo người dùng nếu có thời gian gián đoạn: [Chờ xác nhận].
3. Xóa hoặc đổi tên kho cũ. Không xóa khi chưa sao lưu.
4. Chạy quy trình nạp đầy đủ.
5. Kiểm tra báo cáo và bộ câu hỏi chuẩn.
6. Ghi lại lý do nạp lại vào `docs/7-ghi-chu/`.

---

## 16. Git và commit

[Điền: nếu dự án có quy ước khác, thay thế phần này.]

### 16.1. Nhánh

- Nhánh chính: `main`. Không đẩy trực tiếp lên nhánh chính.
- Nhánh tính năng: `feat/<ten-ngan>`.
- Nhánh sửa lỗi: `fix/<ten-ngan>`.
- Nhánh tài liệu: `docs/<ten-ngan>`.

### 16.2. Commit

Định dạng: `<loại>(<phạm vi>): <mô tả ngắn>`

| Loại       | Dùng khi                        |
| ---------- | ------------------------------- |
| `feat`     | Thêm tính năng                  |
| `fix`      | Sửa lỗi                         |
| `docs`     | Tài liệu                        |
| `refactor` | Đổi cấu trúc, không đổi hành vi |
| `test`     | Thêm hoặc sửa test              |
| `chore`    | Việc vặt: cấu hình, phụ thuộc   |

Ví dụ:

- `feat(chat): thêm bước kiểm tra không có thông tin`
- `fix(knowledge): sửa gộp bảng khi ô gộp nằm ở dòng cuối`
- `docs(qt-02): tăng phiên bản 1.2, thêm luồng lỗi E7`

Mô tả ngắn không quá 72 ký tự. Phần thân (nếu cần) ghi lý do thay đổi.

### 16.3. Không được commit

- File `.env` thật.
- File có khóa, mật khẩu, token.
- File dữ liệu cá nhân của sinh viên.
- File tạm, file sinh tự động (`__pycache__`, `node_modules`, `.DS_Store`).
- Kho ChromaDB hoặc Neo4j dữ liệu thật.
- Tài liệu nguồn của trường nếu có bản quyền hạn chế [Chờ xác nhận].

---

## 17. Checklist trước khi nộp

Trước khi mở pull request hoặc báo hoàn thành, kiểm tra:

- [ ] Đọc lại file này nếu đã lâu không làm việc.
- [ ] Chạy unit test, không có lỗi.
- [ ] Chạy integration test nếu có thay đổi liên quan đến kho hoặc dịch vụ.
- [ ] Không có khóa, mật khẩu trong thay đổi.
- [ ] Không có log ghi nội dung câu hỏi ở mức INFO trở lên.
- [ ] Mỗi tiêu chí AC liên quan có test.
- [ ] Module không import chéo lớp bên trong.
- [ ] Tham số không hard-code trong mã nghiệp vụ.
- [ ] Đặc tả và tài liệu liên quan đã cập nhật, có số phiên bản mới.
- [ ] Lịch sử thay đổi đã ghi.
- [ ] Commit đúng định dạng.
- [ ] Mô tả thay đổi bằng tiếng Việt, nêu rõ ảnh hưởng tới sinh viên hoặc quản trị viên.

---

## 18. Việc không được làm mà không hỏi

- Thêm thư viện phụ thuộc mới.
- Thêm thư mục hoặc file ở cấp gốc.
- Đổi giá trị tham số trong mục 5.3 hoặc 6.
- Đổi cách chọn nhãn của router.
- Đổi quy tắc "không có thông tin".
- Xóa dữ liệu trong kho tri thức, hoặc xóa lịch sử hội thoại.
- Đổi dịch vụ bên ngoài.
- Thay đổi phân quyền.
- Tạo `CLAUDE.md` hoặc file cấu hình công cụ khác song song với `AGENTS.md`.
- Gửi dữ liệu sinh viên ra ngoài theo cách mới.
- Đổi cấu trúc thư mục `docs/`.

---

## 19. Khi không chắc

Thứ tự xử lý:

1. Đọc tài liệu liên quan trong `docs/`.
2. Tìm trong đặc tả QT xem đã có `GD` hoặc `Q` liên quan chưa.
3. Nếu chưa có, ghi câu hỏi vào mục 20 bên dưới, không tự quyết.
4. Nếu buộc phải làm ngay, chọn phương án an toàn hơn:
   - Thông báo không có thông tin thay vì trả lời phỏng đoán.
   - Dùng `Vector` thay vì dừng hệ thống.
   - Ghi log thay vì bỏ qua lỗi.
   - Dừng quy trình nạp thay vì ghi dữ liệu nghi ngờ.
5. Ghi vào mục "Ghi chú" trong báo cáo công việc: đã chọn gì, vì sao, cần xác nhận gì.

---

## 20. Câu hỏi mở đang chờ

Danh sách này cập nhật khi có quyết định. Trước khi làm việc liên quan, kiểm tra xem câu hỏi đã có câu trả lời chưa.

| Mã   | Nội dung                                    | Ảnh hưởng          | Nơi ghi      |
| ---- | ------------------------------------------- | ------------------ | ------------ |
| Q-01 | Ai yêu cầu và duyệt                         | Phạm vi, ưu tiên   | QT-01, QT-02 |
| Q-03 | Đơn vị nào được ghi khi không có thông tin  | Nội dung thông báo | QT-01        |
| Q-04 | Xử lý khi dịch vụ lỗi                       | Mục 7.2            | QT-01, QT-02 |
| Q-05 | Xử lý khi bước trích thực thể sai định dạng | Mục 6              | QT-02        |
| Q-06 | Rollback khi ghi kho lỗi giữa chừng         | Mục 6              | QT-02        |
| Q-06 | Có ghi audit câu hỏi không                  | Mục 10             | QT-01        |
| Q-07 | Phân quyền và cách kiểm tra                 | Mục 11.2           | QT-01, QT-02 |
| Q-08 | Thành phần giao diện                        | Mục 4, 5           | QT-01        |
| Q-09 | Sinh viên có bắt buộc đăng nhập             | Mục 11.2           | QT-01        |
| Q-10 | Báo cáo nạp đi đâu                          | Mục 6              | QT-02        |
| Q-11 | Nạp bằng lệnh hay giao diện                 | Mục 3              | QT-02        |
| Q-12 | `chunk_size` là ký tự hay token             | Mục 5.3, 6         | QT-02        |
| A-02 | Lưu lịch sử hội thoại ở đâu                 | Mục 5              | Kiến trúc    |
| A-03 | Ngưỡng "không có thông tin"                 | Mục 5.3            | Kiến trúc    |
| A-05 | `chunk_size` ký tự hay token                | Mục 5.3            | Kiến trúc    |
| P-03 | Pipeline nạp nằm ở đâu                      | Mục 6              | Kế hoạch     |
| P-05 | Ngưỡng chất lượng câu trả lời               | Mục 13.5           | Kế hoạch     |
| P-06 | Có môi trường staging không                 | Mục 13             | Kế hoạch     |

---

## 21. Tài liệu liên quan

| Tài liệu                                                          | Nội dung                                    |
| ----------------------------------------------------------------- | ------------------------------------------- |
| [README](README.md)                                               | Cài đặt và chạy                             |
| [Tổng quan](docs/1-tong-quan/tong-quan-chatbot-tlu.md)            | Mục tiêu, phạm vi, cho người không kỹ thuật |
| [Kế hoạch](docs/2-ky-thuat/Plan_chatbot_tlu.md)               | Giai đoạn, phụ thuộc, rủi ro                |
| [Kiến trúc](docs/2-ky-thuat/Kien_truc_chatbot_tlu.md)             | Sơ đồ, quyết định kỹ thuật (ADR)            |
| [QT-01](docs/2-ky-thuat/flows/QT1_hoi_dap_sinh_vien.md)         | Luồng hỏi đáp                               |
| [QT-02](docs/2-ky-thuat/flows/QT2_cap_nhat_tri_thuc.md) | Luồng nạp tri thức                          |

---

_Phiên bản 1.1, ngày 2026-10-13. Cập nhật khi cấu trúc, quy ước, hoặc lệnh thay đổi. Các mục có [Điền] cần bổ sung khi có mã nguồn thật._

# Tổng quan chatbot TLU

| Mục | Giá trị |
|-----|---------|
| Dự án | ChatBot (Trường Đại học Thủy Lợi) |
| Phiên bản | 1.0 - 2026-10-13 |
| Trạng thái | Đang triển khai |
| Đối tượng đọc | Ban lãnh đạo, quản lý dự án, và người mới tham gia |

## 1. Chatbot TLU là gì

Chatbot TLU là một trợ lý hỏi đáp bằng tiếng Việt cho sinh viên Trường Đại học Thủy Lợi. Sinh viên gõ câu hỏi tự nhiên, ví dụ về học phí, học bổng, ngành học hay thủ tục, và nhận câu trả lời ngay trên giao diện web.

Điểm quan trọng nhất: chatbot chỉ trả lời dựa trên tài liệu chính thức của trường. Khi tài liệu không có thông tin, chatbot nói rõ là không có và gợi ý liên hệ đơn vị phù hợp. Chatbot không tự trả lời theo kiến thức chung, để tránh đưa ra thông tin sai về quy định của trường.

## 2. Vấn đề dự án giải quyết

- Sinh viên phải tìm nhiều nơi để có một câu trả lời: trang web, file quy định, bảng học phí, và các thông báo rải rác.
- Thông tin đã có nhưng khó tra cứu nhanh, nhất là khi câu hỏi liên quan nhiều mục cùng lúc.
- Cán bộ phải trả lời lặp lại các câu hỏi giống nhau.

Chatbot giúp sinh viên tra cứu nhanh hơn, và giảm số câu hỏi lặp lại cho đơn vị hỗ trợ. Hiệu quả cụ thể cần đo sau khi triển khai (chưa có chỉ tiêu).

## 3. Ai sử dụng

| Nhóm | Dùng để làm gì |
|------|----------------|
| **Sinh viên** | Hỏi đáp về quy định, học phí, ngành học, học bổng, thủ tục |
| **Quản trị viên dữ liệu** | Đưa tài liệu mới của trường vào hệ thống, theo đợt |
| **Cán bộ phòng ban** | Vai trò đang được xác định. Có thể là nguồn cung cấp tài liệu |

## 4. Cách hoạt động, nói ngắn gọn

Hệ thống gồm hai phần chạy độc lập:

**Phần 1: Nạp tri thức.** Quản trị viên đưa tài liệu của trường vào. Hệ thống đọc, làm sạch, chia nhỏ, và lưu lại để tra cứu. Phần này chạy theo đợt, không phục vụ trực tiếp sinh viên.

**Phần 2: Hỏi đáp.** Khi sinh viên gửi câu hỏi, hệ thống:

1. Xác định loại câu hỏi: định nghĩa, quan hệ giữa các mục, hay chỉ là lời chào.
2. Tìm trong kho tài liệu những đoạn liên quan nhất.
3. Soạn câu trả lời từ các đoạn đó.
4. Ghi lại cuộc trò chuyện để trả lời tiếp các câu hỏi sau.

Nếu không tìm thấy thông tin phù hợp, hệ thống trả lời rằng chưa có thông tin và gợi ý liên hệ.

## 5. Phạm vi

**Đã đưa vào:**

- Hỏi đáp tiếng Việt trên giao diện web.
- Nạp tài liệu từ trang web của trường, file DOCX, PDF và bảng XLSX.
- Nhớ ngữ cảnh trong cùng một cuộc trò chuyện.
- Ghi nhật ký các sự kiện chính.

**Chưa đưa vào:**

- Chuyển câu hỏi cho nhân viên hỗ trợ thật.
- Cập nhật tài liệu tự động theo lịch. Hiện nạp thủ công theo đợt.
- Ứng dụng di động.
- Giao diện quản trị dữ liệu riêng.

## 6. Quyết định chính

| Vấn đề | Quyết định | Lý do ngắn gọn |
|--------|-----------|----------------|
| Nguồn trả lời | Chỉ dùng tài liệu của trường | Tránh thông tin sai về quy định |
| Khi thiếu thông tin | Nói rõ là chưa có, gợi ý liên hệ | Trung thực với sinh viên |
| Cách lưu tri thức | Hai kho: một kho theo nội dung và một kho theo quan hệ giữa các mục | Mỗi loại câu hỏi cần cách tìm khác nhau |
| Cập nhật tri thức | Nạp theo đợt, không xóa dữ liệu cũ | Có thể nạp thêm tài liệu mà không làm lại từ đầu |

Chi tiết kỹ thuật xem tại [kiến trúc](../2-ky-thuat/Kien_truc_chatbot_tlu.md).

## 7. Tiến độ và mốc

Chưa có mốc thời gian cụ thể. Kế hoạch chia thành sáu giai đoạn: chuẩn bị, nền tảng, nạp tri thức, trả lời, giao diện, kiểm thử và vận hành. Chi tiết tại [kế hoạch triển khai](../2-ky-thuat/Plan_chatbot_tlu.md).

| Giai đoạn | Nội dung | Trạng thái |
|-----------|----------|------------|
| 0. Chuẩn bị | Tài liệu, môi trường, khóa truy cập | Chưa bắt đầu hoặc đang làm (chưa xác nhận) |
| 1. Nền tảng | Cấu hình và kết nối dịch vụ | Chưa bắt đầu hoặc đang làm (chưa xác nhận) |
| 2. Nạp tri thức | Đưa tài liệu của trường vào hệ thống | Chưa bắt đầu hoặc đang làm (chưa xác nhận) |
| 3. Trả lời | Xử lý câu hỏi của sinh viên | Chưa bắt đầu hoặc đang làm (chưa xác nhận) |
| 4. Giao diện | Trang chat cho sinh viên | Chưa bắt đầu hoặc đang làm (chưa xác nhận) |
| 5. Kiểm thử và vận hành | Kiểm tra theo tiêu chí và đưa vào sử dụng | Chưa bắt đầu hoặc đang làm (chưa xác nhận) |

## 8. Rủi ro chính

- **Thông tin cũ:** tài liệu được cập nhật trên trang web nhưng chatbot chưa được nạp lại thì sẽ trả lời theo bản cũ.
- **Chất lượng câu trả lời:** chưa đo trên bộ câu hỏi thật. Cần thử nghiệm trước khi đưa vào sử dụng.
- **Chi phí dịch vụ bên ngoài:** chatbot dùng các dịch vụ trả phí theo lượt gọi. Chi phí khi có nhiều người dùng chưa được ước tính.
- **Dữ liệu gửi đi:** câu hỏi và đoạn tài liệu được gửi tới dịch vụ bên ngoài. Cần xác nhận việc này phù hợp với quy định của trường.

## 9. Việc cần quyết định

| Mã | Nội dung | Ai quyết định |
|----|----------|---------------|
| Q-01 | Ai là người yêu cầu và người phê duyệt dự án | Ban lãnh đạo |
| Q-03 | Đơn vị nào được ghi trong câu trả lời khi không có thông tin | Đơn vị hỗ trợ sinh viên |
| Q-07 | Có phân quyền cho việc nạp tài liệu không | Ban lãnh đạo |
| Q-09 | Sinh viên có bắt buộc đăng nhập không | Ban lãnh đạo |
| P-02 | Mốc thời gian mục tiêu | Ban lãnh đạo |
| P-04 | Có ai cùng phát triển ngoài người yêu cầu không | Ban lãnh đạo |

## 10. Thuật ngữ

| Thuật ngữ | Nghĩa |
|-----------|-------|
| **Tri thức** | Nội dung từ tài liệu của trường mà chatbot dùng để trả lời |
| **Nạp tri thức** | Đưa tài liệu vào hệ thống để chatbot có thể tra cứu |
| **Đặc tả quy trình (QT)** | Mô tả một việc cụ thể: ai làm, làm gì, thấy gì, và tiêu chí đạt |
| **Modulith** | Kiểu tổ chức mã nguồn: một ứng dụng, chia thành các phần theo tính năng |
| **Kho tài liệu** | Nơi lưu tài liệu đã xử lý để tra cứu nhanh |

## 11. Tài liệu liên quan

| Tài liệu | Nội dung |
|----------|----------|
| [Kế hoạch triển khai](../2-ky-thuat/Plan_chatbot_tlu.md) | Các giai đoạn, phụ thuộc, rủi ro chi tiết |
| [Kiến trúc](../2-ky-thuat/Kien_truc_chatbot_tlu.md) | Sơ đồ kỹ thuật và các quyết định |
| [QT-01: Sinh viên hỏi đáp](../2-ky-thuat/flows/QT1_hoi_dap_sinh_vien.md) | Luồng hỏi đáp và tiêu chí nghiệm thu |
| [QT-02: Nạp và cập nhật tri thức](../2-ky-thuat/flows/QT2_cap_nhat_tri_thuc.md) | Luồng nạp tri thức và tiêu chí nghiệm thu |
| [README](../../README.md) | Hướng dẫn cài đặt và chạy |

## Lịch sử thay đổi

| Phiên bản | Ngày | Thay đổi |
|-----------|------|----------|
| 1.0 | 2026-10-13 | Tạo mới từ đặc tả QT, kế hoạch, và kiến trúc |
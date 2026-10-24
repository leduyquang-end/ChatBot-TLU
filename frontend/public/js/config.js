/**
 * config.js — Nguồn sự thật duy nhất (Single Source of Truth)
 *
 * ĐÂY LÀ FILE DUY NHẤT cần sửa khi backend thay đổi endpoint, field name,
 * hay giá trị mặc định. Không hard-code bất kỳ giá trị nào ở file khác.
 *
 * Mọi key trong cấu hình API phản ánh đúng những gì backend đang trả về.
 * Khi backend thêm/đổi field, chỉ cần cập nhật ở đây.
 */

/* ─────────────────────────────────────────────
   1. API Endpoints
   Nguồn: nginx.conf → proxy /api/* → backend:8000/*
   auth routes: /auth/...   (url_prefix="/auth")
   chat routes: /chat/...   (url_prefix="/chat")
───────────────────────────────────────────── */
export const API = {
  BASE:          "/api",
  AUTH_LOGIN:    "/api/auth/login",
  USER_ME:       "/api/user/me",
  CHAT_ASK:      "/api/chat/ask",
  CHAT_HISTORY:  "/api/chat/history",   // GET ?conversation_id=...
  HEALTH:        "/api/health",
};

/* ─────────────────────────────────────────────
   2. Request field names (gửi lên backend)
   Nguồn: chat/api/routes.py → data.get("question"), data.get("conversation_id")
          auth/api/routes.py → data.get("username"), data.get("password")
───────────────────────────────────────────── */
export const REQ = {
  LOGIN_USERNAME:      "username",
  LOGIN_PASSWORD:      "password",
  ASK_QUESTION:        "question",
  ASK_CONVERSATION_ID: "conversation_id",
};

/* ─────────────────────────────────────────────
   3. Response field names (nhận từ backend)
   Nguồn: chat_pipeline.py → return dict
          auth/routes.py   → return jsonify(...)
───────────────────────────────────────────── */
export const RES = {
  // POST /api/auth/login
  LOGIN_TOKEN:         "token",
  LOGIN_USER_ID:       "user_id",
  LOGIN_ROLE:          "role",

  // GET /api/user/me
  USER_ID:             "id",
  USER_ROLE:           "role",

  // POST /api/chat/ask
  ASK_ANSWER:          "answer",
  ASK_MODE:            "mode",
  ASK_CONVERSATION_ID: "conversation_id",
  ASK_SOURCES:         "sources",       // string[] — có thể là [] nếu không tìm được

  // GET /api/chat/history
  HISTORY_TURNS:       "turns",
  HISTORY_CONV_ID:     "conversation_id",

  // Lỗi — handle_app_error → {"error": {"code": ..., "message": ...}}
  ERROR_WRAPPER:       "error",
  ERROR_CODE:          "code",
  ERROR_MESSAGE:       "message",

  // Mỗi turn trong history (conversation.py → add_turn)
  TURN_ROLE:           "role",
  TURN_CONTENT:        "content",
  TURN_ROLE_USER:      "user",
  TURN_ROLE_BOT:       "assistant",   // backend dùng "assistant", không phải "bot"
};

/* ─────────────────────────────────────────────
   4. Retrieval Mode values
   Nguồn: domain/retrieval_mode.py → RetrievalMode enum
   Nếu backend đổi tên enum value, chỉ sửa ở đây.
───────────────────────────────────────────── */
export const RETRIEVAL_MODE = {
  VECTOR: "Vector",
  GRAPH:  "Graph",
  HYBRID: "Hybrid",
  NONE:   "None",
};

/* ─────────────────────────────────────────────
   5. Giới hạn & hằng số UI — có thể thay đổi
───────────────────────────────────────────── */
export const LIMITS = {
  QUESTION_MAX_LENGTH: 2000,    // phải khớp với settings.question_max_length ở backend
  MAX_SESSIONS_STORED: 20,      // số session lưu localStorage
  HISTORY_MAX_DISPLAY: 50,      // số lượt tối đa hiển thị khi load lại
  TEXTAREA_MAX_HEIGHT: 160,     // px
  REQUEST_TIMEOUT_MS: 125_000,  // lớn hơn proxy_read_timeout 120s của nginx
};

/* ─────────────────────────────────────────────
   6. HTTP Status codes cần xử lý đặc biệt
───────────────────────────────────────────── */
export const HTTP = {
  UNAUTHORIZED:  401,
  BAD_REQUEST:   400,
  INTERNAL:      500,
};

/* ─────────────────────────────────────────────
   7. LocalStorage keys — tập trung để tránh typo
───────────────────────────────────────────── */
export const STORAGE = {
  TOKEN:           "tlu_token",
  USER_ID:         "tlu_user_id",
  ROLE:            "tlu_role",
  CONV_ID:         "tlu_conv_id",
  SESSIONS:        "tlu_sessions",
};

/* ─────────────────────────────────────────────
   8. Mock mode — bật khi backend chưa sẵn sàng
   Đặt MOCK_ENABLED = true để test UI độc lập.
   KHÔNG commit với MOCK_ENABLED = true.
───────────────────────────────────────────── */
export const MOCK = {
  ENABLED: false,

  // Các câu trả lời này chỉ mô phỏng luồng giao diện, không phải thông tin chính thức.
  LOGIN_DELAY_MS: 800,
  ASK_DELAY_MS:   1500,
  RESPONSES: {
    topics: [
      {
        terms: ["học phí", "lệ phí", "tiền học"],
        answer: "Đây là câu trả lời mô phỏng cho chủ đề học phí. Frontend chưa truy vấn backend hoặc tài liệu chính thức nên không thể xác nhận mức phí hiện hành.",
      },
      {
        terms: ["học bổng", "bổng"],
        answer: "Đây là câu trả lời mô phỏng cho chủ đề học bổng. Điều kiện, mức hỗ trợ và thời hạn cần được lấy từ thông báo chính thức của Trường.",
      },
      {
        terms: ["ngành", "đào tạo", "chương trình học"],
        answer: "Đây là câu trả lời mô phỏng cho chủ đề ngành học. Danh sách ngành và chương trình đào tạo cần được xác nhận từ dữ liệu chính thức của Trường.",
      },
      {
        terms: ["thủ tục", "xác nhận sinh viên", "giấy xác nhận", "bảo lưu"],
        answer: "Đây là câu trả lời mô phỏng cho thủ tục sinh viên. Hồ sơ, nơi tiếp nhận và thời hạn xử lý cần được xác nhận từ hướng dẫn chính thức của Trường.",
      },
      {
        terms: ["lịch học", "lịch thi", "thời khóa biểu", "thi cuối"],
        answer: "Đây là câu trả lời mô phỏng cho lịch học và lịch thi. Lịch cụ thể phụ thuộc học kỳ và lớp, nên cần tra cứu trên hệ thống chính thức của Trường.",
      },
    ],
    no_info: "Chế độ mô phỏng chưa có câu trả lời mẫu cho chủ đề này. Hãy kết nối backend thật để tra cứu dữ liệu phù hợp.",
  },
};

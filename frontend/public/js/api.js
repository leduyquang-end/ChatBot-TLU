/**
 * api.js — Fetch wrapper cách ly toàn bộ HTTP logic
 *
 * Tất cả giao tiếp với backend đi qua file này.
 * Components không bao giờ gọi fetch() trực tiếp.
 *
 * Nếu backend thay đổi auth scheme, error shape,... → chỉ sửa file này.
 */
import { API, REQ, RES, HTTP, MOCK, LIMITS } from "./config.js";

/* ─── Lỗi tùy chỉnh ─── */
export class AuthError extends Error {
  constructor(msg = "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.") {
    super(msg);
    this.name = "AuthError";
  }
}
export class ApiError extends Error {
  constructor(msg, code) {
    super(msg);
    this.name = "ApiError";
    this.code = code;
  }
}

/* ─── Token helper (dùng nội bộ, không export) ─── */
let _token = "";
export function setToken(t)   { _token = t || ""; }
export function clearToken()  { _token = ""; }
export function hasToken()    { return Boolean(_token); }

/* ─── Parse lỗi theo đúng format backend ─── */
async function _parseError(res) {
  try {
    const body = await res.json();
    const err  = body?.[RES.ERROR_WRAPPER];
    return {
      message: err?.[RES.ERROR_MESSAGE] || `HTTP ${res.status}`,
      code: err?.[RES.ERROR_CODE],
    };
  } catch {
    return { message: `HTTP ${res.status}`, code: "" };
  }
}

/* ─── Core fetch với timeout & error handling ─── */
async function _fetch(url, opts = {}, { requiresAuth = true } = {}) {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), LIMITS.REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      ...opts,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(_token ? { Authorization: `Bearer ${_token}` } : {}),
        ...(opts.headers || {}),
      },
    });

    if (res.status === HTTP.UNAUTHORIZED) {
      const { message, code } = await _parseError(res);
      if (requiresAuth) {
        clearToken();
        throw new AuthError(message);
      }
      throw new ApiError(message, code);
    }

    if (!res.ok) {
      const { message, code } = await _parseError(res);
      throw new ApiError(message, code);
    }

    try {
      return await res.json();
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new ApiError("Máy chủ trả về dữ liệu không đúng định dạng.");
      }
      throw error;
    }
  } catch (e) {
    if (e.name === "AbortError") throw new ApiError("Yêu cầu quá thời gian. Vui lòng thử lại.");
    if (e instanceof TypeError) {
      throw new ApiError("Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối và thử lại.");
    }
    throw e;
  } finally {
    clearTimeout(tid);
  }
}

/* ═══════════════════════════════════════════════
   PUBLIC API — giao tiếp với các route backend
═══════════════════════════════════════════════ */

/**
 * Đăng nhập.
 * @returns {{ token, user_id, role }}
 */
export async function apiLogin(username, password) {
  if (MOCK.ENABLED) {
    await _delay(MOCK.LOGIN_DELAY_MS);
    if (username === "sinhvien01" && password === "demo-password") {
      return { [RES.LOGIN_TOKEN]: "mock-token", [RES.LOGIN_USER_ID]: "u001", [RES.LOGIN_ROLE]: "student" };
    }
    throw new ApiError("Tài khoản hoặc mật khẩu không đúng");
  }

  return _fetch(API.AUTH_LOGIN, {
    method: "POST",
    body: JSON.stringify({
      [REQ.LOGIN_USERNAME]: username,
      [REQ.LOGIN_PASSWORD]: password,
    }),
  }, { requiresAuth: false });
}

/**
 * Lấy danh tính và vai trò đã được backend xác thực.
 * @returns {{ id, role }}
 */
export async function apiCurrentUser() {
  if (MOCK.ENABLED) {
    return { [RES.USER_ID]: "u001", [RES.USER_ROLE]: "student" };
  }

  return _fetch(API.USER_ME, { method: "GET" });
}

/**
 * Gửi câu hỏi.
 * @returns {{ answer, mode, conversation_id, sources[] }}
 *
 * Lưu ý: `sources` có thể là mảng rỗng [] nếu backend chưa implement
 * hoặc không tìm được tài liệu. Frontend phải xử lý gracefully.
 */
export async function apiAsk(question, conversationId) {
  if (question.length > LIMITS.QUESTION_MAX_LENGTH) {
    throw new ApiError(`Câu hỏi tối đa ${LIMITS.QUESTION_MAX_LENGTH} ký tự`);
  }

  if (MOCK.ENABLED) {
    await _delay(MOCK.ASK_DELAY_MS);
    const normalizedQuestion = question.toLocaleLowerCase("vi");
    const topic = MOCK.RESPONSES.topics.find(({ terms }) =>
      terms.some(term => normalizedQuestion.includes(term))
    );
    return {
      [RES.ASK_ANSWER]: topic?.answer ?? MOCK.RESPONSES.no_info,
      [RES.ASK_MODE]: "None",
      [RES.ASK_CONVERSATION_ID]: conversationId,
      [RES.ASK_SOURCES]: [],
    };
  }

  return _fetch(API.CHAT_ASK, {
    method: "POST",
    body: JSON.stringify({
      [REQ.ASK_QUESTION]:        question,
      [REQ.ASK_CONVERSATION_ID]: conversationId,
    }),
  });
}

/**
 * Lấy lịch sử hội thoại.
 * @returns {{ conversation_id, turns: [{role, content}] }}
 *
 * QUAN TRỌNG: Mỗi turn có role = "user" | "assistant" (không phải "bot")
 * Xem: domain/conversation.py → add_turn()
 */
export async function apiHistory(conversationId) {
  if (MOCK.ENABLED) {
    return { [RES.HISTORY_CONV_ID]: conversationId, [RES.HISTORY_TURNS]: [] };
  }

  return _fetch(`${API.CHAT_HISTORY}?${REQ.ASK_CONVERSATION_ID}=${encodeURIComponent(conversationId)}`);
}

/**
 * Kiểm tra backend có sẵn không (dùng khi app khởi động).
 * @returns {boolean}
 */
export async function apiHealthCheck() {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(API.HEALTH, { signal: controller.signal });
    return response.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(tid);
  }
}

function _delay(ms) { return new Promise(r => setTimeout(r, ms)); }

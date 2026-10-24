/**
 * store.js — Quản lý state & localStorage tập trung
 *
 * Không có component nào đọc/ghi localStorage trực tiếp.
 * Mọi thứ đi qua đây để dễ trace và không bị typo key.
 */
import { STORAGE, LIMITS, RES } from "./config.js";

/* ─── Session item lưu vào localStorage ─── */
// { id: string, title: string, ts: number }

export const store = {
  /* Token */
  getToken:   () => localStorage.getItem(STORAGE.TOKEN)   || "",
  setToken:   (v) => localStorage.setItem(STORAGE.TOKEN, v),
  clearToken: ()  => localStorage.removeItem(STORAGE.TOKEN),

  /* User info */
  getUserId:   () => localStorage.getItem(STORAGE.USER_ID) || "",
  setUserId:   (v) => localStorage.setItem(STORAGE.USER_ID, v),
  getRole:     () => localStorage.getItem(STORAGE.ROLE)    || "",
  setRole:     (v) => localStorage.setItem(STORAGE.ROLE, v),

  /* Conversation ID hiện tại */
  getConvId:   () => localStorage.getItem(STORAGE.CONV_ID) || _newUUID(),
  setConvId:   (v) => localStorage.setItem(STORAGE.CONV_ID, v),
  clearConvId: ()  => localStorage.removeItem(STORAGE.CONV_ID),

  /* Danh sách session (sidebar history) */
  getSessions() {
    const key = _sessionsKey();
    if (!key) return [];
    try {
      const sessions = JSON.parse(localStorage.getItem(key) || "[]");
      return Array.isArray(sessions)
        ? sessions
          .filter(session =>
            session &&
            typeof session.id === "string" &&
            typeof session.title === "string" &&
            Number.isFinite(session.ts)
          )
          .slice(0, LIMITS.MAX_SESSIONS_STORED)
        : [];
    }
    catch { return []; }
  },
  saveSession(id, title) {
    const key = _sessionsKey();
    if (!key) return;
    const sessions = this.getSessions().filter(s => s.id !== id);
    sessions.unshift({ id, title: _truncate(title, 60), ts: Date.now() });
    if (sessions.length > LIMITS.MAX_SESSIONS_STORED) sessions.pop();
    localStorage.setItem(key, JSON.stringify(sessions));
  },
  removeSession(id) {
    const key = _sessionsKey();
    if (!key) return;
    const sessions = this.getSessions().filter(s => s.id !== id);
    localStorage.setItem(key, JSON.stringify(sessions));
  },

  /* Xóa tất cả khi logout */
  clearAll() {
    [STORAGE.TOKEN, STORAGE.USER_ID, STORAGE.ROLE, STORAGE.CONV_ID].forEach(k =>
      localStorage.removeItem(k)
    );
    // Giữ lại SESSIONS để user thấy lịch sử khi đăng nhập lại
  },

  /**
   * Chuẩn hoá response từ backend → shape ổn định cho UI.
   *
   * Mục đích: nếu backend thêm/đổi field, chỉ cần sửa hàm này,
   * không cần đụng vào code render.
   *
   * Đầu ra luôn có đủ các field, kể cả khi backend thiếu.
   */
  normalizeAskResponse(raw) {
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      throw new Error("Phản hồi hỏi đáp từ máy chủ không đúng định dạng.");
    }

    const answer = raw[RES.ASK_ANSWER];
    if (typeof answer !== "string" || !answer.trim()) {
      throw new Error("Phản hồi hỏi đáp không có nội dung câu trả lời hợp lệ.");
    }

    const mode = raw[RES.ASK_MODE];
    const conversationId = raw[RES.ASK_CONVERSATION_ID];
    const rawSources = raw[RES.ASK_SOURCES];
    if (mode != null && typeof mode !== "string") {
      throw new Error("Trường chế độ truy xuất trong phản hồi không hợp lệ.");
    }
    if (conversationId != null && typeof conversationId !== "string") {
      throw new Error("Mã cuộc trò chuyện trong phản hồi không hợp lệ.");
    }
    if (rawSources != null && !Array.isArray(rawSources)) {
      throw new Error("Danh sách nguồn trong phản hồi không hợp lệ.");
    }

    return {
      answer:         answer,
      mode:           mode ?? "",
      conversationId: conversationId ?? "",
      sources:        Array.isArray(rawSources)
        ? rawSources
          .map(source => {
            if (typeof source === "string") return source;
            if (!source || typeof source !== "object") return "";
            return source.title || source.name || source.document || source.source || "";
          })
          .filter(source => typeof source === "string" && source.trim())
        : [],
    };
  },
  normalizeHistoryResponse(raw) {
    const turns = Array.isArray(raw) ? raw : raw?.[RES.HISTORY_TURNS];
    if (!Array.isArray(turns)) {
      throw new Error("Phản hồi lịch sử từ máy chủ không đúng định dạng.");
    }
    return turns.map(turn => {
      const role = turn?.[RES.TURN_ROLE];
      if (role !== RES.TURN_ROLE_USER && role !== RES.TURN_ROLE_BOT) return null;
      return {
        role,
        content: turn?.[RES.TURN_CONTENT] ?? "",
      };
    }).filter(turn => turn && typeof turn.content === "string" && turn.content.trim());
  },
};

function _sessionsKey() {
  const userId = store.getUserId();
  return userId ? `${STORAGE.SESSIONS}:${encodeURIComponent(userId)}` : "";
}

function _newUUID() {
  const id = crypto.randomUUID();
  store.setConvId(id);
  return id;
}
function _truncate(str, len) {
  return str.length > len ? str.slice(0, len - 1) + "…" : str;
}

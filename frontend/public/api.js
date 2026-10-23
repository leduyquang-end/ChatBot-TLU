const API_BASE = "/api";

const KEYS = {
  access: "tlu.access",
  refresh: "tlu.refresh",
  conversation: "tlu.cid",
  user: "tlu.uid",
};

const DEFAULT_MESSAGES = {
  400: "Dữ liệu chưa hợp lệ.",
  401: "Bạn cần đăng nhập để tiếp tục.",
  403: "Bạn không có quyền thực hiện thao tác này.",
  404: "Không tìm thấy dữ liệu.",
  409: "Dữ liệu đã thay đổi, hãy thử lại.",
  429: "Bạn thao tác quá nhanh, vui lòng thử lại sau.",
  500: "Hệ thống đang gặp sự cố. Vui lòng thử lại sau.",
};

export class ApiError extends Error {
  constructor(message, status = 0, code = "") {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

function newConversationId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `c-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const session = {
  get access() {
    return localStorage.getItem(KEYS.access) || "";
  },
  get refresh() {
    return localStorage.getItem(KEYS.refresh) || "";
  },
  get conversationId() {
    let id = localStorage.getItem(KEYS.conversation);
    if (!id) {
      id = newConversationId();
      localStorage.setItem(KEYS.conversation, id);
    }
    return id;
  },
  setConversationId(id) {
    if (id) localStorage.setItem(KEYS.conversation, id);
  },
  resetConversation() {
    localStorage.setItem(KEYS.conversation, newConversationId());
  },
  setUser(userId) {
    if (!userId) return;
    const previous = localStorage.getItem(KEYS.user);
    if (previous && previous !== userId) this.resetConversation();
    localStorage.setItem(KEYS.user, userId);
  },
  save(data) {
    if (data?.token) localStorage.setItem(KEYS.access, data.token);
    if (data?.refresh_token) localStorage.setItem(KEYS.refresh, data.refresh_token);
  },
  hasSession() {
    return Boolean(this.access);
  },
  clear() {
    for (const key of Object.values(KEYS)) localStorage.removeItem(key);
  },
};

async function rawRequest(path, { method = "GET", body, token, signal } = {}) {
  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(API_BASE + path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError("Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.", 0, "NETWORK");
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.error?.message || DEFAULT_MESSAGES[response.status] || "Yêu cầu không thành công.";
    throw new ApiError(message, response.status, data?.error?.code || "");
  }
  return data;
}

let refreshPromise = null;

function refreshSession() {
  const refreshToken = session.refresh;
  if (!refreshToken) {
    session.clear();
    return Promise.reject(new ApiError("Phiên đăng nhập đã hết hạn.", 401, "UNAUTHORIZED"));
  }
  if (!refreshPromise) {
    refreshPromise = rawRequest("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    })
      .then((data) => {
        session.save(data);
        return data;
      })
      .catch((error) => {
        session.clear();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function apiRequest(path, options = {}) {
  const { auth = true, retryOnUnauthorized = true, ...rest } = options;
  try {
    return await rawRequest(path, { ...rest, token: auth ? session.access : "" });
  } catch (error) {
    if (auth && retryOnUnauthorized && error.status === 401) {
      const refreshed = await refreshSession();
      return rawRequest(path, { ...rest, token: refreshed.token });
    }
    throw error;
  }
}

export const api = {
  login(username, password) {
    return rawRequest("/auth/login", { method: "POST", body: { username, password } });
  },
  logout(refreshToken) {
    return rawRequest("/auth/logout", { method: "POST", body: { refresh_token: refreshToken } });
  },
  me() {
    return apiRequest("/user/me");
  },
  updateMe(fullName) {
    return apiRequest("/user/me", { method: "PUT", body: { full_name: fullName } });
  },
  changePassword(oldPassword, newPassword) {
    return apiRequest("/user/change-password", {
      method: "POST",
      body: { old_password: oldPassword, new_password: newPassword },
    });
  },
  listUsers() {
    return apiRequest("/user");
  },
  ask(question, conversationId) {
    return apiRequest("/chat/ask", {
      method: "POST",
      body: { question, conversation_id: conversationId },
    });
  },
  history(conversationId) {
    return apiRequest(`/chat/history?conversation_id=${encodeURIComponent(conversationId)}`);
  },
};

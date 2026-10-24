/**
 * app.js — Controller chính, kết nối api.js + store.js + ui.js
 *
 * Đây là file "controller" duy nhất. Nó:
 * - Lắng nghe DOM events
 * - Gọi API qua api.js
 * - Cập nhật state qua store.js
 * - Render kết quả qua ui.js
 *
 * Không có raw fetch() hay localStorage ở đây.
 */
import { apiLogin, apiCurrentUser, apiAsk, apiHistory, apiHealthCheck, setToken, clearToken, AuthError } from "./api.js";
import { store } from "./store.js";
import {
  showToast,
  createMessageBubble,
  createTypingIndicator,
  createSessionItem,
} from "./ui.js";
import { LIMITS, RES, MOCK } from "./config.js";

/* ════════════════════════════════════════════
   DOM refs — tập trung để dễ tìm
════════════════════════════════════════════ */
const $ = (id) => document.getElementById(id);

const DOM = {
  // Auth overlay
  authOverlay:    $("authOverlay"),
  loginForm:      $("loginForm"),
  usernameInput:  $("username"),
  passwordInput:  $("password"),
  loginBtn:       $("loginBtn"),
  loginError:     $("loginError"),

  // App shell
  appShell:       $("appShell"),
  sidebarToggle:  $("sidebarToggle"),
  sidebar:        $("sidebar"),
  sidebarOverlay: $("sidebarOverlay"),
  sessionList:    $("sessionList"),
  newChatBtn:     $("newChatBtn"),
  logoutBtn:      $("logoutBtn"),

  // Chat area
  feedArea:       $("feedArea"),
  emptyState:     $("emptyState"),
  chipArea:       $("chipArea"),
  backendStatus:  $("backendStatus"),
  backendStatusLabel: $("backendStatusLabel"),
  typingSlot:     null,            // sẽ gán khi typing indicator thêm vào DOM

  // Composer
  composer:       $("composer"),
  questionInput:  $("questionInput"),
  charCount:      $("charCount"),
  sendBtn:        $("sendBtn"),

  // Toast area
  toastArea:      $("toastArea"),
};

/* ════════════════════════════════════════════
   Suggest chips — câu hỏi thường gặp
   Thêm/bớt chip ở đây, không ảnh hưởng gì khác
════════════════════════════════════════════ */
const CHIPS = [
  { icon: "💰", label: "Học phí",            query: "Học phí năm học này là bao nhiêu?" },
  { icon: "🏅", label: "Học bổng",           query: "Các loại học bổng dành cho sinh viên?" },
  { icon: "📚", label: "Ngành học",          query: "Trường có những ngành đào tạo nào?" },
  { icon: "📋", label: "Thủ tục hành chính", query: "Thủ tục xin xác nhận sinh viên?" },
  { icon: "📅", label: "Lịch học & thi",     query: "Khi nào bắt đầu thi cuối học kỳ?" },
];

let sendRequestId = 0;
let historyRequestId = 0;

/* ════════════════════════════════════════════
   App init
════════════════════════════════════════════ */
function init() {
  bindGlobalEvents();

  const savedToken = store.getToken();
  const savedUserId = store.getUserId();
  if (savedToken && savedUserId) {
    setToken(savedToken);
    restoreAuthSession(savedUserId);
  } else {
    if (savedToken) {
      clearToken();
      store.clearAll();
    }
    enterAuth();
  }

  // Mock mode badge
  if (MOCK.ENABLED) {
    const badge = document.createElement("div");
    badge.className = "mock-badge";
    badge.textContent = "MOCK MODE";
    document.body.appendChild(badge);
  }
}

async function restoreAuthSession(savedUserId) {
  try {
    const user = await apiCurrentUser();
    if (user[RES.USER_ID] !== savedUserId || user[RES.USER_ROLE] !== "student") {
      handleLogout();
      showToast("Tài khoản này không được phép sử dụng chức năng hỏi đáp sinh viên.", "error");
      return;
    }

    enterApp();
    restoreCurrentSession();
  } catch (err) {
    clearToken();
    if (err instanceof AuthError) {
      store.clearAll();
      enterAuth();
      showToast(err.message, "error");
      return;
    }

    enterAuth();
    showToast(
      `Không thể xác minh phiên đăng nhập${err?.message ? `: ${err.message}` : "."} Vui lòng thử lại.`,
      "error",
    );
  }
}

/* ════════════════════════════════════════════
   Auth flow
════════════════════════════════════════════ */
function enterAuth() {
  DOM.authOverlay.hidden = false;
  DOM.appShell.hidden = true;
  DOM.usernameInput.focus();
  setLoginError("");
}

function enterApp() {
  DOM.authOverlay.hidden = true;
  DOM.appShell.hidden = false;
  renderSessions();
  renderChips();
  showFeed(false);   // hiện empty state
  DOM.questionInput.focus();
  refreshBackendStatus();
}

async function refreshBackendStatus() {
  DOM.backendStatus.classList.remove("chat-header-status--offline");
  DOM.backendStatusLabel.textContent = "Đang kiểm tra dịch vụ...";
  const healthy = MOCK.ENABLED || await apiHealthCheck();
  DOM.backendStatus.classList.toggle("chat-header-status--offline", !healthy);
  DOM.backendStatusLabel.textContent = healthy
    ? "Sẵn sàng hỗ trợ"
    : "Chưa kết nối được dịch vụ";
}

async function restoreCurrentSession() {
  const requestId = ++historyRequestId;
  const conversationId = store.getConvId();

  try {
    const raw = await apiHistory(conversationId);
    if (requestId !== historyRequestId || conversationId !== store.getConvId()) return;

    const turns = store.normalizeHistoryResponse(raw).slice(-LIMITS.HISTORY_MAX_DISPLAY);
    if (!turns.length) {
      if (store.getSessions().some(session => session.id === conversationId)) {
        showToast("Lịch sử chưa có trên máy chủ hiện tại; bạn vẫn có thể bắt đầu cuộc trò chuyện mới.", "info");
      }
      return;
    }

    clearFeed();
    showFeed(true);
    turns.forEach(turn => appendMessage({ role: turn.role, content: turn.content }));

    if (!store.getSessions().some(session => session.id === conversationId)) {
      const firstQuestion = turns.find(turn => turn.role !== RES.TURN_ROLE_BOT);
      if (firstQuestion) store.saveSession(conversationId, firstQuestion.content);
    }
    renderSessions();
  } catch (err) {
    if (requestId !== historyRequestId) return;
    if (err instanceof AuthError) {
      handleLogout();
      showToast(err.message, "error");
      return;
    }
    showToast(
      `Không thể khôi phục lịch sử hội thoại${err?.message ? `: ${err.message}` : "."} Bạn vẫn có thể bắt đầu trao đổi mới.`,
      "info",
    );
  }
}

async function handleLogin(e) {
  e?.preventDefault();
  if (DOM.loginBtn.disabled) return;

  const username = DOM.usernameInput.value.trim();
  const password = DOM.passwordInput.value;
  if (!username || !password) {
    setLoginError("Vui lòng nhập tài khoản và mật khẩu.");
    return;
  }

  setLoginLoading(true);
  try {
    const data = await apiLogin(username, password);
    const token  = data[RES.LOGIN_TOKEN];
    const userId = data[RES.LOGIN_USER_ID];
    if (typeof token !== "string" || !token || typeof userId !== "string" || !userId) {
      throw new Error("Phản hồi đăng nhập thiếu token hoặc mã người dùng.");
    }

    setToken(token);
    const user = await apiCurrentUser();
    if (user[RES.USER_ID] !== userId || user[RES.USER_ROLE] !== "student") {
      clearToken();
      setLoginError("Tài khoản này không được phép sử dụng chức năng hỏi đáp sinh viên.");
      return;
    }

    store.setToken(token);
    store.setUserId(userId);
    store.setRole(user[RES.USER_ROLE]);

    // Tạo conversation mới
    const convId = crypto.randomUUID();
    store.setConvId(convId);

    DOM.usernameInput.value = "";
    DOM.passwordInput.value = "";
    enterApp();
  } catch (err) {
    setLoginError(err instanceof AuthError ? err.message : (err.message || "Đăng nhập thất bại."));
  } finally {
    setLoginLoading(false);
  }
}

function handleLogout() {
  sendRequestId += 1;
  historyRequestId += 1;
  clearToken();
  store.clearAll();
  clearFeed();
  enterAuth();
}

function setLoginError(msg) {
  DOM.loginError.textContent = msg;
  DOM.loginError.hidden = !msg;
}
function setLoginLoading(on) {
  DOM.loginBtn.disabled = on;
  DOM.loginBtn.querySelector("span").textContent = on ? "Đang đăng nhập…" : "Đăng nhập";
  DOM.loginBtn.querySelector(".btn-spinner").hidden = !on;
}

/* ════════════════════════════════════════════
   Chat flow
════════════════════════════════════════════ */
async function handleSend(e) {
  e?.preventDefault();
  if (DOM.sendBtn.disabled) return;

  const question = DOM.questionInput.value.trim();
  if (!/[\p{L}\p{N}]/u.test(question)) {
    showToast("Vui lòng nhập câu hỏi có nội dung.", "error");
    DOM.questionInput.focus();
    return;
  }

  DOM.questionInput.value = "";
  updateCharCount();
  showFeed(true);
  DOM.chipArea.hidden = true;    // ẩn chips sau câu hỏi đầu tiên

  const userMessage = appendMessage({ role: "user", content: question });
  showTyping(true);
  setSendDisabled(true);

  const convId = store.getConvId();
  const requestId = ++sendRequestId;
  historyRequestId += 1;

  try {
    const raw  = await apiAsk(question, convId);
    const data = store.normalizeAskResponse(raw);
    if (requestId !== sendRequestId || convId !== store.getConvId()) return;

    // Nếu server trả về conversation_id khác (ví dụ: server tạo mới), cập nhật
    if (data.conversationId && data.conversationId !== convId) {
      store.setConvId(data.conversationId);
    }

    try {
      store.saveSession(data.conversationId || convId, question);
    } catch {
      showToast("Đã nhận câu trả lời nhưng không thể lưu phiên vào lịch sử trên trình duyệt.", "info");
    }
    renderSessions();

    showTyping(false);
    appendMessage({
      role:      RES.TURN_ROLE_BOT,
      content:   data.answer,
      mode:      data.mode,
      sources:   data.sources,
    });
  } catch (err) {
    if (requestId !== sendRequestId || convId !== store.getConvId()) return;
    showTyping(false);
    if (err instanceof AuthError) {
      handleLogout();
      showToast(err.message, "error");
    } else {
      userMessage.remove();
      DOM.questionInput.value = question;
      DOM.questionInput.dispatchEvent(new Event("input", { bubbles: true }));
      if (DOM.feedArea.children.length === 0) {
        showFeed(false);
        renderChips();
      }
      showToast(`${err.message || "Không gửi được câu hỏi."} Câu hỏi đã được giữ lại để bạn thử lại.`, "error");
    }
  } finally {
    if (requestId === sendRequestId) {
      setSendDisabled(false);
      DOM.questionInput.focus();
    }
  }
}

/* ════════════════════════════════════════════
   Session sidebar
════════════════════════════════════════════ */
function renderSessions() {
  const sessions = store.getSessions();
  const activeId = store.getConvId();
  DOM.sessionList.innerHTML = "";
  if (!sessions.length) {
    DOM.sessionList.innerHTML = `<li class="session-empty">Chưa có cuộc trò chuyện nào</li>`;
    return;
  }
  sessions.forEach(s => {
    const li = createSessionItem({
      id:       s.id,
      title:    s.title,
      ts:       s.ts,
      isActive: s.id === activeId,
      onClick:  loadSession,
      onDelete: deleteSession,
    });
    DOM.sessionList.appendChild(li);
  });
}

async function loadSession(id) {
  if (id === store.getConvId()) {
    closeSidebar();
    return;
  }
  const requestId = ++historyRequestId;
  sendRequestId += 1;
  store.setConvId(id);
  setSendDisabled(false);
  clearFeed();
  showFeed(false);
  closeSidebar();

  // Load lịch sử từ server
  showTyping(true);
  try {
    const raw   = await apiHistory(id);
    if (requestId !== historyRequestId || id !== store.getConvId()) return;
    const turns = store.normalizeHistoryResponse(raw);
    if (!turns.length) {
      showFeed(false);
      renderChips();
      renderSessions();
      showToast("Không tìm thấy lịch sử của cuộc trò chuyện này trên máy chủ.", "info");
      return;
    }
    showFeed(turns.length > 0);
    turns.slice(-LIMITS.HISTORY_MAX_DISPLAY).forEach(t => appendMessage({ role: t.role, content: t.content }));
    renderSessions();
  } catch (err) {
    if (requestId !== historyRequestId) return;
    if (err instanceof AuthError) {
      handleLogout();
      showToast(err.message, "error");
    } else {
      showToast("Không thể tải lịch sử. " + (err.message || ""), "error");
    }
  } finally {
    if (requestId === historyRequestId) showTyping(false);
  }
}

function deleteSession(id) {
  store.removeSession(id);
  if (id === store.getConvId()) {
    startNewChat();
  } else {
    renderSessions();
  }
  showToast("Đã xóa cuộc trò chuyện khỏi danh sách trên trình duyệt; dữ liệu máy chủ không bị xóa.", "info");
}

function startNewChat() {
  sendRequestId += 1;
  historyRequestId += 1;
  setSendDisabled(false);
  showTyping(false);
  const convId = crypto.randomUUID();
  store.setConvId(convId);
  clearFeed();
  showFeed(false);
  renderChips();
  renderSessions();
  closeSidebar();
  DOM.questionInput.focus();
}

/* ════════════════════════════════════════════
   Feed helpers
════════════════════════════════════════════ */
function appendMessage(opts) {
  const el = createMessageBubble(opts);
  DOM.feedArea.appendChild(el);
  scrollToBottom();
  return el;
}

function showTyping(on) {
  const existing = $("typingIndicator");
  if (on && !existing) {
    DOM.feedArea.appendChild(createTypingIndicator());
    scrollToBottom();
  } else if (!on && existing) {
    existing.remove();
  }
}

function showFeed(hasMessages) {
  DOM.emptyState.hidden = hasMessages;
  DOM.feedArea.dataset.empty = hasMessages ? "false" : "true";
}

function clearFeed() {
  DOM.feedArea.innerHTML = "";
  DOM.chipArea.hidden = false;
}

function scrollToBottom() {
  // Chỉ scroll nếu user đang ở gần đáy (không cắt ngang khi đang đọc lên)
  const feed = DOM.feedArea;
  const threshold = 150;
  const nearBottom = feed.scrollHeight - feed.scrollTop - feed.clientHeight < threshold;
  if (nearBottom || $("typingIndicator")) {
    feed.scrollTop = feed.scrollHeight;
  }
}

/* ════════════════════════════════════════════
   Chips
════════════════════════════════════════════ */
function renderChips() {
  DOM.chipArea.innerHTML = "";
  DOM.chipArea.hidden = false;
  CHIPS.forEach(chip => {
    const btn = document.createElement("button");
    btn.className = "chip";
    btn.type = "button";
    btn.innerHTML = `${chip.icon} <span>${chip.label}</span>`;
    btn.addEventListener("click", () => {
      DOM.questionInput.value = chip.query;
      updateCharCount();
      DOM.composer.dispatchEvent(new Event("submit", { bubbles: true }));
    });
    DOM.chipArea.appendChild(btn);
  });
}

/* ════════════════════════════════════════════
   Sidebar toggle
════════════════════════════════════════════ */
function toggleSidebar() {
  const open = DOM.sidebar.classList.toggle("sidebar--open");
  DOM.sidebarOverlay.hidden = !open;
}
function closeSidebar() {
  DOM.sidebar.classList.remove("sidebar--open");
  DOM.sidebarOverlay.hidden = true;
}

/* ════════════════════════════════════════════
   Composer helpers
════════════════════════════════════════════ */
function setSendDisabled(on) {
  DOM.sendBtn.disabled = on;
  DOM.questionInput.disabled = on;
  DOM.composer.setAttribute("aria-busy", String(on));
  DOM.sendBtn.setAttribute("aria-label", on ? "Đang gửi câu hỏi" : "Gửi câu hỏi");
}

function updateCharCount() {
  const len = DOM.questionInput.value.length;
  DOM.charCount.textContent = `${len}/${LIMITS.QUESTION_MAX_LENGTH}`;
  DOM.charCount.classList.toggle("char-count--warn", len > LIMITS.QUESTION_MAX_LENGTH * 0.85);
}

/* ════════════════════════════════════════════
   Global event binding
════════════════════════════════════════════ */
function bindGlobalEvents() {
  // Login
  DOM.loginForm.addEventListener("submit", handleLogin);
  DOM.passwordInput.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); DOM.loginForm.dispatchEvent(new Event("submit")); }
  });

  // Logout & new chat
  DOM.logoutBtn.addEventListener("click", handleLogout);
  DOM.newChatBtn.addEventListener("click", startNewChat);

  // Sidebar
  DOM.sidebarToggle.addEventListener("click", toggleSidebar);
  DOM.sidebarOverlay.addEventListener("click", closeSidebar);

  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if (DOM.sidebar.classList.contains("sidebar--open")) closeSidebar();
  });

  // Composer
  DOM.composer.addEventListener("submit", handleSend);
  DOM.questionInput.addEventListener("input", () => {
    updateCharCount();
    // Auto-resize textarea
    DOM.questionInput.style.height = "auto";
    DOM.questionInput.style.height =
      Math.min(DOM.questionInput.scrollHeight, LIMITS.TEXTAREA_MAX_HEIGHT) + "px";
  });
  // Enter gửi, Shift+Enter xuống dòng
  DOM.questionInput.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      DOM.composer.dispatchEvent(new Event("submit", { bubbles: true }));
    }
  });
}

/* ════════════════════════════════════════════
   Start
════════════════════════════════════════════ */
init();

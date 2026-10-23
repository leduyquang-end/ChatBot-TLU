import { api, session } from "./api.js";

const MODE_LABELS = {
  Vector: "Tra cứu nội dung",
  Graph: "Tra cứu quan hệ",
  Hybrid: "Kết hợp",
  None: "Không truy cập",
};

const ROLE_LABELS = {
  student: "Sinh viên",
  admin: "Quản trị viên",
};

const SAMPLE_QUESTIONS = [
  "Điều kiện xét học bổng là gì?",
  "Học phần nào phải học trước môn X?",
  "Học phí học kỳ này bao nhiêu?",
];

const state = {
  me: null,
  busy: false,
  toastTimer: null,
};

const $ = (id) => document.getElementById(id);

function showLogin(message = "") {
  $("app-view").hidden = true;
  $("login-view").hidden = false;
  setAlert($("login-error"), message, "error");
  $("username").focus();
}

function showApp() {
  $("login-view").hidden = true;
  $("app-view").hidden = false;
}

function setAlert(element, message, kind) {
  element.textContent = message || "";
  element.classList.toggle("alert-error", kind === "error");
  element.classList.toggle("alert-success", kind === "success");
  element.hidden = !message;
}

function toast(message, kind = "success") {
  const box = $("toast");
  box.textContent = message;
  box.className = `toast toast-${kind}`;
  box.hidden = false;
  if (state.toastTimer) clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    box.hidden = true;
  }, 4000);
}

function renderIdentity() {
  const me = state.me;
  $("me-name").textContent = me.full_name;
  $("me-role").textContent = ROLE_LABELS[me.role] || me.role;
  $("tab-admin").hidden = me.role !== "admin";
  $("profile-username").value = me.username;
  $("profile-fullname").value = me.full_name;
}

function switchView(view) {
  for (const name of ["chat", "profile", "admin"]) {
    $(`view-${name}`).hidden = name !== view;
  }
  for (const tab of document.querySelectorAll(".tab")) {
    const active = tab.dataset.view === view;
    tab.classList.toggle("active", active);
    if (active) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  }
  if (view === "admin") loadUsers();
  if (view === "chat") $("question").focus();
}

function resetChat() {
  $("messages").replaceChildren();
  setAlert($("chat-error"), "", "error");
}

function renderWelcome() {
  resetChat();
  const row = document.createElement("div");
  row.className = "msg bot";

  const bubble = document.createElement("div");
  bubble.className = "bubble";

  const title = document.createElement("strong");
  title.textContent = "Xin chào! Mình có thể giúp gì cho bạn?";
  const text = document.createElement("p");
  text.textContent =
    "Bạn có thể hỏi về quy định, học phí, ngành học, học bổng, thủ tục… Câu trả lời dựa trên tài liệu đã nạp của trường.";

  const samples = document.createElement("div");
  samples.className = "samples";
  for (const question of SAMPLE_QUESTIONS) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "sample-chip";
    chip.dataset.question = question;
    chip.textContent = question;
    samples.appendChild(chip);
  }

  bubble.append(title, text, samples);
  row.appendChild(bubble);
  $("messages").appendChild(row);
}

function addMessage({ text, role, mode, sources = [] }) {
  const row = document.createElement("div");
  row.className = `msg ${role === "user" ? "user" : "bot"}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  row.appendChild(bubble);

  if (mode || sources.length) {
    const meta = document.createElement("div");
    meta.className = "msg-meta";

    if (mode) {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = MODE_LABELS[mode] || mode;
      meta.appendChild(chip);
    }

    if (sources.length) {
      const details = document.createElement("details");
      details.className = "sources";
      const summary = document.createElement("summary");
      summary.textContent = `Nguồn (${sources.length})`;
      const list = document.createElement("ul");
      for (const source of sources) {
        const item = document.createElement("li");
        item.textContent = source;
        list.appendChild(item);
      }
      details.append(summary, list);
      meta.appendChild(details);
    }

    row.appendChild(meta);
  }

  $("messages").appendChild(row);
  $("messages").scrollTop = $("messages").scrollHeight;
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "msg bot typing";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  for (let index = 0; index < 3; index += 1) {
    const dot = document.createElement("span");
    dot.className = "dot";
    bubble.appendChild(dot);
  }

  row.appendChild(bubble);
  $("messages").appendChild(row);
  $("messages").scrollTop = $("messages").scrollHeight;
  return row;
}

function setComposerBusy(busy) {
  $("send-btn").disabled = busy;
  $("send-btn").textContent = busy ? "Đang gửi…" : "Gửi";
}

function handleAuthFailure(message) {
  session.clear();
  state.me = null;
  state.busy = false;
  resetChat();
  setComposerBusy(false);
  showLogin(message);
}

async function loadHistory() {
  resetChat();
  try {
    const data = await api.history(session.conversationId);
    const turns = Array.isArray(data.turns) ? data.turns : [];
    if (!turns.length) {
      renderWelcome();
      return;
    }
    for (const turn of turns) {
      addMessage({
        text: turn.content,
        role: turn.role === "assistant" ? "bot" : "user",
      });
    }
  } catch (error) {
    if (error.status === 401) {
      handleAuthFailure("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      return;
    }
    renderWelcome();
    setAlert($("chat-error"), "Không tải được lịch sử hội thoại. Bạn vẫn có thể đặt câu hỏi mới.", "error");
  }
}

async function sendQuestion(question) {
  if (state.busy) return;
  state.busy = true;
  setComposerBusy(true);
  setAlert($("chat-error"), "", "error");
  addMessage({ text: question, role: "user" });
  $("question").value = "";
  const typing = showTyping();

  try {
    const data = await api.ask(question, session.conversationId);
    session.setConversationId(data.conversation_id);
    addMessage({
      text: data.answer,
      role: "bot",
      mode: data.mode,
      sources: Array.isArray(data.sources) ? data.sources : [],
    });
  } catch (error) {
    if (error.status === 401) {
      handleAuthFailure("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      return;
    }
    setAlert($("chat-error"), error.message, "error");
  } finally {
    typing.remove();
    state.busy = false;
    setComposerBusy(false);
    $("question").focus();
  }
}

async function handleLogin(event) {
  event.preventDefault();
  const username = $("username").value.trim();
  const password = $("password").value;
  setAlert($("login-error"), "", "error");

  if (!username || !password) {
    setAlert($("login-error"), "Vui lòng nhập tài khoản và mật khẩu.", "error");
    return;
  }

  const button = $("login-submit");
  button.disabled = true;
  button.textContent = "Đang đăng nhập…";

  try {
    const data = await api.login(username, password);
    session.save(data);
    session.setUser(data.user_id);
    await enterApp();
    $("login-form").reset();
  } catch (error) {
    setAlert($("login-error"), error.message || "Đăng nhập thất bại.", "error");
  } finally {
    button.disabled = false;
    button.textContent = "Đăng nhập";
  }
}

async function handleLogout() {
  const refreshToken = session.refresh;
  session.clear();
  state.me = null;
  resetChat();
  showLogin();
  if (!refreshToken) return;
  try {
    await api.logout(refreshToken);
  } catch {
    // Phiên có thể đã hết hạn hoặc server không phản hồi — đăng xuất phía máy khách vẫn hoàn tất.
  }
}

async function saveProfile(event) {
  event.preventDefault();
  const fullName = $("profile-fullname").value.trim();
  const message = $("profile-message");
  setAlert(message, "", "error");

  if (!fullName) {
    setAlert(message, "Họ và tên không được để trống.", "error");
    return;
  }

  const button = $("profile-submit");
  button.disabled = true;
  try {
    const updated = await api.updateMe(fullName);
    state.me = updated;
    renderIdentity();
    setAlert(message, "Đã cập nhật họ tên.", "success");
    toast("Đã cập nhật họ tên.");
  } catch (error) {
    if (error.status === 401) {
      handleAuthFailure("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      return;
    }
    setAlert(message, error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function changePassword(event) {
  event.preventDefault();
  const oldPassword = $("old-password").value;
  const newPassword = $("new-password").value;
  const confirmation = $("confirm-password").value;
  const message = $("password-message");
  setAlert(message, "", "error");

  if (!oldPassword) {
    setAlert(message, "Vui lòng nhập mật khẩu hiện tại.", "error");
    return;
  }
  if (newPassword.length < 6 || newPassword.length > 128) {
    setAlert(message, "Mật khẩu mới phải từ 6 đến 128 ký tự.", "error");
    return;
  }
  if (newPassword !== confirmation) {
    setAlert(message, "Mật khẩu nhập lại không khớp.", "error");
    return;
  }

  const button = $("password-submit");
  button.disabled = true;
  try {
    await api.changePassword(oldPassword, newPassword);
    $("password-form").reset();
    setAlert(message, "Đã đổi mật khẩu. Hãy dùng mật khẩu mới cho lần đăng nhập sau.", "success");
    toast("Đã đổi mật khẩu.");
  } catch (error) {
    if (error.status === 401) {
      handleAuthFailure("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      return;
    }
    setAlert(message, error.message, "error");
  } finally {
    button.disabled = false;
  }
}

async function loadUsers() {
  const body = $("users-body");
  const status = $("admin-state");
  body.replaceChildren();
  $("users-count").textContent = "";
  status.textContent = "Đang tải…";
  status.hidden = false;

  try {
    const data = await api.listUsers();
    const users = Array.isArray(data.users) ? data.users : [];
    $("users-count").textContent = `${users.length} người dùng`;
    status.hidden = users.length > 0;
    if (!users.length) status.textContent = "Chưa có người dùng.";

    for (const user of users) {
      const row = document.createElement("tr");
      for (const value of [user.id, user.username, user.full_name]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.appendChild(cell);
      }
      const roleCell = document.createElement("td");
      const badge = document.createElement("span");
      badge.className = `badge badge-${user.role}`;
      badge.textContent = ROLE_LABELS[user.role] || user.role;
      roleCell.appendChild(badge);
      row.appendChild(roleCell);
      body.appendChild(row);
    }
  } catch (error) {
    if (error.status === 401) {
      handleAuthFailure("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      return;
    }
    status.textContent = error.message;
    status.hidden = false;
  }
}

async function enterApp() {
  const me = await api.me();
  state.me = me;
  session.setUser(me.id);
  renderIdentity();
  showApp();
  switchView("chat");
  await loadHistory();
}

function bindEvents() {
  $("login-form").addEventListener("submit", handleLogin);
  $("logout-btn").addEventListener("click", handleLogout);
  $("new-chat").addEventListener("click", () => {
    session.resetConversation();
    renderWelcome();
    $("question").focus();
  });

  for (const tab of document.querySelectorAll(".tab")) {
    tab.addEventListener("click", () => switchView(tab.dataset.view));
  }

  $("composer").addEventListener("submit", (event) => {
    event.preventDefault();
    const question = $("question").value.trim();
    if (!question) {
      setAlert($("chat-error"), "Vui lòng nhập câu hỏi.", "error");
      $("question").focus();
      return;
    }
    setAlert($("chat-error"), "", "error");
    sendQuestion(question);
  });

  $("messages").addEventListener("click", (event) => {
    const chip = event.target.closest(".sample-chip");
    if (!chip) return;
    sendQuestion(chip.dataset.question);
  });

  $("profile-form").addEventListener("submit", saveProfile);
  $("password-form").addEventListener("submit", changePassword);
}

async function boot() {
  bindEvents();
  if (!session.hasSession()) {
    showLogin();
    return;
  }
  try {
    await enterApp();
  } catch (error) {
    if (error.status !== 401) {
      session.clear();
    }
    showLogin(
      error.status === 401
        ? "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."
        : "Không tải được thông tin người dùng. Vui lòng đăng nhập lại.",
    );
  }
}

boot();

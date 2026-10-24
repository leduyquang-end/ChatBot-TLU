/**
 * ui.js — Các hàm render thuần, không biết về API hay store.
 *
 * Nhận dữ liệu đã được normalize → tạo DOM element → trả về element.
 * Không có side effect ngoài tạo DOM.
 */
import { RETRIEVAL_MODE, RES } from "./config.js";

/* ─────────────────────────────────────────────
   Markdown render nhẹ (không cần thư viện ngoài)
   Chỉ parse các pattern phổ biến trong câu trả lời chatbot
───────────────────────────────────────────── */
function renderMd(text) {
  if (!text) return "";
  // Escape HTML trước
  let s = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Code block ```...```
  s = s.replace(/```([\s\S]*?)```/g, (_, code) =>
    `<pre><code>${code.trim()}</code></pre>`
  );
  // Inline code `...`
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bold **...**
  s = s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Italic *...*
  s = s.replace(/\*(.+?)\*/g, "<em>$1</em>");
  // Bullet list
  s = s.replace(/^[ \t]*[-*+] (.+)$/gm, "<li>$1</li>");
  // Ordered list
  s = s.replace(/^[ \t]*\d+\. (.+)$/gm, "<li>$1</li>");
  // Wrap consecutive <li> in <ul>
  s = s.replace(/(<li>[\s\S]*?<\/li>)+/g, m => `<ul>${m}</ul>`);
  // Line breaks (nhưng không trong block elements)
  s = s.replace(/\n/g, "<br>");
  // Sửa <br> trong <ul>/<pre>
  s = s.replace(/<ul>([\s\S]*?)<\/ul>/g, (_, inner) =>
    `<ul>${inner.replace(/<br>/g, "")}</ul>`
  );
  return s;
}

/* ─────────────────────────────────────────────
   Mode label — map từ backend string → UI label
   Nếu backend đổi value, chỉ cần sửa config.js RETRIEVAL_MODE
───────────────────────────────────────────── */
function modeLabel(mode) {
  const map = {
    [RETRIEVAL_MODE.VECTOR]: "📄 Tài liệu",
    [RETRIEVAL_MODE.GRAPH]:  "🔗 Quan hệ",
    [RETRIEVAL_MODE.HYBRID]: "🔍 Kết hợp",
    [RETRIEVAL_MODE.NONE]:   "💬 Trả lời trực tiếp",
  };
  // Fallback: hiển thị mode gốc nếu backend thêm giá trị mới
  return map[mode] ?? (mode ? `🔎 ${mode}` : "");
}

/* ─────────────────────────────────────────────
   Toast notification
───────────────────────────────────────────── */
export function showToast(message, type = "error") {
  const el = Object.assign(document.createElement("div"), {
    className: `toast toast--${type}`,
    textContent: message,
  });
  document.getElementById("toastArea").appendChild(el);
  requestAnimationFrame(() => el.classList.add("toast--show"));
  setTimeout(() => {
    el.classList.remove("toast--show");
    el.addEventListener("transitionend", () => el.remove(), { once: true });
  }, type === "error" ? 5000 : 3000);
}

function createAssistantAvatar(className) {
  const avatar = document.createElement("div");
  avatar.className = `assistant-avatar ${className}`;
  avatar.setAttribute("aria-hidden", "true");
  avatar.innerHTML = `
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="m2.5 8.5 9.5-5 9.5 5-9.5 5-9.5-5Z" />
      <path d="M5.5 10v5c3.8 3 9.2 3 13 0v-5M21.5 8.5v6" />
      <path d="M21.5 14.5v2.2" />
    </svg>
    <span>TLU</span>`;
  return avatar;
}

/* ─────────────────────────────────────────────
   Typing indicator
───────────────────────────────────────────── */
export function createTypingIndicator() {
  const wrap = document.createElement("div");
  wrap.className = "msg-wrap msg-wrap--bot";
  wrap.id = "typingIndicator";
  const col = document.createElement("div");
  col.className = "bubble-col";
  col.innerHTML = `<div class="bubble bubble--bot bubble--typing" aria-label="Đang soạn câu trả lời">
    <span class="dot"></span><span class="dot"></span><span class="dot"></span>
  </div>`;
  wrap.append(createAssistantAvatar("assistant-avatar--message"), col);
  return wrap;
}

/* ─────────────────────────────────────────────
   Message bubble
   @param {object} opts
   @param {"user"|"bot"} opts.role     — role của người gửi
   @param {string}  opts.content       — nội dung đã normalize
   @param {string}  opts.mode          — giá trị từ backend (có thể "")
   @param {string[]} opts.sources      — mảng tên tài liệu (có thể [])
   @param {number}  [opts.timestamp]   — ms epoch, default Date.now()
───────────────────────────────────────────── */
export function createMessageBubble({ role, content, mode = "", sources = [], timestamp }) {
  const isBot = role === RES.TURN_ROLE_BOT || role === "bot";
  const bubbleRole = isBot ? "bot" : "user";
  const ts = new Date(timestamp || Date.now()).toLocaleTimeString("vi-VN", {
    hour: "2-digit", minute: "2-digit",
  });

  const wrap = document.createElement("div");
  wrap.className = `msg-wrap msg-wrap--${bubbleRole}`;

  // Avatar (chỉ hiện bên bot)
  if (isBot) {
    wrap.appendChild(createAssistantAvatar("assistant-avatar--message"));
  }

  const col = document.createElement("div");
  col.className = "bubble-col";

  // Bubble chính
  const bubble = document.createElement("div");
  bubble.className = `bubble bubble--${bubbleRole}`;
  if (isBot) {
    bubble.innerHTML = renderMd(content);
  } else {
    // User message: text thuần, không render markdown (tránh XSS từ input)
    bubble.textContent = content;
  }
  col.appendChild(bubble);

  // Nguồn tài liệu (chỉ hiện khi có và là bot)
  if (isBot && sources.length > 0) {
    const srcRow = document.createElement("div");
    srcRow.className = "bubble-sources";
    srcRow.innerHTML = "📎 " + sources
      .map(s => `<span class="source-tag">${escHtml(s)}</span>`)
      .join(" ");
    col.appendChild(srcRow);
  }

  // Meta (timestamp + mode)
  const meta = document.createElement("div");
  meta.className = "bubble-meta";
  const modePart = isBot && mode ? ` · ${modeLabel(mode)}` : "";
  meta.textContent = `${ts}${modePart}`;
  col.appendChild(meta);

  wrap.appendChild(col);
  return wrap;
}

/* ─────────────────────────────────────────────
   Session item cho sidebar
───────────────────────────────────────────── */
export function createSessionItem({ id, title, ts, isActive, onClick, onDelete }) {
  const li = document.createElement("li");
  li.className = `session-item${isActive ? " session-item--active" : ""}`;
  li.dataset.id = id;

  const time = ts ? new Date(ts).toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" }) : "";

  li.innerHTML = `
    <button class="session-btn" type="button" title="${escHtml(title)}">
      <span class="session-title">${escHtml(title)}</span>
      <span class="session-date">${time}</span>
    </button>
    <button class="session-del" type="button" aria-label="Xóa cuộc trò chuyện khỏi danh sách trên trình duyệt">✕</button>
  `;
  li.querySelector(".session-btn").addEventListener("click", () => onClick(id));
  li.querySelector(".session-del").addEventListener("click", (e) => {
    e.stopPropagation();
    onDelete(id);
  });
  return li;
}

/* ─── Utilities ─── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

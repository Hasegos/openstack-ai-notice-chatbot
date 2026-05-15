let currentSessionId = null;
let isLoading        = false;

const sessionList  = document.getElementById("session-list");
const chatMessages = document.getElementById("chat-messages");
const chatWelcome  = document.getElementById("chat-welcome");
const chatTitle    = document.getElementById("chat-title");
const chatInput    = document.getElementById("chat-input");
const sendBtn      = document.getElementById("send-btn");
const newChatBtn   = document.getElementById("new-chat-btn");

/**
 * ──────────────────────────────────
 * 1. 초기화 — 세션 목록 로드
 * ──────────────────────────────────
 */
async function init() {
    await loadSessions();
}

/**
 * ───────────────────────
 * 2. 세션 목록 로드
 * ───────────────────────
 */
async function loadSessions() {
    try {
        const sessions = await apiRequest("/api/chat/sessions", { method: "GET" });
        renderSessionList(sessions);
    } catch {
        // 세션 로드 실패 시 빈 목록 유지
    }
}

/**
 * ──────────────────────────────────
 * 3. 세션 목록 렌더링
 * ──────────────────────────────────
 */
function renderSessionList(sessions) {
    sessionList.replaceChildren();

    if (!sessions || sessions.length === 0) {
        const empty = document.createElement("p");
        empty.style.cssText = "font-size:12px; color:rgba(255,255,255,0.3); text-align:center; padding:1rem;";
        empty.textContent = "대화 내역이 없습니다.";
        sessionList.appendChild(empty);
        return;
    }
    
    sessions.forEach(session => {
        sessionList.appendChild(createSessionItem(session));
    });
}

/**
 * ──────────────────────────────────
 * 4. 세션 아이템 생성 (삭제 버튼 포함)
 * ──────────────────────────────────
 */
function createSessionItem(session) {
    const item = document.createElement("div");
    item.className = "chat__session-item" +
        (session.session_id === currentSessionId ? " chat__session-item--active" : "");
    item.dataset.sessionId = session.session_id;

    // 세션 제목
    const title = document.createElement("span");
    title.className = "chat__session-title";
    title.textContent = session.title || "새 대화";

    // 삭제 버튼
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "chat__session-delete";
    deleteBtn.setAttribute("aria-label", "세션 삭제");
    deleteBtn.textContent = "✕";

    // 삭제 버튼 클릭 — 이벤트 버블링 차단
    deleteBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await confirmDeleteSession(session.session_id);
    });

    item.appendChild(title);
    item.appendChild(deleteBtn);

    // 세션 클릭 → 로드
    item.addEventListener("click", () => loadSession(session.session_id));

    return item;
}

/**
 * ──────────────────────────────────
 * 5. 세션 삭제 확인 + 처리
 * ──────────────────────────────────
 */
async function confirmDeleteSession(sessionId) {
    if (!confirm("이 대화를 삭제하시겠습니까?\n삭제된 대화는 복구할 수 없습니다.")) return;

    try {
        await apiRequest(`/api/chat/sessions/${sessionId}`, { method: "DELETE" });

        // 현재 열려있는 세션이 삭제된 경우 새 채팅으로 전환
        if (currentSessionId === sessionId) {
            startNewChat();
        }

        // 세션 목록 갱신
        await loadSessions();
    } catch {
        alert("세션 삭제 중 오류가 발생했습니다.");
    }
}

/**
 * ─────────────────────
 * 6. 특정 세션 로드
 * ─────────────────────
 */
async function loadSession(sessionId) {
    try {
        const session = await apiRequest(`/api/chat/sessions/${sessionId}`, { method: "GET" });
        currentSessionId = session.session_id;

        chatTitle.textContent = session.title || "새 대화";

        if (chatWelcome) chatWelcome.style.display = "none";

        chatMessages.replaceChildren();
        session.messages.forEach(msg => appendMessage(msg.role, msg.content));

        updateActiveSession(sessionId);
        scrollToBottom();
    } catch {
        // 세션 로드 실패 처리
    }
}

/**
 * ──────────────────────────────────
 * 7. 메시지 버블 추가
 * ──────────────────────────────────
 */
function appendMessage(role, content) {
    if (chatWelcome) chatWelcome.style.display = "none";

    const wrapper = document.createElement("div");
    wrapper.className = `chat__message chat__message--${role}`;

    const roleLabel = document.createElement("span");
    roleLabel.className = "chat__message-role";
    roleLabel.textContent = role === "user" ? "나" : "공지봇";

    const bubble = document.createElement("div");
    bubble.className = "chat__message-bubble";
    bubble.textContent = content;

    wrapper.appendChild(roleLabel);
    wrapper.appendChild(bubble);
    chatMessages.appendChild(wrapper);

    return wrapper;
}

/**
 * ──────────────────────────────────
 * 8. 로딩 버블 추가/제거
 * ──────────────────────────────────
 */
function appendLoadingBubble() {
    const wrapper = document.createElement("div");
    wrapper.className = "chat__message chat__message--assistant";
    wrapper.id = "loading-bubble";

    const roleLabel = document.createElement("span");
    roleLabel.className = "chat__message-role";
    roleLabel.textContent = "공지봇";

    const bubble = document.createElement("div");
    bubble.className = "chat__message-bubble chat__message-bubble--loading";

    for (let i = 0; i < 3; i++) {
        const dot = document.createElement("div");
        dot.className = "chat__loading-dot";
        bubble.appendChild(dot);
    }

    wrapper.appendChild(roleLabel);
    wrapper.appendChild(bubble);
    chatMessages.appendChild(wrapper);
    scrollToBottom();
}

function removeLoadingBubble() {
    const bubble = document.getElementById("loading-bubble");
    if (bubble) bubble.remove();
}

/**
 * ───────────────────
 * 9. 메시지 전송
 * ───────────────────
 */
async function sendMessage(message) {
    if (!message.trim() || isLoading) return;

    isLoading = true;
    sendBtn.disabled = true;
    chatInput.value = "";
    chatInput.style.height = "auto";

    appendMessage("user", message);
    scrollToBottom();
    appendLoadingBubble();

    try {
        const data = await apiRequest("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: currentSessionId || null,
                message: message,
            }),
        });

        removeLoadingBubble();

        if (!currentSessionId) {
            currentSessionId = data.session_id;
            await loadSessions();
            chatTitle.textContent = message.slice(0, 20) + (message.length > 20 ? "..." : "");
        }

        appendMessage("assistant", data.answer);
        scrollToBottom();

    } catch (err) {
        removeLoadingBubble();
        appendMessage("assistant", err.message || "오류가 발생했습니다. 잠시 후 다시 시도해주세요.");
        scrollToBottom();
    } finally {
        isLoading = false;
        updateSendButton();
    }
}

/**
 * ────────────────
 * 10. 새 채팅
 * ────────────────
 */
function startNewChat() {
    currentSessionId = null;
    chatTitle.textContent = "새 대화를 시작하세요";
    chatMessages.replaceChildren();

    if (chatWelcome) {
        chatWelcome.style.display = "";
        chatMessages.appendChild(chatWelcome);
    }

    updateActiveSession(null);
    chatInput.focus();
}

/**
 * ──────────────────────────────────
 * 11. 활성 세션 표시 업데이트
 * ──────────────────────────────────
 */
function updateActiveSession(sessionId) {
    document.querySelectorAll(".chat__session-item").forEach(item => {
        const isActive = parseInt(item.dataset.sessionId) === sessionId;
        item.classList.toggle("chat__session-item--active", isActive);
    });
}

/**
 * ──────────────────────────────────
 * 12. 전송 버튼 활성화 제어
 * ──────────────────────────────────
 */
function updateSendButton() {
    sendBtn.disabled = chatInput.value.trim() === "" || isLoading;
}

/**
 * ──────────────────────────────────
 * 13. 스크롤 최하단 이동
 * ──────────────────────────────────
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── 이벤트 리스너 ──

sendBtn.addEventListener("click", () => {
    sendMessage(chatInput.value.trim());
});

chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(chatInput.value.trim());
    }
});

chatInput.addEventListener("input", () => {
    chatInput.style.height = "auto";
    chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
    updateSendButton();
});

newChatBtn.addEventListener("click", startNewChat);

document.querySelectorAll(".chat__example-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const msg = btn.dataset.msg;
        if (msg) sendMessage(msg);
    });
});

init();
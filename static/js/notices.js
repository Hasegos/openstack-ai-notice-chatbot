const LIMIT = 20;
let currentPage   = 1;
let currentFilter = "all";
let searchQuery   = "";
let allNotices    = [];
let filtered      = [];

const noticesList       = document.getElementById("notices-list");
const noticesLoading    = document.getElementById("notices-loading");
const noticesEmpty      = document.getElementById("notices-empty");
const noticesPagination = document.getElementById("notices-pagination");
const searchInput       = document.getElementById("search-input");

// 모달 요소
const modal       = document.getElementById("notice-modal");
const backdrop    = document.getElementById("modal-backdrop");
const modalClose  = document.getElementById("modal-close");
const modalTag    = document.getElementById("modal-tag");
const modalDate   = document.getElementById("modal-date");
const modalTitle  = document.getElementById("modal-title");
const modalSummary = document.getElementById("modal-summary");
const modalContent = document.getElementById("modal-content");
const modalLink   = document.getElementById("modal-link");

/**
 * ──────────────────────────────────
 * 1. 초기화 — 공지 목록 로드
 * ──────────────────────────────────
 */
async function init() {
    showLoading(true);
    try {
        const data = await apiRequest("/api/notices?skip=0&limit=200", { method: "GET" });
        allNotices = data || [];
        applyFilter();
    } catch {
        showLoading(false);
        showEmpty(true);
    }
}

/**
 * ─────────────────────
 * 2. 필터 + 검색 적용
 * ─────────────────────
 */
function applyFilter() {
    filtered = allNotices.filter(notice => {
        // 분류 필터
        if (currentFilter === "school" && notice.dept_id !== null) return false;
        if (currentFilter === "dept"   && notice.dept_id === null) return false;

        // 검색 필터
        if (searchQuery) {
            const keyword = searchQuery.toLowerCase();
            const title   = (notice.title   || "").toLowerCase();
            const summary = (notice.summary || "").toLowerCase();
            if (!title.includes(keyword) && !summary.includes(keyword)) return false;
        }

        return true;
    });

    currentPage = 1;
    render();
}

/**
 * ──────────────────────────────────
 * 3. 현재 페이지 렌더링
 * ──────────────────────────────────
 */
function render() {
    showLoading(false);

    if (filtered.length === 0) {
        showEmpty(true);
        noticesList.replaceChildren();
        noticesPagination.replaceChildren();
        return;
    }

    showEmpty(false);

    // 페이지 슬라이싱
    const start = (currentPage - 1) * LIMIT;
    const page  = filtered.slice(start, start + LIMIT);

    // 목록 렌더링
    noticesList.replaceChildren();
    page.forEach(notice => {
        noticesList.appendChild(createNoticeCard(notice));
    });

    // 페이지네이션 렌더링
    renderPagination();
}

/**
 * ──────────────────────────────────
 * 4. 공지 카드 생성
 * ──────────────────────────────────
 */
function createNoticeCard(notice) {
    const card = document.createElement("div");
    card.className = "notice-card";

    // 상단 (태그 + 날짜)
    const top = document.createElement("div");
    top.className = "notice-card__top";

    const tag = document.createElement("span");
    tag.className = notice.dept_id
        ? "notice-card__tag notice-card__tag--dept"
        : "notice-card__tag";
    tag.textContent = notice.dept_id ? "학과 공지" : "학교 공지";

    const date = document.createElement("span");
    date.className = "notice-card__date";
    date.textContent = formatDate(notice.published_at || notice.created_at);

    top.appendChild(tag);
    top.appendChild(date);

    // 제목
    const title = document.createElement("div");
    title.className = "notice-card__title";
    title.textContent = notice.title || "제목 없음";

    // 요약
    const summary = document.createElement("div");
    summary.className = "notice-card__summary";
    summary.textContent = notice.summary || "요약 정보가 없습니다.";

    card.appendChild(top);
    card.appendChild(title);
    card.appendChild(summary);

    card.addEventListener("click", () => openModal(notice));
    return card;
}

/**
 * ─────────────────
 * 5. 모달 열기
 * ─────────────────
 */
function openModal(notice) {
    modalTag.textContent     = notice.dept_id ? "학과 공지" : "학교 공지";
    modalDate.textContent    = formatDate(notice.published_at || notice.created_at);
    modalTitle.textContent   = notice.title   || "제목 없음";
    modalSummary.textContent = notice.summary || "요약 정보가 없습니다.";
    modalContent.textContent = notice.content || "본문 내용이 없습니다.";

    if (notice.source_url) {
        modalLink.href = notice.source_url;
        modalLink.style.display = "";
    } else {
        modalLink.style.display = "none";
    }

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";
}

/**
 * ────────────────
 * 6. 모달 닫기
 * ────────────────
 */
function closeModal() {
    modal.style.display = "none";
    document.body.style.overflow = "";
}

/**
 * ──────────────────────────────────
 * 7. 페이지네이션 렌더링
 * ──────────────────────────────────
 */
function renderPagination() {
    const totalPages = Math.ceil(filtered.length / LIMIT);
    noticesPagination.replaceChildren();

    if (totalPages <= 1) return;

    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement("button");
        btn.className = "notices__page-btn" +
            (i === currentPage ? " notices__page-btn--active" : "");
        btn.textContent = i;
        btn.addEventListener("click", () => {
            currentPage = i;
            render();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
        noticesPagination.appendChild(btn);
    }
}

/**
 * ────────────
 * 8. 유틸
 * ────────────
 */
function showLoading(show) {
    noticesLoading.style.display = show ? "flex" : "none";
}

function showEmpty(show) {
    noticesEmpty.style.display = show ? "flex" : "none";
}

function formatDate(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    if (isNaN(d)) return "";
    return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, "0")}.${String(d.getDate()).padStart(2, "0")}`;
}

/**
 * ────────────────
 * 이벤트 리스너
 * ────────────────
 */

// 필터 버튼
document.querySelectorAll(".notices__filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".notices__filter-btn")
            .forEach(b => b.classList.remove("notices__filter-btn--active"));
        btn.classList.add("notices__filter-btn--active");
        currentFilter = btn.dataset.filter;
        applyFilter();
    });
});

// 검색 (300ms 디바운스)
let searchTimer;
searchInput.addEventListener("input", () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        searchQuery = searchInput.value.trim();
        applyFilter();
    }, 300);
});

// 모달 닫기
modalClose.addEventListener("click", closeModal);
backdrop.addEventListener("click", closeModal);
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
});

// 초기화
init();
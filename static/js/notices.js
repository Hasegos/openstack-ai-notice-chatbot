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
        const FETCH_SIZE = 100;
        let skip = 0;
        let fetched = [];
        while (true) {
            const data = await apiRequest(
                `/api/notices?skip=${skip}&limit=${FETCH_SIZE}`,
                { method: "GET" }
            );
            if (!data || data.length === 0) break;
            fetched = fetched.concat(data);

            if (data.length < FETCH_SIZE) break;
            skip += FETCH_SIZE;
        }
        allNotices = fetched;
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

        if (currentFilter === "school" && notice.dept_id !== null) return false;
        if (currentFilter === "dept"   && notice.dept_id === null) return false;

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

    const start = (currentPage - 1) * LIMIT;
    const page  = filtered.slice(start, start + LIMIT);

    noticesList.replaceChildren();
    page.forEach(notice => {
        noticesList.appendChild(createNoticeCard(notice));
    });

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

    const title = document.createElement("div");
    title.className = "notice-card__title";
    title.textContent = notice.title || "제목 없음";

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
async function openModal(notice) {
    modalTag.textContent     = notice.dept_id ? "학과 공지" : "학교 공지";
    modalDate.textContent    = formatDate(notice.published_at || notice.created_at);
    modalTitle.textContent   = notice.title   || "제목 없음";
    modalSummary.textContent = notice.summary || "요약 정보가 없습니다.";
    modalContent.textContent = "본문 불러오는 중...";

    if (notice.source_url) {
        modalLink.href = notice.source_url;
        modalLink.style.display = "";
    } else {
        modalLink.style.display = "none";
    }

    modal.style.display = "flex";
    document.body.style.overflow = "hidden";

    try {
        const detail = await apiRequest(`/api/notices/${notice.notice_id}`, { method: "GET" });
        const raw = detail.content || "";

        if(raw){
            modalContent.replaceChildren(buildSafeContent(raw));
        }
        else{
            modalContent.textContent = "본문 내용이 없습니다."
        }
    } catch {
        modalContent.textContent = "본문을 불러오지 못했습니다.";
    }
}

function buildSafeContent(html) {
    const ALLOWED_IMG_HOST = "www.uc.ac.kr";
    const doc = new DOMParser().parseFromString(html || "", "text/html");
    const out = document.createDocumentFragment();

    function convert(srcNode, destParent) {
        srcNode.childNodes.forEach((child) => {
            if (child.nodeType === Node.TEXT_NODE) {
                // 태그를 벗기며 살아남는 들여쓰기/개행을 단일 공백으로 축약.
                // 공백만 있는 텍스트 노드는 통째로 버린다.
                const normalized = child.nodeValue.replace(/\s+/g, " ");
                if (normalized.trim() === "") return;
                destParent.appendChild(document.createTextNode(normalized));
                return;
            }
            if (child.nodeType !== Node.ELEMENT_NODE) return;

            const tag = child.tagName.toLowerCase();

            switch (tag) {
                case "p": {
                    const p = document.createElement("p");
                    convert(child, p);
                    if (p.childNodes.length) destParent.appendChild(p); // 빈 <p> 버림
                    break;
                }
                case "br":
                    destParent.appendChild(document.createElement("br"));
                    break;
                case "strong":
                case "b": {
                    const s = document.createElement("strong");
                    convert(child, s);
                    if (s.childNodes.length) destParent.appendChild(s);
                    break;
                }
                case "img": {
                    const src = child.getAttribute("src") || "";
                    try {
                        const u = new URL(src, location.origin);
                        if ((u.protocol === "http:" || u.protocol === "https:")
                            && u.hostname === ALLOWED_IMG_HOST) {
                            const img = document.createElement("img");
                            img.src = u.href;
                            img.alt = child.getAttribute("alt") || "";
                            img.loading = "lazy";
                            destParent.appendChild(img);
                        }
                    } catch { /* 무시 */ }
                    break;
                }
                case "a": {
                    const href = child.getAttribute("href") || "";
                    try {
                        const u = new URL(href, location.origin);
                        if (u.protocol === "http:" || u.protocol === "https:") {
                            const a = document.createElement("a");
                            a.href = u.href;
                            a.target = "_blank";
                            a.rel = "noopener noreferrer";
                            convert(child, a);
                            destParent.appendChild(a);
                            break;
                        }
                    } catch { /* fall through */ }
                    convert(child, destParent);
                    break;
                }

                // ── 표 계열 ──────────────────────────────
                case "table": {
                    const t = document.createElement("table");
                    convert(child, t);
                    if (t.childNodes.length) destParent.appendChild(t);
                    break;
                }
                case "thead":
                case "tbody":
                case "tfoot": {
                    const sec = document.createElement(tag);
                    convert(child, sec);
                    if (sec.childNodes.length) destParent.appendChild(sec);
                    break;
                }
                case "tr": {
                    const tr = document.createElement("tr");
                    convert(child, tr);
                    if (tr.childNodes.length) destParent.appendChild(tr);
                    break;
                }
                case "th":
                case "td": {
                    const cell = document.createElement(tag);
                    // colspan/rowspan 은 숫자만 안전하게 허용
                    const cs = child.getAttribute("colspan");
                    const rs = child.getAttribute("rowspan");
                    if (cs && /^\d+$/.test(cs)) cell.colSpan = parseInt(cs, 10);
                    if (rs && /^\d+$/.test(rs)) cell.rowSpan = parseInt(rs, 10);
                    convert(child, cell);
                    destParent.appendChild(cell); // 빈 셀도 유지 (표 구조상 필요)
                    break;
                }
                // ────────────────────────────────────────

                default:
                    // span, font, div 등: 태그 버리고 내용만
                    convert(child, destParent);
            }
        });
    }

    convert(doc.body, out);
    return out;
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

    const WINDOW = 2;
    const pages  = new Set();

    pages.add(1);
    pages.add(totalPages);
    for (let i = currentPage - WINDOW; i <= currentPage + WINDOW; i++) {
        if (i >= 1 && i <= totalPages) pages.add(i);
    }

    const sorted = [...pages].sort((a, b) => a - b);

    const prevBtn = document.createElement("button");
    prevBtn.className = "notices__page-btn";
    prevBtn.textContent = "‹";
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener("click", () => {
        if (currentPage > 1) { 
            currentPage--; render();
            window.scrollTo({ top: 0, behavior: "smooth" });
        }
    });
    noticesPagination.appendChild(prevBtn);

    let prev = null;
    for (const p of sorted) {
        if (prev !== null && p - prev > 1) {
            const ellipsis = document.createElement("span");
            ellipsis.className = "notices__page-ellipsis";
            ellipsis.textContent = "…";
            noticesPagination.appendChild(ellipsis);
        }
        const btn = document.createElement("button");
        btn.className = "notices__page-btn" +
            (p === currentPage ? " notices__page-btn--active" : "");
        btn.textContent = p;
        btn.addEventListener("click", () => {
            currentPage = p;
            render();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
        noticesPagination.appendChild(btn);
        prev = p;
    }

    const nextBtn = document.createElement("button");
    nextBtn.className = "notices__page-btn";
    nextBtn.textContent = "›";
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener("click", () => {
        if (currentPage < totalPages) { 
            currentPage++;
            render();
            window.scrollTo({ top: 0, behavior: "smooth" }); 
        }
    });
    noticesPagination.appendChild(nextBtn);
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
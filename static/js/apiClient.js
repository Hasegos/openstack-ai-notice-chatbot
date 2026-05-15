/**
 * ─────────────────────
 * 1. API 요청 공통 함수
 * ─────────────────────
 */
async function apiRequest(url, options = {}) {
    // 1-1. 기본 헤더 설정 (CSRF 방지 및 API 요청 식별을 위해 XMLHttpRequest 설정)
    const defaultHeaders = {
        "X-Requested-With": "XMLHttpRequest",
        ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...options.headers,
    };

    const fetchOptions = {
        credentials: "include",
        ...options,
        headers: defaultHeaders,
    };

    try {
        const response = await fetch(url, fetchOptions);
        return await handleResponse(response);
    } catch (error) {
        throw error;
    }
}

/**
 * ──────────────────────────
 * 2. API 응답 및 에러 핸들러
 * ──────────────────────────
 */
async function handleResponse(response) {

    // 2-1. 성공적인 응답 처리 (200-299)
    if (response.ok) {
        const text = await response.text();
        return text ? JSON.parse(text) : null;
    }

    // ──────────────── 
    // 2-2. 401 처리
    // ────────────────
    if (response.status === 401) {
        if (window.location.pathname === "/login") {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.detail || "이메일 또는 비밀번호가 올바르지 않습니다.");
        }
        window.location.href = "/login";
        return null;
    }

    // 2-3. 에러 데이터 추출 시도
    let errorData;
    try {
        errorData = await response.json();
    } catch {
        errorData = { detail: "알 수 없는 오류가 발생했습니다." };
    }

    // ───────────────────
    // 2-4. detail 파싱
    // ───────────────────
    let errorMessage;
    if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail
            .map(err => {
                const msg = err.msg || "";
                return msg.replace(/^Value error,\s*/i, "").trim();
            })
            .filter(msg => msg.length > 0)
            .join("\n");
    } else {
        errorMessage = errorData.detail || "오류가 발생했습니다.";
    }

    // 2-5. 에러 발생 시 예외 던지기
    throw new Error(errorMessage);
}

/**
 * ───────────────────────
 * 3. 사용자 UI 에러 표시
 * ───────────────────────
 */
function showError(message, alertBoxId = "errorAlert") {
    const box = document.getElementById(alertBoxId);
    if (box) {
        if (message) {
            box.textContent = message;
            box.style.display = "block";
        } else {
            box.style.display = "none";
        }
    } else if (message) {
        alert(message);
    }
}
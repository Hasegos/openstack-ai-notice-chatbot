/**
 * ───────────────────────────────
 * 1. 로그인 폼 제출 이벤트 리스너
 * ───────────────────────────────
 */
document.getElementById("login-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    showError("");

    // ──────────────────────────
    // 1-1. 폼 데이터 수집
    // ──────────────────────────
    const username = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
        showError("이메일과 비밀번호를 입력해주세요.");
        return;
    }

    try {
        // ──────────────────────────
        // 1-2. 로그인 API 요청 (JSON)
        // ──────────────────────────
        const data = await apiRequest("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        });

        // ──────────────────────────
        // 1-3. 인증 성공 시 페이지 이동
        // ──────────────────────────
        if (data && data.redirect_url) {
            document.getElementById("password").value = "";
            window.location.replace(data.redirect_url);
        }

    } catch (err) {
        // ──────────────────────────────────────
        // 1-4. 에러 표시 + 비밀번호 필드 초기화
        // ──────────────────────────────────────
        document.getElementById("password").value = "";
        showError(err.message || "로그인 중 오류가 발생했습니다.");
    }
});

/**
 * ──────────────────────────
 * 2. 비밀번호 표시/숨김 토글
 * ──────────────────────────
 */
const pwToggle = document.getElementById("pw-toggle");
const pwInput  = document.getElementById("password");
const eyeIcon  = document.getElementById("eye-icon");

if (pwToggle && pwInput) {
    pwToggle.addEventListener("click", () => {
        const isPassword = pwInput.type === "password";
        pwInput.type = isPassword ? "text" : "password";

        // ── eye ↔ eye-off SVG 전환 ──
        while (eyeIcon.firstChild) eyeIcon.removeChild(eyeIcon.firstChild);

        if (isPassword) {
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", "M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24");

            const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
            line.setAttribute("x1", "1"); line.setAttribute("y1", "1");
            line.setAttribute("x2", "23"); line.setAttribute("y2", "23");

            eyeIcon.appendChild(path);
            eyeIcon.appendChild(line);
        } else {
            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", "M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z");

            const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            circle.setAttribute("cx", "12"); circle.setAttribute("cy", "12"); circle.setAttribute("r", "3");

            eyeIcon.appendChild(path);
            eyeIcon.appendChild(circle);
        }
    });
}

/**
 * ──────────────────────────────────
 * 3. 인풋 포커스 시 라벨 색상 전환
 * ──────────────────────────────────
 */
document.querySelectorAll(".login-form__input").forEach(input => {
    input.addEventListener("focus", () => {
        input.closest(".login-form__group")
            ?.querySelector(".login-form__label")
            ?.style.setProperty("color", "var(--accent)");
    });
    input.addEventListener("blur", () => {
        input.closest(".login-form__group")
            ?.querySelector(".login-form__label")
            ?.style.removeProperty("color");
    });
});
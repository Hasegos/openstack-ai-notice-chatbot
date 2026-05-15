/**
 * ──────────────────────────────
 * 셀렉트박스 옵션 초기화 헬퍼
 * ──────────────────────────────
 */
function resetSelect(selectEl, label) {
    selectEl.options.length = 0;
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = label;
    selectEl.appendChild(opt);
}

/**
 * ──────────────────────────────────
 * 1. 학교 선택 시 학과 동적 로딩
 * ──────────────────────────────────
 */
const schoolSelect = document.getElementById("school-select");
const deptSelect   = document.getElementById("dept-select");

if (schoolSelect) {
    schoolSelect.addEventListener("change", async () => {
        const schoolId = schoolSelect.value;

        if (!schoolId) {
            resetSelect(deptSelect, "— 학교를 먼저 선택하세요 —");
            deptSelect.disabled = true;
            return;
        }

        resetSelect(deptSelect, "— 불러오는 중 —");
        deptSelect.disabled = true;

        try {
            // ───────────────────────
            // 1-1. 학과 목록 API 요청
            // ───────────────────────
            const data = await apiRequest(`/api/schools/${schoolId}/departments`, {
                method: "GET",
            });

            // ──────────────────────
            // 1-2. 학과 옵션 렌더링
            // ──────────────────────
            resetSelect(deptSelect, "— 학과를 선택하세요 —");
            data.forEach(dept => {
                const opt = document.createElement("option");
                opt.value       = dept.dept_id;
                opt.textContent = dept.dept_name;
                deptSelect.appendChild(opt);
            });
            deptSelect.disabled = false;

        } catch {
            resetSelect(deptSelect, "불러오기 실패");
            deptSelect.disabled = true;
        }
    });
}

/**
 * ──────────────────────────────────
 * 2. 회원가입 폼 제출 이벤트 리스너
 * ──────────────────────────────────
 */
document.getElementById("register-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    showError("");

    // ────────────────────
    // 2-1. 폼 데이터 수집
    // ────────────────────
    const username        = document.getElementById("email").value.trim();
    const password        = document.getElementById("password").value;
    const password_confirm = document.getElementById("password-confirm").value;
    const student_name    = document.getElementById("student-name").value.trim();
    const student_number  = document.getElementById("student-number").value.trim();
    const school_id       = parseInt(document.getElementById("school-select").value);
    const dept_id         = parseInt(document.getElementById("dept-select").value);

    // ──────────────────────────────────
    // 2-2. 클라이언트 유효성 검사
    // ──────────────────────────────────
    if (!username || !password || !password_confirm || !student_name || !student_number) {
        showError("모든 항목을 입력해주세요.");
        return;
    }
    if (password !== password_confirm) {
        showError("비밀번호가 일치하지 않습니다.");
        document.getElementById("password").value         = "";
        document.getElementById("password-confirm").value = "";
        return;
    }
    if (!school_id) {
        showError("학교를 선택해주세요.");
        return;
    }
    if (!dept_id) {
        showError("학과를 선택해주세요.");
        return;
    }

    try {
        // ──────────────────────────────────
        // 2-3. 회원가입 API 요청 (JSON)
        // ──────────────────────────────────
        await apiRequest("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username,
                password,
                student_name,
                student_number,
                school_id,
                dept_id,
            }),
        });

        // ──────────────────────────────────
        // 2-4. 가입 성공 시 로그인 페이지 이동
        // ──────────────────────────────────
        window.location.replace("/login");

    } catch (err) {
        // ──────────────────────────────────
        // 2-5. 에러 표시 + 비밀번호 초기화
        // ──────────────────────────────────
        document.getElementById("password").value         = "";
        document.getElementById("password-confirm").value = "";
        showError(err.message || "회원가입 중 오류가 발생했습니다.");
    }
});

/**
 * ──────────────────────────
 * 3. 비밀번호 표시/숨김 토글
 * ──────────────────────────
 */
const pwToggle = document.getElementById("pw-toggle");
const pwInput  = document.getElementById("password");
const eyeIcon  = document.getElementById("eye-icon");

if (pwToggle && pwInput) {
    pwToggle.addEventListener("click", () => {
        const isPassword = pwInput.type === "password";
        pwInput.type = isPassword ? "text" : "password";

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
 * 4. 인풋 포커스 시 라벨 색상 전환
 * ──────────────────────────────────
 */
document.querySelectorAll(".register-form__input, .register-form__select").forEach(el => {
    el.addEventListener("focus", () => {
        el.closest(".register-form__group")
        ?.querySelector(".register-form__label")
        ?.style.setProperty("color", "var(--accent)");
    });
    el.addEventListener("blur", () => {
        el.closest(".register-form__group")
        ?.querySelector(".register-form__label")
        ?.style.removeProperty("color");
    });
});
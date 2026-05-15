const schoolSelect = document.getElementById('school-select');
const deptSelect   = document.getElementById('dept-select');
const startBtn     = document.getElementById('start-btn');

/**
 * ──────────────────────────────
 * 셀렉트박스 옵션 초기화 헬퍼
 * ──────────────────────────────
 */
function resetSelect(selectEl, label) {
    selectEl.options.length = 0;
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = label;
    selectEl.appendChild(opt);
}

/**
 * ──────────────────────────────────
 * 1. 학교 선택 시 학과 동적 로딩
 * ──────────────────────────────────
 */
if (schoolSelect) {
    schoolSelect.addEventListener('change', async () => {
        const schoolId = schoolSelect.value;

        if (!schoolId) {
            resetSelect(deptSelect, '— 학과 선택 —');
            return;
        }

        resetSelect(deptSelect, '— 불러오는 중 —');

        try {
            // ──────────────────────────────────
            // 1-1. 학과 목록 API 요청
            // ──────────────────────────────────
            const res  = await fetch(`/api/schools/${schoolId}/departments`);
            const data = await res.json();

            // ──────────────────────────────────
            // 1-2. 학과 옵션 렌더링
            // ──────────────────────────────────
            resetSelect(deptSelect, '— 학과 선택 —');
            data.forEach(d => {
                const opt = document.createElement('option');
                opt.value       = d.dept_id;
                opt.textContent = d.dept_name;
                deptSelect.appendChild(opt);
            });

        } catch {
            resetSelect(deptSelect, '불러오기 실패');
        }
    });
}

/**
 * ──────────────────────────────────
 * 2. 공지봇 시작하기 버튼
 * ──────────────────────────────────
 */
if (startBtn) {
    startBtn.addEventListener('click', () => {
        const schoolId = schoolSelect.value;
        const deptId   = deptSelect.value;

        if (!schoolId) {
            alert('학교를 선택해주세요.');
            return;
        }

        const params = new URLSearchParams({ school_id: schoolId });
        if (deptId) params.append('department_id', deptId);
        window.location.href = `/register?${params}`;
    });
}
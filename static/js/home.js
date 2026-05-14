const schoolSelect = document.getElementById('school-select');
const deptSelect   = document.getElementById('dept-select');
const startBtn     = document.getElementById('start-btn');

if (schoolSelect) {
    schoolSelect.addEventListener('change', async () => {
        const schoolId = schoolSelect.value;
        deptSelect.innerHTML = '<option value="">— 불러오는 중 —</option>';

        if (!schoolId) {
            deptSelect.innerHTML = '<option value="">— 학과 선택 —</option>';
            return;
        }
        try {
            const res  = await fetch(`/api/schools/${schoolId}/departments`);
            const data = await res.json();
            deptSelect.innerHTML = '<option value="">— 학과 선택 —</option>';
            data.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.id;
                opt.textContent = d.name;
                deptSelect.appendChild(opt);
            });
        } catch {
            deptSelect.innerHTML = '<option value="">불러오기 실패</option>';
        }
    });
}

if (startBtn) {
    startBtn.addEventListener('click', () => {
        const schoolId = schoolSelect.value;
        const deptId   = deptSelect.value;
        if (!schoolId) { alert('학교를 선택해주세요.'); return; }
        const params = new URLSearchParams({ school_id: schoolId });
        if (deptId) params.append('department_id', deptId);
        window.location.href = `/register?${params}`;
    });
}
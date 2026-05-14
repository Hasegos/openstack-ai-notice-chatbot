from sqlalchemy.orm import Session

from models.department_model import Department

# ──────────────────────────────────────────
# 1. 학교별 학과 목록 조회 (Read)
# ──────────────────────────────────────────
def get_departments_by_school(
    db: Session,
    school_id: int
):
    """
    특정 학교에 속한 활성화된 학과 목록을 조회합니다.
    학교 선택 시 학과 셀렉트박스 동적 로딩에 사용됩니다.
    """
    return (
        db.query(Department)
        .filter(Department.school_id == school_id, Department.is_active == True)
        .all()
    )

# ──────────────────────────────
# 2. 학과 단건 조회 (Read)
# ──────────────────────────────
def get_department_by_id(
    db: Session,
    dept_id: int
):
    """
    dept_id를 기준으로 특정 학과를 조회합니다.
    """
    return db.query(Department).filter(Department.dept_id == dept_id).first()
from sqlalchemy.orm import Session

from models.school_model import School

# ────────────────────────────
# 1. 전체 학교 목록 조회 (Read)
# ────────────────────────────
def get_all_schools(
    db: Session
):
    """
    활성화된 학교 목록 전체를 조회합니다.
    회원가입 화면 셀렉트박스에 사용됩니다.
    """
    return db.query(School).filter(School.is_active == True).all()

# ──────────────────────────────
# 2. 학교 단건 조회 (Read)
# ──────────────────────────────
def get_school_by_id(
    db: Session,
    school_id: int
):
    """
    school_id를 기준으로 특정 학교를 조회합니다.
    """
    return db.query(School).filter(School.school_id == school_id).first()
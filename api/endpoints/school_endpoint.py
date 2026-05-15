from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from crud.school_crud import get_all_schools, get_school_by_id
from crud.department_crud import get_departments_by_school
from db.session import get_db
from schemas.school_schema import SchoolOut
from schemas.department_schema import DepartmentOut

router = APIRouter()

# ───────────────────────────────────────────
# 1. 활성화된 학교 목록 조회
# ───────────────────────────────────────────
@router.get(
    "",
    response_model=list[SchoolOut],
    status_code=status.HTTP_200_OK
)
def get_schools(db: Session = Depends(get_db)):
    """
    is_active=True인 학교 목록 전체를 반환합니다.
    회원가입 · 메인 페이지 셀렉트박스에 사용됩니다.
    """
    return get_all_schools(db)


# ───────────────────────────────────────────
# 2. 학교별 활성화된 학과 목록 조회
# ───────────────────────────────────────────
@router.get(
    "/{school_id}/departments",
    response_model=list[DepartmentOut],
    status_code=status.HTTP_200_OK
)
def get_departments(
    school_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 학교의 is_active=True인 학과 목록을 반환합니다.
    학교 선택 후 학과 셀렉트박스 동적 로딩에 사용됩니다.
    """
    # ──────────────────────────────
    # 2-1. 학교 존재 여부 확인
    # ──────────────────────────────
    school = get_school_by_id(db, school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 학교입니다."
        )

    # ──────────────────────────────
    # 2-2. 학과 목록 조회 및 반환
    # ──────────────────────────────
    return get_departments_by_school(db, school_id)
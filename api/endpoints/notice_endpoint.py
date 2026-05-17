from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.auth import get_current_user
from crud.notice_crud import get_notice_by_id, get_notices_by_dept, get_notices_by_school
from db.session import get_db
from models.user_model import User
from schemas.notice_schema import NoticeDetail, NoticeOut

router = APIRouter()

# ───────────────────
# 1. 공지 목록 조회
# ───────────────────
@router.get(
    "",
    response_model=list[NoticeOut],
    status_code=status.HTTP_200_OK
)
def get_notices(
    skip: int = 0,
    limit: int = 20,
    dept: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    로그인된 사용자의 학교 공지 목록을 반환합니다.
    dept=true 이면 학과 공지만, 기본값은 전체(학교+학과) 반환합니다.
    """
    if dept and current_user.dept_id:
        return get_notices_by_dept(
            db,
            school_id=current_user.school_id,
            dept_id=current_user.dept_id,
            skip=skip,
            limit=limit
        )

    return get_notices_by_school(
        db,
        school_id=current_user.school_id,
        dept_id=current_user.dept_id,
        skip=skip,
        limit=limit
    )

# ─────────────────────
# 2. 공지 상세 조회
# ─────────────────────
@router.get(
    "/{notice_id}",
    response_model=NoticeDetail,
    status_code=status.HTTP_200_OK
)
def get_notice(
    notice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 공지사항의 상세 내용을 반환합니다.
    자신의 학교 공지만 조회 가능합니다.
    """
    notice = get_notice_by_id(db, notice_id)

    if not notice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="공지사항을 찾을 수 없습니다."
        )

    # ──────────────────────────────────────
    # 다른 학교 공지 접근 차단
    # ──────────────────────────────────────
    if notice.school_id != current_user.school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )

    return notice
from typing import Optional
from sqlalchemy.orm import Session

from models.notice_model import Notice

# ──────────────────────────────────────────
# 1. 학교별 공지 목록 조회 (Read)
# ──────────────────────────────────────────
def get_notices_by_school(
    db: Session,
    school_id: int,
    skip: int = 0,
    limit: int = 20
):
    """
    특정 학교의 전체 공지사항 목록을 조회합니다.
    학교 전체 공지 (dept_id = NULL) 포함입니다.
    """
    return (
        db.query(Notice)
        .filter(Notice.school_id == school_id)
        .order_by(Notice.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

# ──────────────────────────────────────────
# 2. 학과별 공지 목록 조회 (Read)
# ──────────────────────────────────────────
def get_notices_by_dept(
    db: Session,
    school_id: int,
    dept_id: int,
    skip: int = 0,
    limit: int = 20
):
    """
    특정 학과의 공지사항 목록을 조회합니다.
    """
    return (
        db.query(Notice)
        .filter(Notice.school_id == school_id, Notice.dept_id == dept_id)
        .order_by(Notice.published_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

# ──────────────────────────────
# 3. 공지 단건 조회 (Read)
# ──────────────────────────────
def get_notice_by_id(
    db: Session,
    notice_id: int
):
    """
    notice_id를 기준으로 공지사항 상세를 조회합니다.
    """
    return db.query(Notice).filter(Notice.notice_id == notice_id).first()
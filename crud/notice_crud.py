from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text, or_

from models.notice_model import Notice

# ──────────────────────────────────────────
# 1. 학교별 공지 목록 조회 (Read)
# ──────────────────────────────────────────
def get_notices_by_school(
    db: Session,
    school_id: int,
    dept_id = None,
    skip: int = 0,
    limit: int = 100
):
    """
    특정 학교의 전체 공지사항 목록을 조회합니다.
    학교 전체 공지 (dept_id = NULL) 포함입니다.
    """
    return (
        db.query(Notice)
        .filter(
            Notice.school_id == school_id,
            or_(
                Notice.dept_id == None,
                Notice.dept_id == dept_id
            )
        )
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

# ──────────────────────────────────────────────────
# 4. 벡터 유사도 검색 (RAG)
# cosine 유사도 기준 상위 k개 공지 반환
# ──────────────────────────────────────────────────
def search_similar_notices(
    db: Session,
    query_embedding: List[float],
    school_id: int,
    dept_id: int = None,
    limit: int = 5
) -> List[Notice]:
    """
    사용자 질문의 임베딩 벡터와 코사인 유사도가 높은 공지를 반환합니다.
    embedding이 NULL인 공지는 제외합니다.
    """
    
    # ──────────────────────────────
    # 4-1. float 타입 검증
    # ──────────────────────────────
    if not all(isinstance(v, (int, float)) for v in query_embedding):
        raise ValueError("임베딩 벡터에 유효하지 않은 값이 포함되어 있습니다.")
    
    # ──────────────────────────────────────────
    # 4-2. 벡터 문자열 변환 (PostgreSQL 형식)
    # ──────────────────────────────────────────
    embedding_str = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"

    # ──────────────────────────────────────────────────────────
    # 4-3. pgvector 코사인 유사도 검색
    # 학교 공지(dept_id=NULL) + 내 학과 공지만 대상으로 검색
    # ──────────────────────────────────────────────────────────
    result = db.execute(
        text("""
            SELECT notice_id, school_id, dept_id, title, content, source_url, published_at,
            1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM notices
            WHERE school_id = :school_id
            AND embedding IS NOT NULL
            AND (dept_id IS NULL OR dept_id = :dept_id)
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """),
        {
            "embedding": embedding_str,
            "school_id": school_id,
            "dept_id": dept_id,
            "limit": limit,
        }
    ).fetchall()

    return result

# ──────────────────────────────────────────
# 5. 공지 개수 집계 (Read)
# ──────────────────────────────────────────
def count_notices(
    db: Session,
    school_id: int,
    dept_id: int = None
) -> dict:
    """학교/학과 공지 개수를 반환합니다."""
    from sqlalchemy import func

    # ──────────────────────────────
    # 5-1. 학교 공지 수 (dept_id=NULL)
    # ──────────────────────────────
    school_count = (
        db.query(func.count(Notice.notice_id))
        .filter(Notice.school_id == school_id, Notice.dept_id == None)
        .scalar()
    )

    # ──────────────────────────────
    # 5-2. 학과 공지 수
    # ──────────────────────────────
    dept_count = (
        db.query(func.count(Notice.notice_id))
        .filter(Notice.school_id == school_id, Notice.dept_id == dept_id)
        .scalar()
    ) if dept_id else 0

    return {
        "school_count": school_count,
        "dept_count": dept_count,
        "total": school_count + dept_count
    }

# ──────────────────────────────────────────
# 6. 최신 공지 목록 조회 (Read)
# ──────────────────────────────────────────
def get_recent_notices(
    db: Session,
    school_id: int,
    dept_id: int = None,
    limit: int = 5
) -> list:
    """최신 공지를 반환합니다. dept_id 있으면 학과 공지 우선."""
    from sqlalchemy import or_

    # ──────────────────────────────────────────────────────────
    # 6-1. 학교 공지 + 내 학과 공지 필터 후 최신순 정렬
    # ──────────────────────────────────────────────────────────
    return (
        db.query(Notice)
        .filter(
            Notice.school_id == school_id,
            or_(Notice.dept_id == None, Notice.dept_id == dept_id)
        )
        .order_by(Notice.published_at.desc())
        .limit(limit)
        .all()
    )
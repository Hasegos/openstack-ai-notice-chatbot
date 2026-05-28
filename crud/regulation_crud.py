from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.regulation_model import Regulation

# ──────────────────────────────────────────────────
# 1. 벡터 유사도 검색 (RAG)
# cosine 유사도 기준 상위 k개 교칙 반환
# ──────────────────────────────────────────────────
def search_similar_regulations(
    db: Session,
    query_embedding: List[float],
    school_id: int,
    limit: int = 10,
) -> list:
    """
    사용자 질문의 임베딩 벡터와 코사인 유사도가 높은 교칙을 반환합니다.
    embedding이 NULL인 항목은 제외합니다.
    """
    # ──────────────────────────────
    # 1-1. float 타입 검증
    # ──────────────────────────────
    if not all(isinstance(v, (int, float)) for v in query_embedding):
        raise ValueError("임베딩 벡터에 유효하지 않은 값이 포함되어 있습니다.")

    # ──────────────────────────────────────────
    # 1-2. 벡터 문자열 변환 (PostgreSQL 형식)
    # ──────────────────────────────────────────
    embedding_str = "[" + ",".join(str(float(v)) for v in query_embedding) + "]"

    # ──────────────────────────────────────────────────────────
    # 1-3. pgvector 코사인 유사도 검색
    # ──────────────────────────────────────────────────────────
    result = db.execute(
        text("""
            SELECT regulation_id, school_id, category, article_no, title, content,
                revision_history,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM regulations
            WHERE school_id = :school_id
            AND embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
        """),
        {
            "embedding": embedding_str,
            "school_id": school_id,
            "limit": limit,
        }
    ).fetchall()

    return result

# ──────────────────────────────────────────────────
# 2. 키워드 검색
# 조항 번호/제목/내용 기반 직접 검색
# ──────────────────────────────────────────────────
def search_regulations_by_keyword(
    db: Session,
    keyword: str,
    school_id: int,
    limit: int = 5,
) -> list:
    """
    조항 번호, 제목, 내용에서 키워드로 직접 검색합니다.
    """
    result = db.execute(
        text("""
            SELECT regulation_id, school_id, category, article_no, title, content,
                revision_history
            FROM regulations
            WHERE school_id = :school_id
            AND (
                title      ILIKE :keyword
                OR content    ILIKE :keyword
                OR article_no ILIKE :keyword
            )
            ORDER BY article_no
            LIMIT :limit
        """),
        {
            "school_id": school_id,
            "keyword": f"%{keyword}%",
            "limit": limit,
        }
    ).fetchall()

    return result
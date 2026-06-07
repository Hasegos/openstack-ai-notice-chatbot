from sqlalchemy.orm import Session

from crud.notice_crud import (
    search_similar_notices,
    search_notices_by_keyword,
    count_notices,
    get_recent_notices,
)
from crud.regulation_crud import (
    search_similar_regulations,
    search_regulations_by_keyword,
)
from services.llm_service import get_embedding
from services.query_parser import (
    extract_notice_keywords,
    extract_article_keyword,
    extract_year_keyword,
)

# ─────────────────────────────────────
# 공지 현황 카운트 컨텍스트 생성
# ─────────────────────────────────────
def build_count_context(db: Session, school_id: int, dept_id: int) -> str:
    """학교/학과/전체 공지 개수 컨텍스트를 생성합니다."""
    counts = count_notices(db, school_id=school_id, dept_id=dept_id)
    return (
        f"[공지 현황] 학교 공지: {counts['school_count']}개 / "
        f"학과 공지: {counts['dept_count']}개 / "
        f"전체: {counts['total']}개"
    )

# ─────────────────────────────────────
# 최근/목록 공지 컨텍스트 생성
# ─────────────────────────────────────
def build_recent_context(
    db: Session,
    school_id: int,
    dept_id: int,
    count_context: str,
    intent: str,
    source_ids: list,
) -> str:
    """최신/목록 질문에 대한 공지 목록 컨텍스트를 생성합니다."""
    limit = 20 if intent == "list" else 5
    recent = get_recent_notices(
        db,
        school_id=school_id,
        dept_id=dept_id,
        limit=limit
    )
    lines = []
    for n in recent:
        source_ids.append({
            "id": n.notice_id,
            "title": n.title,
            "dept_name": "학과 공지" if n.dept_id else "학교 공지",
            "created_at": n.published_at.isoformat() if n.published_at else None,
            "source_url": n.source_url,
        })
        date = n.published_at.strftime("%Y.%m.%d") if n.published_at else "날짜 미상"
        lines.append(f"- [{date}] {n.title} ({n.source_url or ''})")
    return count_context + "\n\n[최근 공지 목록]\n" + "\n".join(lines)

# ─────────────────────────────────────
# 공지 유사도 + 키워드 보조 검색 컨텍스트 생성
# ─────────────────────────────────────
async def build_notice_context(
    db: Session,
    message: str,
    school_id: int,
    dept_id: int,
    query_type: str,
    count_context: str,
    source_ids: list,
    recent_context: str = "",
) -> tuple[str, list[float]]:
    """
    공지 유사도 검색 + 키워드 보조 검색 결과를 병합하여 컨텍스트를 생성합니다.
    recent_context: 직전 대화 일부. "그거 언제야?" 같은 후속 질문의 대명사를
                    해소하기 위해 검색 쿼리 앞에 붙입니다 (검색 정확도 보강).
    반환: (공지 컨텍스트 문자열, 질문 임베딩 벡터)
    """
    # ── 검색용 쿼리 구성 (직전 대화 + 현재 질문) ──
    search_query = f"{recent_context}\n{message}".strip() if recent_context else message

    # ── 공지 유사도 검색 ──────────────────────
    query_embedding = await get_embedding(search_query)
    print(f"[RAG] embedding 생성 완료: {len(query_embedding)}차원")

    # 규정성 질문이면 공지는 적게, 그 외엔 6개
    notice_limit = 3 if query_type == "regulation" else 6
    similar_notices = search_similar_notices(
        db,
        query_embedding=query_embedding,
        school_id=school_id,
        dept_id=dept_id,
        limit=notice_limit
    )
    print(f"[RAG] 공지 유사도 검색: {len(similar_notices)}개")

    # ── 공지 키워드 보조 검색 (추상적 질문 대응) ──
    collected = {}
    for row in similar_notices:
        collected[row.notice_id] = row

    keywords = extract_notice_keywords(message)
    if keywords:
        print(f"[RAG] 공지 키워드 감지: {keywords}")
        for kw in keywords:
            kw_notices = search_notices_by_keyword(
                db,
                keyword=kw,
                school_id=school_id,
                dept_id=dept_id,
                limit=5,
            )
            for row in kw_notices:
                if row.notice_id not in collected:
                    collected[row.notice_id] = row
                    print(f"[RAG] 키워드 보조 추가: {row.title}")

    rag_context = ""
    if collected:
        merged = sorted(
            collected.values(),
            key=lambda r: r.published_at or "",
            reverse=True
        )
        context_parts = [count_context]
        for row in merged:
            source_ids.append({
                "id": row.notice_id,
                "title": row.title,
                "dept_name": "학과 공지" if row.dept_id else "학교 공지",
                "created_at": row.published_at.isoformat() if row.published_at else None,
                "source_url": row.source_url,
            })
            date = row.published_at.strftime("%Y.%m.%d") if row.published_at else "날짜 미상"
            content_preview = (row.content or "")[:500]
            context_parts.append(
                f"[공지 제목] {row.title}\n"
                f"[게시일] {date}\n"
                f"[내용] {content_preview}\n"
                f"[출처] {row.source_url}"
            )
        rag_context = "\n\n---\n\n".join(context_parts)

    return rag_context, query_embedding

# ───────────────────────────────────────────
# 교칙 검색 컨텍스트 생성 (키워드 + 유사도)
# ───────────────────────────────────────────
def build_regulation_context(
    db: Session,
    message: str,
    school_id: int,
    query_type: str,
    query_embedding: list[float],
) -> str:
    """
    교칙 키워드 검색 + 유사도 검색 결과를 병합하여 컨텍스트를 생성합니다.
    """
    reg_parts   = []
    seen_titles = set()

    # ── 조항 번호 패턴 감지 → 키워드 검색 ──────
    article_keyword = extract_article_keyword(message)
    if article_keyword:
        print(f"[Regulation] 조항 키워드 감지: {article_keyword}")
        keyword_regs = search_regulations_by_keyword(
            db,
            keyword=article_keyword,
            school_id=school_id,
            limit=5,
        )
        for row in keyword_regs:
            key = f"{row.category}-{row.title}"
            if key in seen_titles:
                continue
            seen_titles.add(key)
            print(f"[Regulation 키워드] {row.category} {row.title}")
            content_str = f"[교칙 {row.category} {row.title}]\n{row.content}"
            if row.revision_history:
                content_str += f"\n[개정 이력] {row.revision_history}"
            reg_parts.append(content_str)

    # ── 유사도 검색 (threshold 0.55 이상) ──
    if query_embedding:
        # 규정성 질문이면 5개, 혼합이면 3개
        reg_limit = 5 if query_type == "regulation" else 3
        similar_regs = search_similar_regulations(
            db,
            query_embedding=query_embedding,
            school_id=school_id,
            limit=reg_limit,
        )
        year_keyword = extract_year_keyword(message)
        for row in similar_regs:
            print(f"[Regulation 유사도] {row.category} {row.title} ({row.similarity:.4f})")
            if row.similarity < 0.55:
                continue
            key = f"{row.category}-{row.title}"
            if key in seen_titles:
                continue
            seen_titles.add(key)
            revision_info = ""
            if row.revision_history:
                revision_info = f"\n[개정 이력] {row.revision_history}"
            if year_keyword and row.revision_history and year_keyword in row.revision_history:
                revision_info += f"\n[참고] {year_keyword}년 관련 개정 내역 포함"
            content = f"[교칙 {row.category} {row.title}]{revision_info}\n{row.content}"
            reg_parts.append(content)

    regulation_context = ""
    if reg_parts:
        regulation_context = "\n\n---\n\n".join(reg_parts)
        print(f"[Regulation RAG] 최종 {len(reg_parts)}개 컨텍스트 구성")
    else:
        print(f"[Regulation RAG] 관련 교칙 없음")

    return regulation_context
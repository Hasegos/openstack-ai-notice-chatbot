import json

from sqlalchemy.orm import Session

from crud.notice_crud import (
    rerank_vector_search,
    search_notices_by_keyword,
    count_notices,
    get_recent_notices,
)
from crud.regulation_crud import (
    search_similar_regulations,
    search_regulations_by_keyword,
)
from services.llm_service import get_embedding, call_ollama
from services.query_parser import (
    extract_notice_keywords,
    extract_article_keyword,
    extract_year_keyword,
)

# ─────────────────────────────────────────────────────────────
# 쿼리 확장 — 구어체 질문 → 공식 행정 용어 4개 (LLM 호출)
# ─────────────────────────────────────────────────────────────
async def expand_query(query_text: str) -> list[str]:
    """
    구어체/단어 단위 쿼리를 공식 행정 용어로 확장합니다.
    LLM 서버 미응답, JSON 파싱 실패 등 모든 예외 상황에서 [] 반환.
    호출 실패해도 원본 쿼리 검색은 계속 진행됩니다.
    """
    system_prompt = (
        "당신은 대학교 공지사항 검색 시스템의 쿼리 확장 모듈입니다.\n"
        "사용자 질문을 분석해 공지사항 검색에 도움이 될 관련 키워드를 생성합니다."
    )
    user_prompt = (
        "다음 질문에 대해 공지사항 검색에 도움이 될 관련 키워드 4개를 생성하세요.\n"
        "반드시 JSON 배열 형식으로만 응답하고, 설명은 포함하지 마세요.\n"
        f"질문: {query_text}\n"
        '응답 형식: ["키워드1", "키워드2", "키워드3", "키워드4"]\n'
        "규칙:\n"
        "- 원래 질문의 의미를 유지하는 공식적 행정 용어 포함\n"
        "- 학교 공지에 실제 사용되는 표현 위주\n"
        "- 불필요한 조사나 어미는 제거\n"
        "예시 입력: '수업 빠져도 돼?'\n"
        '예시 출력: ["출석 인정", "결석 처리", "출결 관리", "수업 불참"]'
    )
    try:
        raw = await call_ollama([
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ])
        # LLM이 코드블록·설명 텍스트를 포함할 수 있으므로 [ ... ] 부분만 추출
        start = raw.index("[")
        end   = raw.rindex("]") + 1
        keywords = json.loads(raw[start:end])
        if isinstance(keywords, list):
            return [str(k) for k in keywords if k]
        return []
    except Exception:
        return []

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
        source_ids.append(n.notice_id)
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

    # ── 쿼리 확장 (구어체 → 공식 행정 용어, 실패 시 [] fallback) ──
    expanded_keywords = await expand_query(message)
    all_queries = [search_query] + expanded_keywords
    if expanded_keywords:
        print(f"[RAG] 쿼리 확장 결과: {expanded_keywords}")

    # ── 임베딩은 원본 쿼리로 1회만 생성 ──
    query_embedding = await get_embedding(search_query)
    print(f"[RAG] embedding 생성 완료: {len(query_embedding)}차원")

    # 규정성 질문이면 공지는 적게, 그 외엔 6개
    notice_limit = 3 if query_type == "regulation" else 6

    # all_queries 각각으로 re-ranking 검색 후 notice_id 기준 중복 제거
    # 원본 쿼리는 full notice_limit, 확장 키워드는 최대 3개씩 추가
    collected = {}
    for i, q in enumerate(all_queries):
        k = notice_limit if i == 0 else min(3, notice_limit)
        results = rerank_vector_search(
            db,
            query_text=q,
            query_embedding=query_embedding,
            school_id=school_id,
            dept_id=dept_id,
            top_k=k,
        )
        for row in results:
            if row.notice_id not in collected:
                collected[row.notice_id] = row
    print(f"[RAG] 공지 re-ranking 완료 (확장 포함): {len(collected)}개 후보")

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
            source_ids.append(row.notice_id)
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
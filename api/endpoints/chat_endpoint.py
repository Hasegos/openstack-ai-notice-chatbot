import json, logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.rate_limit import limiter

logger = logging.getLogger(__name__)

from core.auth import get_current_user
from core.config import settings
from crud.chat_crud import (
    create_session,
    create_message,
    delete_session,
    get_sessions_by_user,
    get_session_by_id,
    get_messages_by_session,
)
from db.session import get_db, SessionLocal
from models.user_model import User
from schemas.chat_schema import ChatRequest, ChatSessionOut

from services.query_parser import classify_intent, detect_query_type
from services.llm_service import call_ollama_stream
from services.rag_service import (
    build_count_context,
    build_recent_context,
    build_notice_context,
    build_regulation_context,
)
from services.memory_service import build_memory_context, messages_to_text

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────
# 1. 채팅 메시지 전송 (스트리밍)
# SSE 이벤트 포맷:
#   data: {"type":"meta","session_id":N,"sources":[...]}  ← 스트림 시작 전 1회
#   data: {"type":"token","content":"..."}                ← 토큰 단위 반복
#   data: [DONE]                                          ← 스트림 종료
#   data: {"type":"error","message":"..."}                ← 오류 발생 시
# ─────────────────────────────────────────────────────────────────────
@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
async def chat_stream(
    request: Request,
    req: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    스트리밍 버전 채팅. RAG 파이프라인은 기존 chat()과 동일하며,
    LLM 응답을 SSE(text/event-stream)로 토큰 단위 전송합니다.
    답변 전체는 스트리밍 완료 후 DB에 저장합니다.
    """
    school_id = current_user.school_id
    dept_id   = current_user.dept_id
    user_id   = current_user.user_id

    rag_context        = ""
    regulation_context = ""
    source_ids         = []
    query_embedding    = []
    memory_summary     = ""
    recent_messages    = []

    intent     = classify_intent(req.message)
    query_type = detect_query_type(req.message)
    logger.info(f"[Stream] 분류 결과: {intent} / 질문 유형: {query_type}")

    # ══════════════════════════════════════════════════════════
    # DB 세션 구간 — 세션 처리 + 메시지 저장 + RAG 검색 + compact
    # ══════════════════════════════════════════════════════════
    with SessionLocal() as db:
        # ── 1-1. 세션 처리 (신규 or 기존) ──
        if req.session_id:
            session = get_session_by_id(db, req.session_id)
            if not session or session.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="세션을 찾을 수 없습니다."
                )
            session_id      = session.session_id
            prev_summary    = session.summary
            prev_summarized = session.summarized_until
        else:
            title = req.message[:20] + ("..." if len(req.message) > 20 else "")
            session = create_session(db, user_id, title)
            session_id      = session.session_id
            prev_summary    = None
            prev_summarized = None

        # ──────────────────────────────────────────
        # 1-2. 검색 보강용 직전 대화 확보
        # ──────────────────────────────────────────
        prior = get_messages_by_session(db, session_id)
        recent_context = messages_to_text(prior[-3:]) if prior else ""

        # ──────────────────────────────────────────
        # 1-3. 사용자 메시지 저장
        # ──────────────────────────────────────────
        create_message(db, session_id, "user", req.message)

        # ──────────────────────────────────────────
        # 1-4. 공지 현황 카운트
        # ──────────────────────────────────────────
        count_context = build_count_context(db, school_id, dept_id)

        # ──────────────────────────────────────────
        # 1-5. 공지 검색
        # ──────────────────────────────────────────
        try:
            if intent == "count":
                rag_context = count_context

            elif intent in ("recent", "list"):
                rag_context = build_recent_context(
                    db,
                    school_id=school_id,
                    dept_id=dept_id,
                    count_context=count_context,
                    intent=intent,
                    source_ids=source_ids,
                )
            else:
                rag_context, query_embedding = await build_notice_context(
                    db,
                    message=req.message,
                    school_id=school_id,
                    dept_id=dept_id,
                    query_type=query_type,
                    count_context=count_context,
                    source_ids=source_ids,
                    recent_context=recent_context,
                )

        except Exception as e:
            logger.error(f"[Stream 공지 RAG] 오류 발생: {e}")
            rag_context = count_context

        # ──────────────────────────────────────────
        # 1-6. 교칙 검색 (규정성/혼합 질문일 때만)
        # ──────────────────────────────────────────
        if intent == "search" and query_type in ("regulation", "both"):
            try:
                regulation_context = build_regulation_context(
                    db, message=req.message, school_id=school_id,
                    query_type=query_type, query_embedding=query_embedding,
                )
            except Exception as e:
                logger.error(f"[Stream 교칙 RAG] 오류 발생: {e}")

        # ────────────────────────────────────────────────────────
        # 1-7. compact — 대화 맥락 구성 (요약본 + 최근 메시지)
        # ────────────────────────────────────────────────────────
        rag_total_len = len(rag_context) + len(regulation_context)
        try:
            memory_summary, recent_messages = await build_memory_context(
                db, session_id=session_id, summary=prev_summary,
                summarized_until=prev_summarized,
                system_prompt_len=len(settings.SYSTEM_PROMPT),
                rag_context_len=rag_total_len,
            )
        except Exception as e:
            # compact 실패해도 답변은 진행 (요약 없이)
            logger.warning(f"[Stream Compact] 오류 발생, 요약 없이 진행: {e}")
            memory_summary, recent_messages = "", []

    # ══════════════════════════════════════════════════════════
    # [LLM 구간] DB 커넥션을 잡지 않은 상태로 Ollama 호출
    # ══════════════════════════════════════════════════════════
    system_content = settings.SYSTEM_PROMPT
    
    # 이전 대화 요약본(compact) 주입
    if memory_summary:
        system_content += f"\n\n아래는 이 사용자와의 이전 대화 요약입니다. 맥락 파악에 참고하세요:\n\n{memory_summary}"

    # RAG 컨텍스트 주입
    if rag_context:
        system_content += f"\n\n아래는 학교 공지사항 검색 결과입니다. 게시일이 가장 최근인 공지를 우선하여 답변하고, 관련 공지의 출처 URL을 반드시 함께 안내하세요:\n\n{rag_context}"
    if regulation_context:
        system_content += f"\n\n아래는 학교 교칙/정관 검색 결과입니다. 규칙 관련 질문 시 이를 우선 참고하세요:\n\n{regulation_context}"

    messages = [{"role": "system", "content": system_content}]
    messages.extend(recent_messages)
    messages.append({"role": "user", "content": req.message})

    # ══════════════════════════════════════════════════════════
    # SSE 제너레이터 — 토큰 스트리밍 + 완료 후 DB 저장
    # ══════════════════════════════════════════════════════════
    async def generate():
        # meta 이벤트: 클라이언트가 session_id, sources를 토큰 수신 전에 확보
        yield f"data: {json.dumps({'type': 'meta', 'session_id': session_id, 'sources': source_ids}, ensure_ascii=False)}\n\n"

        full_tokens: list[str] = []
        try:
            async for token in call_ollama_stream(messages):
                full_tokens.append(token)
                yield f"data: {json.dumps({'type': 'token', 'content': token}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"[Stream LLM] 오류: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': '응답 생성 중 오류가 발생했습니다.'}, ensure_ascii=False)}\n\n"
            return

        # 스트리밍 완료 후 전체 답변을 DB에 저장
        answer = "".join(full_tokens)
        with SessionLocal() as db:
            create_message(db, session_id, "assistant", answer)

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",   # Nginx 버퍼링 비활성화
            "Cache-Control": "no-cache",
        },
    )

# ───────────────────────────────────────────
# 2. 세션 목록 조회
# ───────────────────────────────────────────
@router.get(
    "/sessions",
    response_model=list[ChatSessionOut],
    status_code=status.HTTP_200_OK
)
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인된 사용자의 채팅 세션 목록을 반환합니다.
    """
    return get_sessions_by_user(db, current_user.user_id)

# ───────────────────────────────────────────
# 3. 세션 상세 조회 (메시지 포함)
# ───────────────────────────────────────────
@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionOut,
    status_code=status.HTTP_200_OK
)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 세션의 메시지 목록을 포함한 상세 정보를 반환합니다.
    """
    session = get_session_by_id(db, session_id)

    if not session or session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )

    return session

# ─────────────────
# 4. 세션 삭제
# ─────────────────
@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_200_OK
)
def remove_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 세션과 해당 세션의 모든 메시지를 삭제합니다.
    본인 세션만 삭제 가능합니다.
    """
    # ──────────────────────────────────────
    # 4-1. 세션 존재 여부 + 소유권 확인
    # ──────────────────────────────────────
    session = get_session_by_id(db, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다."
        )

    if session.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="삭제 권한이 없습니다."
        )

    # ──────────────────────────────────────
    # 4-2. 세션 + 메시지 삭제
    # ──────────────────────────────────────
    delete_session(db, session_id)

    return {"message": "세션이 삭제되었습니다."}
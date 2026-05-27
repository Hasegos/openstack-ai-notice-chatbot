import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
from crud.notice_crud import search_similar_notices, count_notices, get_recent_notices
from crud.regulation_crud import search_similar_regulations
from db.session import get_db
from models.user_model import User
from schemas.chat_schema import ChatRequest, ChatResponse, ChatSessionOut

router = APIRouter()

# ─────────────────────────────────────────────────────
# 임베딩 API 호출 (LM Studio)
# ─────────────────────────────────────────────────────
async def get_embedding(text: str) -> list[float]:
    """
    LM Studio 임베딩 API를 호출하여 텍스트의 벡터를 반환합니다.
    """
    payload = {
        "model": settings.EMBEDDING_MODEL,
        "prompt": text,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.EMBEDDING_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]

# ─────────────────────────────────────────────────────
# LM Studio 설정
# API 키 불필요, 모델명은 LM Studio에 로드된 모델 사용
# ─────────────────────────────────────────────────────
async def call_lm_studio(messages: list[dict]) -> str:
    """
    LM Studio 로컬 서버에 chat completion 요청을 보냅니다.
    OpenAI 호환 형식으로 요청합니다.
    """
    payload = {
        "model": settings.Ollama_MODEL,
        "messages": messages,
        "stream": False,
         "options": {
            "temperature": settings.LLM_TEMPERATURE,
            "top_k": settings.LLM_TOP_K,
            "top_p": settings.LLM_TOP_P,
            "repeat_penalty": settings.LLM_REPEAT_PENALTY,
            "num_predict": settings.LLM_NUM_PREDICT,
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.Ollama_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        # 400일 때 실제 응답 내용 출력
        if response.status_code != 200:
            print(f"[LM Studio] 상태코드: {response.status_code}")
            print(f"[LM Studio] 응답 내용: {response.text}")
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

# ─────────────────────────────────────
# 의도 분류
# ─────────────────────────────────────
def classify_intent(message: str) -> str:
    """
    질문 의도를 키워드 기반으로 분류합니다.
    """
    msg = message.lower()

    COUNT_KEYWORDS  = ["몇 개", "몇개", "개수", "총", "전체 수", "얼마나"]
    RECENT_KEYWORDS = ["최근", "최신", "새로운", "방금", "최근에", "요즘", "최근 공지"]
    LIST_KEYWORDS   = ["전부", "모두", "다 보여", "목록", "리스트", "전체 목록"]

    if any(k in msg for k in COUNT_KEYWORDS):
        return "count"
    if any(k in msg for k in RECENT_KEYWORDS):
        return "recent"
    if any(k in msg for k in LIST_KEYWORDS):
        return "list"
    return "search"

# ─────────────────────
# 1. 채팅 메시지 전송
# ─────────────────────
@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자 메시지를 받아 RAG 파이프라인으로 답변을 생성합니다.
    session_id가 없으면 새 세션을 자동 생성합니다.
    """
    # ──────────────────────────────────────
    # 1-1. 세션 처리 (신규 or 기존)
    # ──────────────────────────────────────
    if req.session_id:
        session = get_session_by_id(db, req.session_id)
        if not session or session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="세션을 찾을 수 없습니다."
            )
    else:
        # 첫 질문 앞 20자를 세션 제목으로 사용
        title = req.message[:20] + ("..." if len(req.message) > 20 else "")
        session = create_session(db, current_user.user_id, title)

    # ──────────────────────────────────────
    # 1-2. 사용자 메시지 저장
    # ──────────────────────────────────────
    create_message(db, session.session_id, "user", req.message)

    # ──────────────────────────────────────
    # 1-3. RAG: 질문 임베딩 → 유사 공지 검색
    # ──────────────────────────────────────
    rag_context = ""
    regulation_context = ""
    source_ids = []
    intent      = classify_intent(req.message)
    print(f"[Intent] 분류 결과: {intent}")

    # 항상 공지 개수 주입 (집계 질문 대비)
    counts = count_notices(db, school_id=current_user.school_id, dept_id=current_user.dept_id)
    count_context = (
        f"[공지 현황] 학교 공지: {counts['school_count']}개 / "
        f"학과 공지: {counts['dept_count']}개 / "
        f"전체: {counts['total']}개"
    )

    try:
        if intent == "count":
            # 개수 질문 → 카운트만 넘김
            rag_context = count_context

        elif intent in ("recent", "list"):
            # 최신/목록 질문 → 최근 공지 목록 넘김
            limit = 20 if intent == "list" else 5
            recent = get_recent_notices(
                db,
                school_id=current_user.school_id,
                dept_id=current_user.dept_id,
                limit=limit
            )
            lines = []
            for n in recent:
                source_ids.append(n.notice_id)
                date = n.published_at.strftime("%Y.%m.%d") if n.published_at else "날짜 미상"
                lines.append(f"- [{date}] {n.title} ({n.source_url or ''})")
            rag_context = count_context + "\n\n[최근 공지 목록]\n" + "\n".join(lines)

        else:
            # 기본: 유사도 기반 RAG 검색
            query_embedding = await get_embedding(req.message)
            print(f"[RAG] embedding 생성 완료: {len(query_embedding)}차원")

            similar_notices = search_similar_notices(
                db,
                query_embedding=query_embedding,
                school_id=current_user.school_id,
                dept_id=current_user.dept_id,
                limit=5
            )
            print(f"[RAG] 검색 결과: {len(similar_notices)}개")

            if similar_notices:
                context_parts = [count_context]
                for row in similar_notices:
                    source_ids.append(row.notice_id)
                    print(f"[RAG] 검색된 공지: {row.title} (유사도: {row.similarity:.4f})")
                    content_preview = (row.content or "")[:500]
                    context_parts.append(
                        f"[공지 제목] {row.title}\n[내용] {content_preview}\n[출처] {row.source_url}"
                    )
                rag_context = "\n\n---\n\n".join(context_parts)
            
            # ── 교칙 RAG 추가 ──────────────────────────
            similar_regs = search_similar_regulations(
                db,
                query_embedding=query_embedding,
                school_id=current_user.school_id,
                limit=3,
            )
            if similar_regs:
                reg_parts = []
                for row in similar_regs:
                    reg_parts.append(
                        f"[교칙 {row.category} {row.title}]\n{row.content}"
                    )
                regulation_context = "\n\n---\n\n".join(reg_parts)
                print(f"[Regulation RAG] 검색 결과: {len(similar_regs)}개")

    except Exception as e:
        print(f"[RAG] 오류 발생: {e}")
        rag_context = count_context  # 실패해도 카운트는 넘김

    # ──────────────────────────────────────────────────────────
    # 1-4. 대화 히스토리 + RAG 컨텍스트 구성
    # ──────────────────────────────────────────────────────────
    system_content = settings.SYSTEM_PROMPT
    if rag_context:
        system_content += f"\n\n아래는 학교 공지사항 검색 결과입니다. 이를 참고하여 답변하세요:\n\n{rag_context}"
    
    if regulation_context:
        system_content += f"\n\n아래는 학교 교칙/정관 검색 결과입니다. 규칙 관련 질문 시 이를 우선 참고하세요:\n\n{regulation_context}"

    history = get_messages_by_session(db, session.session_id)
    messages = [{"role": "system", "content": system_content}]
    # 현재 메시지 제외한 이전 히스토리만 포함 (마지막 user 메시지 제외)
    for msg in history[-20: -1]:
        messages.append({"role": msg.role, "content": msg.content})
    # 현재 질문 마지막에 추가
    messages.append({"role": "user", "content": req.message})

    # 1-5. LM Studio 호출 직전에 추가
    total_chars = sum(len(m["content"]) for m in messages)
    print(f"[LM Studio] 총 메시지 길이: {total_chars}자, 메시지 수: {len(messages)}개")

    # ──────────────────────────────────────
    # 1-5. LM Studio 호출
    # ──────────────────────────────────────
    try:
        answer = await call_lm_studio(messages)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LM Studio 서버에 연결할 수 없습니다. LM Studio가 실행 중인지 확인해주세요."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LM Studio 응답 시간이 초과되었습니다."
        )
    except Exception as e:
        print(f"[LM Studio] 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LM Studio 호출 중 오류가 발생했습니다."
        )

    # ──────────────────────────────────────
    # 1-6. 어시스턴트 응답 저장
    # ──────────────────────────────────────
    create_message(db, session.session_id, "assistant", answer)

    return ChatResponse(
        session_id=session.session_id,
        answer=answer,
        sources=source_ids
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
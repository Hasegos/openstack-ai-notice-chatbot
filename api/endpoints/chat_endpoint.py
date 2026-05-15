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
from db.session import get_db
from models.user_model import User
from schemas.chat_schema import ChatRequest, ChatResponse, ChatSessionOut

router = APIRouter()

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
        "model": settings.LM_STUDIO_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.LM_STUDIO_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

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

    # ──────────────────────────────────────────────────────────
    # 1-3. 대화 히스토리 구성 (최근 10턴)
    # LM Studio에 system prompt + 대화 이력 + 현재 질문 전달
    # ──────────────────────────────────────────────────────────
    history = get_messages_by_session(db, session.session_id)
    messages = [{"role": "system", "content": settings.SYSTEM_PROMPT}]
    for msg in history[-20:]:  # 최근 20개 메시지 (10턴)
        messages.append({"role": msg.role, "content": msg.content})

    # ──────────────────────────────────────
    # 1-4. LM Studio 호출
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
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LM Studio 호출 중 오류가 발생했습니다."
        )

    # ──────────────────────────────────────
    # 1-4. 어시스턴트 응답 저장
    # ──────────────────────────────────────
    create_message(db, session.session_id, "assistant", answer)

    return ChatResponse(
        session_id=session.session_id,
        answer=answer,
        sources=[]
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
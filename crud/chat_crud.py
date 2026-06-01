from typing import Optional
from sqlalchemy.orm import Session

from models.chat_session_model import ChatSession
from models.chat_message_model import ChatMessage

# ────────────────────────────────
# 1. 채팅 세션 생성 (Create)
# ────────────────────────────────
def create_session(
    db: Session,
    user_id: int,
    title: Optional[str] = None
):
    """
    새로운 채팅 세션을 생성합니다.
    title은 첫 질문 내용으로 자동 추출하여 넣습니다.
    """
    db_session = ChatSession(
        user_id = user_id,
        title   = title,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session

# ────────────────────────────────
# 2. 채팅 세션 목록 조회 (Read)
# ────────────────────────────────
def get_sessions_by_user(
    db: Session,
    user_id: int
):
    """
    특정 사용자의 채팅 세션 목록을 최신순으로 조회합니다.
    """
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

# ────────────────────────────────
# 3. 채팅 세션 단건 조회 (Read)
# ────────────────────────────────
def get_session_by_id(
    db: Session,
    session_id: int
):
    """
    session_id를 기준으로 특정 세션을 조회합니다.
    """
    return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()

# ────────────────────────────────
# 4. 채팅 메시지 저장 (Create)
# ────────────────────────────────
def create_message(
    db: Session,
    session_id: int,
    role: str,
    content: str
):
    """
    채팅 메시지를 저장합니다.
    role: 'user' 또는 'assistant'
    """
    db_message = ChatMessage(
        session_id = session_id,
        role       = role,
        content    = content,
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

# ────────────────────────────────────────
# 5. 세션 내 메시지 목록 조회 (Read)
# ────────────────────────────────────────
def get_messages_by_session(
    db: Session,
    session_id: int
):
    """
    특정 세션의 메시지 목록을 시간순으로 조회합니다.
    RAG 파이프라인에 대화 히스토리로 전달할 때 사용합니다.
    """
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

# ────────────────────────────────────────
# 6. 채팅 세션 삭제 (Delete)
# ────────────────────────────────────────
def delete_session(
    db: Session,
    session_id: int
):
    """
    세션과 해당 세션의 모든 메시지를 삭제합니다.
    메시지를 먼저 삭제 후 세션을 삭제합니다 (FK 제약 조건).
    """
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.query(ChatSession).filter(ChatSession.session_id == session_id).delete()

    db.commit()
    
# ────────────────────────────────────────
# 7. 세션 요약 저장 (Update)
# ────────────────────────────────────────
def update_session_summary(
    db: Session,
    session_id: int,
    summary: str,
    summarized_until: int
):
    """
    세션의 요약본(summary)과 요약 완료 지점(summarized_until)을 갱신합니다.
    summarized_until: 요약에 포함된 마지막 message_id.
    """
    db.query(ChatSession).filter(ChatSession.session_id == session_id).update({
        ChatSession.summary: summary,
        ChatSession.summarized_until: summarized_until,
    })
    db.commit()

# ─────────────────────────────────────────────────
# 8. 세션 메시지 조회 — 요약 지점 이후만 (Read)
# ─────────────────────────────────────────────────
def get_messages_after(
    db: Session,
    session_id: int,
    after_message_id: Optional[int]
):
    """
    summarized_until 이후에 쌓인 원문 메시지만 시간순으로 조회합니다.
    after_message_id가 None이면 전체 메시지를 반환합니다.
    """
    query = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
    )
    if after_message_id is not None:
        query = query.filter(ChatMessage.message_id > after_message_id)

    return query.order_by(ChatMessage.created_at.asc()).all()
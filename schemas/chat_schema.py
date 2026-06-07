from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# ─────────────────────────
# 1. 채팅 요청 스키마
# ─────────────────────────
class ChatRequest(BaseModel):
    """
    사용자가 챗봇에 질문을 보낼 때 사용하는 데이터 구조입니다.
    """
    session_id : Optional[int]
    message    : str

# ─────────────────────────
# 2. 메시지 응답 스키마
# ─────────────────────────
class ChatMessageOut(BaseModel):
    """
    채팅 메시지 단건을 응답할 때 사용하는 데이터 구조입니다.
    """
    message_id : int
    role       : str
    content    : str
    created_at : Optional[datetime]

    model_config = {"from_attributes": True}

# ─────────────────────────
# 3. 세션 응답 스키마
# ─────────────────────────
class ChatSessionOut(BaseModel):
    """
    채팅 세션 정보를 응답할 때 사용하는 데이터 구조입니다.
    """
    session_id : int
    title      : Optional[str]
    created_at : Optional[datetime]
    messages   : List[ChatMessageOut] = []

    model_config = {"from_attributes": True}
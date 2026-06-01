from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger, String, Text, ForeignKey,
    TIMESTAMP, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base_class import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id : Mapped[int]            = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id    : Mapped[int]            = mapped_column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    title      : Mapped[Optional[str]]  = mapped_column(String(200), nullable=True)
    
    # 대화 요약(compact) 관련
    summary          : Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    summarized_until : Mapped[Optional[int]]  = mapped_column(BigInteger, nullable=True)
    
    created_at : Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, server_default=func.now())

    # relationships
    user     : Mapped["User"]              = relationship(back_populates="sessions")
    messages : Mapped[List["ChatMessage"]] = relationship(back_populates="session")
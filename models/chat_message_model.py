from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Text, String,
    TIMESTAMP, ForeignKey, func, CheckConstraint
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base_class import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="ck_chat_message_role"),
    )

    message_id : Mapped[int]            = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id : Mapped[int]            = mapped_column(BigInteger, ForeignKey("chat_sessions.session_id"), nullable=False)
    role       : Mapped[str]            = mapped_column(String(10), nullable=False)
    content    : Mapped[str]            = mapped_column(Text, nullable=False)
    created_at : Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, server_default=func.now())

    # relationships
    session : Mapped["ChatSession"] = relationship(back_populates="messages")
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    BigInteger, Integer, String, Text,
    TIMESTAMP, func
)
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from db.base_class import Base

class Regulation(Base):
    __tablename__ = "regulations"

    regulation_id    : Mapped[int]               = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    school_id        : Mapped[int]               = mapped_column(Integer, nullable=False, default=1)
    category         : Mapped[str]               = mapped_column(String(50), nullable=False)
    article_no       : Mapped[Optional[str]]     = mapped_column(String(20), nullable=True)
    title            : Mapped[Optional[str]]     = mapped_column(String(200), nullable=True)
    content          : Mapped[str]               = mapped_column(Text, nullable=False)
    revision_history : Mapped[Optional[str]]     = mapped_column(Text, nullable=True)
    embedding        : Mapped[Optional[list]]    = mapped_column(Vector(1024), nullable=True)
    created_at       : Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, server_default=func.now())
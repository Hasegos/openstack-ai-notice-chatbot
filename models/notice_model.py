from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    BigInteger, String, Text,
    TIMESTAMP, ForeignKey, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base_class import Base
from pgvector.sqlalchemy import Vector

class Notice(Base):
    __tablename__ = "notices"

    notice_id    : Mapped[int]                  = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    school_id    : Mapped[int]                  = mapped_column(BigInteger, ForeignKey("schools.school_id"), nullable=False)
    dept_id      : Mapped[Optional[int]]        = mapped_column(BigInteger, ForeignKey("departments.dept_id"), nullable=True)
    title        : Mapped[Optional[str]]        = mapped_column(String(500), nullable=True)
    content      : Mapped[Optional[str]]        = mapped_column(Text, nullable=True)
    summary      : Mapped[Optional[str]]        = mapped_column(Text, nullable=True)
    source_url   : Mapped[Optional[str]]        = mapped_column(String(500), nullable=True)
    # embedding    : Mapped[Optional[List[float]]] = mapped_column(Vector(1024), nullable=True)
    published_at : Mapped[Optional[datetime]]   = mapped_column(TIMESTAMP, nullable=True)
    created_at   : Mapped[Optional[datetime]]   = mapped_column(TIMESTAMP, nullable=True, server_default=func.now())

    # relationships
    school      : Mapped["School"]          = relationship(back_populates="notices")
    department  : Mapped[Optional["Department"]] = relationship(back_populates="notices")
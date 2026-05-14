from datetime import datetime
from typing import List
from sqlalchemy import (
    BigInteger, Boolean, String,
    TIMESTAMP, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base_class import Base

class School(Base):
    __tablename__ = "schools"

    school_id   : Mapped[int]           = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    school_name : Mapped[str]           = mapped_column(String(100), nullable=False, unique=True)
    notice_url  : Mapped[str]           = mapped_column(String(500), nullable=False)
    is_active   : Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    created_at  : Mapped[datetime]      = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    # relationships
    departments : Mapped[List["Department"]] = relationship(back_populates="school")
    users       : Mapped[List["User"]]       = relationship(back_populates="school")
    notices     : Mapped[List["Notice"]]     = relationship(back_populates="school")
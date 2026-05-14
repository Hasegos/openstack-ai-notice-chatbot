from datetime import datetime
from typing import List
from sqlalchemy import (
    BigInteger, Boolean, String,
    TIMESTAMP, ForeignKey, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base_class import Base

class User(Base):
    __tablename__ = "users"

    user_id         : Mapped[int]           = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email           : Mapped[str]           = mapped_column(String(200), nullable=False, unique=True)
    hashed_password : Mapped[str]           = mapped_column(String(200), nullable=False)
    student_number  : Mapped[str]           = mapped_column(String(20),  nullable=False)
    student_name    : Mapped[str]           = mapped_column(String(50),  nullable=False)
    school_id       : Mapped[int]           = mapped_column(BigInteger, ForeignKey("schools.school_id"), nullable=False)
    dept_id         : Mapped[int]           = mapped_column(BigInteger, ForeignKey("departments.dept_id"), nullable=False)
    is_active       : Mapped[bool]          = mapped_column(Boolean, nullable=False, default=True)
    created_at      : Mapped[datetime]      = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    # relationships
    school      : Mapped["School"]           = relationship(back_populates="users")
    department  : Mapped["Department"]       = relationship(back_populates="users")
    sessions    : Mapped[List["ChatSession"]] = relationship(back_populates="user")
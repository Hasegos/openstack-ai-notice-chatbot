from typing import List, Optional
from sqlalchemy import (
    BigInteger, String, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db.base_class import Base

class Department(Base):
    __tablename__ = "departments"

    dept_id    : Mapped[int]            = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    school_id  : Mapped[int]            = mapped_column(BigInteger, ForeignKey("schools.school_id"), nullable=False)
    dept_name  : Mapped[str]            = mapped_column(String(100), nullable=False)
    notice_url : Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    is_active  : Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)

    # relationships
    school  : Mapped["School"]       = relationship(back_populates="departments")
    users   : Mapped[List["User"]]   = relationship(back_populates="department")
    notices : Mapped[List["Notice"]] = relationship(back_populates="department")
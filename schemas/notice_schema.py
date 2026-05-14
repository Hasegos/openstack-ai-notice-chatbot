from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# ─────────────────────
# 1. 공지 응답 스키마
# ─────────────────────
class NoticeOut(BaseModel):
    """
    공지사항 정보를 응답할 때 사용하는 데이터 구조입니다.
    """
    notice_id    : int
    school_id    : int
    dept_id      : Optional[int]
    title        : Optional[str]
    summary      : Optional[str]
    source_url   : Optional[str]
    published_at : Optional[datetime]
    created_at   : Optional[datetime]

    model_config = {"from_attributes": True}

# ───────────────────────
# 2. 공지 상세 응답 스키마
# ───────────────────────
class NoticeDetail(NoticeOut):
    """
    공지사항 원문까지 포함한 상세 응답 스키마입니다.
    """
    content : Optional[str]
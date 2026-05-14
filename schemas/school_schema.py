from pydantic import BaseModel

# ─────────────────────
# 1. 학교 응답 스키마
# ─────────────────────
class SchoolOut(BaseModel):
    """
    학교 정보를 응답할 때 사용하는 데이터 구조입니다.
    """
    school_id   : int
    school_name : str
    notice_url  : str
    is_active   : bool

    model_config = {"from_attributes": True}
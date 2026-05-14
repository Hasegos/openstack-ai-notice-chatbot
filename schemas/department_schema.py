from pydantic import BaseModel

# ─────────────────────
# 1. 학과 응답 스키마
# ─────────────────────
class DepartmentOut(BaseModel):
    """
    학과 정보를 응답할 때 사용하는 데이터 구조입니다.
    """
    dept_id    : int
    school_id  : int
    dept_name  : str
    is_active  : bool

    model_config = {"from_attributes": True}
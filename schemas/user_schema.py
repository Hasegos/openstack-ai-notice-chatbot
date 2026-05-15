import re

from pydantic import BaseModel, field_validator

# ─────────────────
# 1. 로그인 스키마
# ─────────────────
class UserLogin(BaseModel):
    """
    로그인 시 입력받는 데이터의 규격과 형식을 검증합니다.
    """
    username : str
    password : str

    # ──────────────────────
    # 1-1. 이메일 형식 검증
    # ──────────────────────
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, v):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return v

# ───────────────────
# 2. 회원가입 스키마
# ───────────────────
class UserCreate(UserLogin):
    """
    로그인 스키마를 상속받아 이메일 검증을 유지하며,
    추가 회원 정보와 비밀번호 복잡성 검사를 수행합니다.
    """
    student_name   : str
    student_number : str
    school_id      : int
    dept_id        : int

    # ──────────────────────────
    # 2-1. 비밀번호 복잡성 검증
    # ──────────────────────────
    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        password_regex = r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'
        if not re.match(password_regex, v):
            raise ValueError("비밀번호는 영문, 숫자, 특수문자를 포함하여 8자 이상이어야 합니다.")
        return v

    # ──────────────────────────
    # 2-2. 이름 검증
    # ──────────────────────────
    @field_validator("student_name")
    @classmethod
    def validate_student_name(cls, v: str) -> str:
        v = v.strip()
        
        if not v:
            raise ValueError("이름을 입력해주세요.")

        if len(v) < 2 or len(v) > 30:
            raise ValueError("이름은 2자 이상 30자 이하로 입력해주세요.")

        # 한글, 영문, 공백만 허용
        if not re.match(r'^[가-힣a-zA-Z\s]+$', v):
            raise ValueError("이름은 한글 또는 영문만 입력 가능합니다.")

        # SQL 인젝션 패턴 차단
        sql_injection_pattern = r"(--|;|'|\"|\/\*|\*\/|xp_|UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)"
        if re.search(sql_injection_pattern, v, re.IGNORECASE):
            raise ValueError("허용되지 않는 문자가 포함되어 있습니다.")
    
        return v

    # ──────────────────────────
    # 2-3. 학번 검증
    # ──────────────────────────
    @field_validator("student_number")
    @classmethod
    def validate_student_number(cls, v: str) -> str:
        v = v.strip()

        if not v:
            raise ValueError("학번을 입력해주세요.")
        
        if not re.match(r'^\d{6,12}$', v):
            raise ValueError("학번은 숫자 6~12자리로 입력해주세요.")
            
        return v

# ───────────────────
# 3. 사용자 응답 스키마
# ───────────────────
class UserOut(BaseModel):
    """
    사용자 정보를 응답할 때 사용하는 데이터 구조입니다.
    비밀번호는 절대 포함하지 않습니다.
    """
    user_id        : int
    email       : str
    student_name   : str
    student_number : str
    school_id      : int
    dept_id        : int
    is_active      : bool

    model_config = {"from_attributes": True}
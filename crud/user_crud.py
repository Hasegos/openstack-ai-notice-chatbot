from sqlalchemy.orm import Session

from models.user_model import User
from core.security import verify_password, get_password_hash
from schemas.user_schema import UserCreate

# ────────────────────────────
# 1. 신규 사용자 생성 (Create)
# ────────────────────────────
def create_user(
    db: Session,
    user_in: UserCreate
):
    """
    새로운 사용자를 데이터베이스에 등록합니다.
    """
    # 1-1. 비밀번호 암호화
    hashed_pw = get_password_hash(user_in.password)

    # 1-2. DB 모델 객체 생성
    db_user = User(
        email           = user_in.username,
        hashed_password = hashed_pw,
        student_name    = user_in.student_name,
        student_number  = user_in.student_number,
        school_id       = user_in.school_id,
        dept_id         = user_in.dept_id,
    )

    # 1-3. DB 저장 및 동기화
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ─────────────────────
# 2. 사용자 조회 (Read)
# ─────────────────────
def get_user_by_email(
    db: Session,
    email: str
):
    """
    이메일을 기준으로 특정 사용자를 조회합니다.
    """
    return db.query(User).filter(User.email == email).first()

# ──────────────────────────
# 3. 사용자 ID 조회 (Read)
# ──────────────────────────
def get_user_by_id(
    db: Session,
    user_id: int
):
    """
    user_id를 기준으로 특정 사용자를 조회합니다.
    """
    return db.query(User).filter(User.user_id == user_id).first()

# ──────────────────────────────
# 4. 사용자 인증 (Authenticate)
# ──────────────────────────────
def authenticate_user(
    db: Session,
    email: str,
    password: str
):
    """
    로그인 시 이메일과 비밀번호를 검증합니다.
    """
    # 4-1. 사용자 존재 여부 확인
    db_user = get_user_by_email(db, email)
    if not db_user:
        return False

    # 4-2. 암호화된 비밀번호 비교 검증
    if not verify_password(password, db_user.hashed_password):
        return False

    return db_user
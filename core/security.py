import jwt

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext

from .config import settings

# ──────────────────────────────
# 1. 비밀번호 해싱 설정 (BCrypt)
# ──────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """평문 비밀번호를 해시화하여 반환합니다."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력된 비밀번호와 DB의 해시값을 비교 검증합니다."""
    return pwd_context.verify(plain_password, hashed_password)

# ────────────────────────
# 2. JWT 액세스 토큰 생성
# ────────────────────────
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    사용자 데이터를 담은 JWT 토큰을 생성합니다.
    """
    to_encode = data.copy()
    
    # ──────────────────────────
    # 2-1. 토큰 만료 시간 계산
    # ──────────────────────────
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # settings에 정의된 기본 만료 시간(예: 30분) 사용
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    # ──────────────────────────
    # 2-2. JWT 서명 및 인코딩
    # ──────────────────────────
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

# ──────────────────────────
# 3. JWT 토큰 복호화 및 검증
# ──────────────────────────
def decode_access_token(token: str):
    """
    전달받은 토큰의 유효성을 검증하고 페이로드를 반환합니다.
    """
    try:
        # ──────────────────────────
        # 3-1. 토큰 디코딩 시도
        # ──────────────────────────
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload

    except jwt.ExpiredSignatureError:
        # 토큰 유효 기간이 만료된 경우
        return "expired"
    
    except jwt.InvalidTokenError:
        # 서명이 일치하지 않거나 구조가 잘못된 토큰일 경우
        return "invalid"
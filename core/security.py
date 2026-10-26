import jwt

from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization

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

# ──────────────────────────────────────
# 4. UC Info 앱 토큰 검증 (ES256 공개키)
# ──────────────────────────────────────
def load_ucinfo_public_key(pem_or_base64: str):
    """
    PEM 문자열 또는 헤더 없는 Base64(X.509 DER) 공개키를 키 객체로 변환합니다.
    키 형식이 잘못되면 예외가 발생합니다.
    """
    body = pem_or_base64.strip()
    if "-----BEGIN" not in body:
        body = f"-----BEGIN PUBLIC KEY-----\n{body}\n-----END PUBLIC KEY-----"
    return serialization.load_pem_public_key(body.encode())

# 기동 시 1회 로드 — 키가 잘못되면 서버가 뜨지 않도록 해 401 연쇄를 막습니다.
_UCINFO_PUBLIC_KEY = (
    load_ucinfo_public_key(settings.UCINFO_JWT_PUBLIC_KEY)
    if settings.UCINFO_JWT_PUBLIC_KEY else None
)

def decode_ucinfo_token(token: str):
    """
    UC Info(Spring)가 발급한 ES256 토큰을 검증하고 페이로드를 반환합니다.
    실패 시 decode_access_token과 동일하게 "expired" / "invalid"를 반환합니다.
    """
    if _UCINFO_PUBLIC_KEY is None:
        return "invalid"
    try:
        return jwt.decode(token, _UCINFO_PUBLIC_KEY, algorithms=["ES256"])
    except jwt.ExpiredSignatureError:
        return "expired"
    except jwt.InvalidTokenError:
        return "invalid"
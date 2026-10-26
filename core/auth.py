from fastapi import Request, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Optional

from db.session import get_db
from crud.user_crud import get_user_by_email, get_or_create_ucinfo_user
from crud.department_crud import get_department_by_name
from .config import settings
from .security import decode_access_token, decode_ucinfo_token

# ─────────────────────────────────────────────────
# 1. 선택적 사용자 인증 (페이지 라우터용)
# ─────────────────────────────────────────────────
# 쿠키에 토큰이 없거나 유효하지 않으면 None을 반환합니다.
# 페이지 접근 제어(리다이렉트)에 사용합니다.
# ─────────────────────────────────────────────────
async def get_current_user_optional(request: Request) -> Optional[str]:
    """
    쿠키에서 JWT를 읽어 유효하면 username(email)을 반환합니다.
    토큰이 없거나 만료/변조된 경우 None을 반환합니다.
    """
    # ──────────────────────────────
    # 1-1. 쿠키에서 액세스 토큰 추출
    # ──────────────────────────────
    token = request.cookies.get("access_token")
    if not token:
        return None

    # ──────────────────────────────
    # 1-2. 토큰 복호화 및 유효성 검증
    # ──────────────────────────────
    payload = decode_access_token(token)
    if payload in ("expired", "invalid"):
        return None

    # ──────────────────────────────
    # 1-3. sub(username) 추출 및 반환
    # ──────────────────────────────
    username: Optional[str] = payload.get("sub")
    return username

# ─────────────────────────────────────────────────
# 2. 필수 사용자 인증 (API 엔드포인트용)
# ─────────────────────────────────────────────────
# 토큰이 없거나 유효하지 않으면 401을 반환합니다.
# Depends(get_current_user)로 보호된 API에 주입합니다.
# ─────────────────────────────────────────────────
async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    쿠키에서 JWT를 읽어 유효하면 DB에서 사용자 객체를 조회하여 반환합니다.
    토큰이 없거나 유효하지 않으면 401을 반환합니다.
    보호된 API 엔드포인트에 Depends로 주입합니다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
    )

    # ─────────────────────────────────────────────
    # 2-0. UC Info 앱 Bearer 토큰 (ES256) 우선 처리
    # ─────────────────────────────────────────────
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return _get_ucinfo_user(db, auth_header[7:], credentials_exception)

    # ─────────────────────────────────
    # 2-1. 쿠키에서 액세스 토큰 추출
    # ─────────────────────────────────
    token = request.cookies.get("access_token")
    if not token:
        raise credentials_exception
    
    # ─────────────────────────────────
    # 2-2. 토큰 복호화 및 유효성 검증
    # ─────────────────────────────────
    payload = decode_access_token(token)
    if payload in ("expired", "invalid"):
        raise credentials_exception

    # ──────────────────────────────
    # 2-3. sub(email) 추출
    # ──────────────────────────────
    email: Optional[str] = payload.get("sub")
    if not email:
        raise credentials_exception
    
    # ──────────────────────────────
    # 2-4. DB에서 사용자 조회
    # ──────────────────────────────
    user = get_user_by_email(db, email)
    if not user:
        raise credentials_exception

    # ──────────────────────────────
    # 2-5. 계정 활성화 여부 확인
    # ──────────────────────────────
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다."
        )

    return user

# ─────────────────────────────────────────────────
# 3. UC Info 앱 사용자 인증 (Bearer, ES256)
# ─────────────────────────────────────────────────
# Spring이 발급한 토큰의 sub(학번), dept(학과명)로 섀도 계정을 매핑합니다.
# dept 클레임이 없는 구 토큰은 401 → 앱이 재로그인하여 새 토큰을 받습니다.
# ─────────────────────────────────────────────────
def _get_ucinfo_user(db: Session, token: str, credentials_exception: HTTPException):
    """
    UC Info 앱 토큰을 검증하고 대응하는 챗봇 사용자 객체를 반환합니다.
    """
    payload = decode_ucinfo_token(token)
    if payload in ("expired", "invalid"):
        raise credentials_exception

    student_id: Optional[str] = payload.get("sub")
    dept_name: Optional[str] = payload.get("dept")
    if not student_id or not dept_name:
        raise credentials_exception

    dept = get_department_by_name(db, settings.UCINFO_SCHOOL_ID, dept_name)
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="챗봇이 지원하지 않는 학과입니다."
        )

    user = get_or_create_ucinfo_user(db, student_id, dept)
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다."
        )
    return user
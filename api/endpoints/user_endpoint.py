from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from slowapi.util import get_remote_address

from core.auth import get_current_user
from core.rate_limit import limiter
from core.security import create_access_token
from crud.user_crud import authenticate_user, create_user, get_user_by_email
from db.session import get_db
from schemas.user_schema import UserCreate, UserLogin, UserOut

router = APIRouter()

# ─────────────
# 1. 회원가입
# ─────────────
@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
):
    """
    신규 사용자를 등록합니다.
    이미 존재하는 이메일이면 409를 반환합니다.
    """
    # ──────────────────────────────
    # 1-1. 이메일 중복 검사
    # ──────────────────────────────
    existing_user = get_user_by_email(db, user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다."
        )

    # ──────────────────────────────
    # 1-2. 사용자 생성 및 반환
    # ──────────────────────────────
    return create_user(db, user_in)

# ─────────────
# 2. 로그인
# ─────────────
@router.post(
    "/login",
    status_code=status.HTTP_200_OK
)
@limiter.limit("5/minute", key_func=get_remote_address)
def login(
    request: Request,
    user_in: UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    이메일과 비밀번호를 검증하고 JWT를 쿠키에 발급합니다.
    성공 시 redirect_url을 함께 반환합니다.
    인증 실패 시 401을 반환합니다.
    """
    # ──────────────────────────────
    # 2-1. 이메일 + 비밀번호 검증
    # ──────────────────────────────
    user = authenticate_user(db, user_in.username, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # ──────────────────────────────
    # 2-2. JWT 액세스 토큰 생성
    # ──────────────────────────────
    access_token = create_access_token(data={"sub": user.email})

    # ──────────────────────────────
    # 2-3. HttpOnly 쿠키에 토큰 저장
    # ──────────────────────────────
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,   # JS에서 접근 불가 (XSS 방어)
        samesite="lax",  # CSRF 방어
        secure=False,    # 로컬 개발용 (배포 시 True로 변경)
    )

    # ──────────────────────────────
    # 2-4. 로그인 성공 + 이동 경로 반환
    # ──────────────────────────────
    return {
        "message": "로그인 성공",
        "redirect_url": "/chat"
    }

# ──────────────
# 3. 로그아웃
# ──────────────
@router.post(
    "/logout",
    status_code=status.HTTP_302_FOUND
)
def logout(response: Response):
    """
    쿠키에서 JWT를 삭제하고 메인 페이지로 리다이렉트합니다.
    form 태그 POST 방식과 호환됩니다.
    """
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token", path="/")
    return response

# ─────────────────
# 4. 내 정보 조회
# ─────────────────
@router.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK
)
async def get_me(
    current_user=Depends(get_current_user)
):
    """
    현재 로그인된 사용자의 정보를 반환합니다.
    토큰이 없거나 유효하지 않으면 401을 반환합니다.
    """
    return current_user
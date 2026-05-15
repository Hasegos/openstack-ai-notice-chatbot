from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from core.auth import get_current_user_optional
from core.templates import templates
from crud.school_crud import get_all_schools
from crud.user_crud import get_user_by_email
from db.session import get_db

# ─────────────────────────────────────────
# 페이지 라우터 — HTML 렌더링 전용
# ─────────────────────────────────────────
page_router = APIRouter()

# ───────────────────
# 1. 메인 랜딩 페이지
# ───────────────────
@page_router.get("/")
async def home_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    메인 랜딩 페이지를 렌더링합니다.
    로그인 여부에 따라 nav 버튼을 동적으로 전환합니다.
    """
    email = await get_current_user_optional(request)
    user = get_user_by_email(db, email) if email else None
    schools = get_all_schools(db)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "is_logged_in": user is not None,
            "current_user": user,
            "schools": schools
        }
    )

# ───────────────────
# 2. 로그인 페이지
# ───────────────────
@page_router.get("/login")
async def login_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 로그인 화면을 렌더링합니다.
    이미 로그인된 사용자는 /chat으로 리다이렉트합니다.
    """
    email = await get_current_user_optional(request)
    if email:
        return RedirectResponse(url="/chat", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"is_logged_in": False}
    )


# ───────────────────
# 3. 회원가입 페이지
# ───────────────────
@page_router.get("/register")
async def register_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    사용자 회원가입 화면을 렌더링합니다.
    이미 로그인된 사용자는 /chat으로 리다이렉트합니다.
    """
    email = await get_current_user_optional(request)
    if email:
        return RedirectResponse(url="/chat", status_code=302)

    schools = get_all_schools(db)

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "is_logged_in": False,
            "schools": schools
        }
    )

# ───────────────────
# 4. 채팅 페이지
# ───────────────────
@page_router.get("/chat")
async def chat_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    채팅 메인 화면을 렌더링합니다.
    미로그인 사용자는 /login으로 리다이렉트합니다.
    """
    email = await get_current_user_optional(request)
    if not email:
        return RedirectResponse(url="/login", status_code=302)

    user = get_user_by_email(db, email)

    return templates.TemplateResponse(
        request=request,
        name="chat.html",
        context={
            "is_logged_in": True,
            "current_user": user,
        }
    )

# ───────────────────
# 5. 공지 목록 페이지
# ───────────────────
@page_router.get("/notices")
async def notices_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    공지 목록 화면을 렌더링합니다.
    미로그인 사용자는 /login으로 리다이렉트합니다.
    """
    email = await get_current_user_optional(request)
    if not email:
        return RedirectResponse(url="/login", status_code=302)

    user = get_user_by_email(db, email)

    return templates.TemplateResponse(
        request=request,
        name="notices.html",
        context={
            "is_logged_in": True,
            "current_user": user,
        }
    )
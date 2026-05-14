from fastapi import APIRouter

from .endpoints import user

# ─────────────────────────────────────────
# API 라우터 통합 등록
# ─────────────────────────────────────────
api_router = APIRouter()

# 로그인 / 회원가입 / 로그아웃
api_router.include_router(user.router, prefix="", tags=["users"])
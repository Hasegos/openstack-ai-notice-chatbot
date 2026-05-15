from fastapi import APIRouter

from .endpoints import user_endpoint, school_endpoint, notice_endpoint, chat_endpoint

# ─────────────────────────────────────────
# API 라우터 통합 등록
# ─────────────────────────────────────────
api_router = APIRouter()

# 인증 / 학교조회 / 채팅 / 공지사항
api_router.include_router(user_endpoint.router, prefix="/api/auth", tags=["auth"])
api_router.include_router(school_endpoint.router, prefix="/api/schools", tags=["schools"])
api_router.include_router(notice_endpoint.router, prefix="/api/notices", tags=["notices"])
api_router.include_router(chat_endpoint.router,   prefix="/api/chat",    tags=["chat"])
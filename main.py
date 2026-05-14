from fastapi import FastAPI , Request
from fastapi.staticfiles import StaticFiles

from db.session import engine
from db.base import Base
from core.config import settings
from api.routers import api_router
from core.templates import templates

# ────────────────────────────
# 1. 데이터베이스 테이블 초기화
# ────────────────────────────
# 정의된 모든 SQLAlchemy 모델을 기반으로 데이터베이스 테이블을 생성합니다.
Base.metadata.create_all(bind=engine)

# ────────────────────────────
# 2. FastAPI 앱 인스턴스 설정
# ────────────────────────────
app = FastAPI(title=settings.PROJECT_NAME)

# ──────────────────────────
# 3. 정적 파일 및 라우터 설정
# ──────────────────────────
# 3-1. 정적 파일(CSS, JS, Image 등) 경로 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3-2. API 라우터 포함 (로그인, 회원가입, 대시보드 등)
app.include_router(api_router)

# ──────────────────────────
# 메인 랜딩 페이지
# ──────────────────────────
@app.get("/")
async def root(
    request: Request
):
    """
    메인 랜딩 페이지 렌더링.
    로그인 상태 여부에 따라 nav 버튼을 동적으로 전환합니다.
    """
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "is_logged_in": False,
            "schools": []
        }
    )
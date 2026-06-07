from core.logging_config import setup_logging
setup_logging()  # 다른 모듈의 logger 사용 전에 핸들러 등록

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded

from db.session import engine
from db.base import Base
from core.config import settings
from core.exception import install_errors
from core.rate_limit import limiter, rate_limit_handler
from api.routers import api_router
from api.pages import page_router

# ────────────────────────────
# 1. 데이터베이스 테이블 초기화
# ────────────────────────────
# 정의된 모든 SQLAlchemy 모델을 기반으로 데이터베이스 테이블을 생성합니다.
if settings.AUTO_CREATE_TABLES:
    Base.metadata.create_all(bind=engine)

# ────────────────────────────
# 2. FastAPI 앱 인스턴스 설정
# ────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    docs_url=None,
    redoc_url=None
)

# ──────────────────────────────
# Rate Limiting 미들웨어 등록
# ──────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# ──────────────────────────
# 3. 정적 파일 및 라우터 설정
# ──────────────────────────
# 3-1. 정적 파일(CSS, JS, Image 등) 경로 마운트
app.mount("/static", StaticFiles(directory="static"), name="static")

# 3-2. API 라우터 포함 (로그인, 회원가입, 대시보드 등)
app.include_router(api_router)
app.include_router(page_router)

# ───────────────────
# 4. 예외 처리기 설치
# ───────────────────
# 커스텀 에러 핸들러(401, 404, 500 에러 처리 등)를 등록합니다.
install_errors(app)
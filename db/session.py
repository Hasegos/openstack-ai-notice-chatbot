from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base
from core.config import settings

# ─────────────────────────
# 1. 데이터베이스 엔진 생성
# ─────────────────────────
# pool_pre_ping=True: 연결이 유효한지 주기적으로 체크하여 끊긴 연결을 방지합니다.
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    pool_recycle=settings.POOL_RECYCLE,
    pool_timeout=settings.POOL_TIMEOUT,
)

# ─────────────────────────
# 2. 세션 생성 팩토리 설정
# ─────────────────────────
# autocommit=False: 명시적으로 db.commit()을 호출할 때만 저장됩니다.
# autoflush=False: 쿼리 실행 전 자동으로 flush(동기화) 하는 것을 방지합니다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ───────────────────────────────────────
# 3. 데이터베이스 세션 의존성 (Dependency)
# ───────────────────────────────────────
def get_db():
    """
    각 요청마다 DB 세션을 생성하고, 처리가 끝나면 자동으로 닫아줍니다.
    FastAPI의 Depends(get_db)를 통해 주입받아 사용합니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
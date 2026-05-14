from sqlalchemy.orm import DeclarativeBase

# ───────────────────────────────────────
# SQLAlchemy 선언적 베이스 클래스 정의
# ───────────────────────────────────────
# 모든 ORM 모델이 상속받는 공통 베이스 클래스입니다.
# 이 클래스를 상속받은 모델은 자동으로 Base.metadata에 등록되며,
# Base.metadata.create_all() 호출 시 등록된 모든 테이블이 한 번에 생성됩니다.
class Base(DeclarativeBase):
    """
    모든 SQLAlchemy 모델이 상속받는 베이스 클래스입니다.
    이 클래스를 상속받은 클래스는 자동으로 DB 테이블과 매핑됩니다.
    """
    pass
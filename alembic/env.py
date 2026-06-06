import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 프로젝트 루트를 sys.path에 추가 — core.config, models 임포트 가능하게
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.config import settings
from db.base_class import Base

# 모든 모델을 명시적으로 임포트 — Base.metadata에 테이블 등록
import models.notice_model       # noqa: F401
import models.user_model         # noqa: F401
import models.school_model       # noqa: F401
import models.department_model   # noqa: F401
import models.chat_session_model # noqa: F401
import models.chat_message_model # noqa: F401
import models.regulation_model   # noqa: F401

config = context.config

# .env 기반 DB URL을 alembic.ini의 sqlalchemy.url 대신 주입
config.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드: DB 연결 없이 SQL 스크립트만 생성합니다."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드: 실제 DB에 연결해 마이그레이션을 실행합니다."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

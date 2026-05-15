from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings): 
    # ───────────────────────────
    # 1. 데이터베이스(PostgreSQL)
    # ───────────────────────────
    POSTGRESQL_USERNAME: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_SERVER: str
    POSTGRESQL_PORT: str
    POSTGRESQL_DATABASE: str
    PROJECT_NAME:str = "openstack LLM AI 챗봇"

    # ──────────────────────
    # 2. 보안 및 인증 (JWT)
    # ──────────────────────
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # ──────────────────────────
    # 3. 계산된 프로퍼티 (DB URL)
    # ──────────────────────────
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> str:
        """
        입력된 정보를 바탕으로 SQLAlchemy 접속 URL을 생성합니다.
        """
        return (
            f"postgresql://{self.POSTGRESQL_USERNAME}:{self.POSTGRESQL_PASSWORD}"
            f"@{self.POSTGRESQL_SERVER}:{self.POSTGRESQL_PORT}/{self.POSTGRESQL_DATABASE}"
            f"?client_encoding=utf8"
        )
    
    # ──────────────────────────
    # 4. 환경 설정 로드 구성
    # ──────────────────────────
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

# ───────────────────
# 5. 설정 객체 인스턴스화
# ───────────────────
settings = Settings()
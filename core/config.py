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

    # ──────────────────────
    # 3. LM Studio 모델
    # ──────────────────────
    LM_STUDIO_URL: str
    LM_STUDIO_MODEL: str
    SYSTEM_PROMPT: str = """당신은 대학교 공지사항을 안내하는 AI 어시스턴트입니다.
    학교와 학과의 공지사항을 바탕으로 학생들의 질문에 친절하고 정확하게 답변해주세요.
    현재는 RAG 파이프라인이 연동되기 전 테스트 단계입니다."""
    
    # ──────────────────────────
    # 4. 계산된 프로퍼티 (DB URL)
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
    # 5. 환경 설정 로드 구성
    # ──────────────────────────
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8"
    )

# ───────────────────
# 6. 설정 객체 인스턴스화
# ───────────────────
settings = Settings()
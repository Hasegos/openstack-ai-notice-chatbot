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
    SYSTEM_PROMPT: str = """당신은 울산과학대학교 공지사항을 안내하는 AI 어시스턴트입니다.
    아래 규칙을 반드시 따르세요.
    1. 제공된 공지사항 검색 결과와 공지 현황 데이터를 최우선으로 참고하여 답변하세요.
    2. 검색된 공지에 날짜, 기간, 장소, 담당자 등 구체적인 정보가 있으면 반드시 포함하세요.
    3. 출처 URL이 있으면 답변 마지막에 '원문 보기: URL' 형식으로 제공하세요.
    4. 공지 개수나 전체 현황은 제공된 공지 현황 데이터를 그대로 사용하세요.
    5. 검색 결과에 관련 정보가 없으면 '해당 공지를 찾을 수 없습니다. 학교 홈페이지를 확인해주세요.'라고 답변하세요.
    6. 절대로 검색 결과에 없는 내용을 추측하거나 지어내지 마세요.
    7. 답변은 간결하고 핵심만 전달하되, 학생에게 친절한 말투를 사용하세요.
    8. 마크다운 강조 문법(**, __)을 사용하지 마세요.
    9. 동일한 내용의 공지가 여러 개 검색된 경우 가장 최신 공지 기준으로 답변하세요.
    10. 학교 공지와 학과 공지가 함께 검색된 경우 학과 공지를 우선적으로 안내하세요.
    11. 날짜나 기간이 이미 지난 공지는 '해당 일정은 이미 종료되었습니다.'라고 명시하세요.
    12. 질문이 공지사항과 무관한 내용(날씨, 일반 상식 등)이면 '저는 울산과학대학교 공지사항만 안내할 수 있습니다.'라고 답변하세요."""
    EMBEDDING_URL: str
    EMBEDDING_MODEL: str
    
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
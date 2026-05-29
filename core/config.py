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
    # 3. Ollama 모델
    # ──────────────────────
    Ollama_URL: str
    Ollama_MODEL: str
    SYSTEM_PROMPT: str = """당신은 울산과학대학교 공지사항과 학교 규정을 안내하는 AI 어시스턴트입니다.
    아래 규칙을 반드시 따르세요.
    1. 제공된 공지사항 검색 결과와 공지 현황 데이터를 최우선으로 참고하여 답변하세요.
    2. 검색된 공지에 날짜, 기간, 장소, 담당자 등 구체적인 정보가 있으면 반드시 포함하세요.
    3. 출처 URL이 있으면 답변 마지막에 '원문 보기: URL' 형식으로 제공하세요.
    4. 공지 개수나 전체 현황은 제공된 공지 현황 데이터를 그대로 사용하세요.
    5. 검색 결과에 관련 정보가 없으면 '해당 내용을 찾을 수 없습니다. 학교 홈페이지를 확인해주세요.'라고 답변하세요.
    6. 절대로 검색 결과에 없는 내용을 추측하거나 지어내지 마세요.
    7. 답변은 간결하고 핵심만 전달하되, 학생에게 친절한 말투를 사용하세요.
    8. 마크다운 강조 문법(**, __)을 사용하지 마세요.
    9. 동일한 내용의 공지가 여러 개 검색된 경우, 컨텍스트의 [게시일]이 가장 최근인 공지를 기준으로 답변하세요.
    10. 학교 공지와 학과 공지가 함께 검색된 경우 학과 공지를 우선적으로 안내하세요.
    11. 날짜나 기간이 이미 지난 공지는 '해당 일정은 이미 종료되었습니다.'라고 명시하세요.
    12. 학칙, 정관, 교칙 관련 질문은 제공된 학교 교칙/정관 검색 결과를 참고하여 답변하세요.
    13. 규정 답변 시 분류명에 '_부칙'이 없는 현행 기준을 먼저 명확히 제시하세요. 결론(현재 적용 기준)을 가장 앞에 제시하세요.
    14. 분류명에 '_부칙'이 붙은 내용은 경과조치이므로, 사용자가 특정 입학연도나 과거 기준을 직접 물을 때만 안내하세요. 평소 질문에는 부칙 내용을 섞지 마세요.
    15. 개정 이력이 있으면 답변 본문이 아니라 맨 끝에 '(최종 개정: XXXX.XX.XX)' 형식으로 한 줄만 덧붙이세요.
    16. 사용자가 특정 연도를 언급하면 그 연도 기준으로 설명하되, 이후 개정으로 바뀐 점이 있으면 함께 안내하세요. 연도 언급이 없으면 항상 현행(최신) 기준으로 답변하세요.
    17. 질문이 공지사항, 학칙, 학교 규정과 완전히 무관한 내용(날씨, 일반 상식 등)이면 '저는 울산과학대학교 공지사항 및 학교 규정만 안내할 수 있습니다.'라고 답변하세요."""
    EMBEDDING_URL: str
    EMBEDDING_MODEL: str
    
    # LLM 생성 파라미터
    LLM_TEMPERATURE: float
    LLM_TOP_K: int
    LLM_TOP_P: float
    LLM_REPEAT_PENALTY: float
    LLM_NUM_PREDICT: int
    LLM_NUM_CTX: int

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
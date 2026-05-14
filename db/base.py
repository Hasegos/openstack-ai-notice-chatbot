from db.base_class import Base
from models.school_model import School
from models.department_model import Department
from models.user_model import User
from models.notice_model import Notice
from models.chat_session_model import ChatSession
from models.chat_message_model import ChatMessage

# ─────────────────────────────────────
# 1. 모델 통합 관리 (Alembic/Base 전용)
# ─────────────────────────────────────
# 이 파일은 Alembic 마이그레이션 도구가 모든 모델을 한 번에 인식하게 하거나,
# 애플리케이션 초기화 시 모든 테이블 정의를 로드하기 위해 사용됩니다.

# 1-1. Base: 모든 모델의 부모 클래스
# 1-2. User: 사용자 정보 관련 모델
# 1-3. Notice: 공지사항 관련 모델
# 1-4. Department: 학과 정보 관련 모델
# 1-5. ChatSession: 채팅 세션 관련 모델
# 1-6. ChatMessage: 채팅 메시지 관련 모델
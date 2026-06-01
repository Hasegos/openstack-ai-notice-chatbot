import re

# ─────────────────────────────────────
# 의도 분류 (집계/최신/목록/검색)
# ─────────────────────────────────────
def classify_intent(message: str) -> str:
    """
    질문 의도를 키워드 기반으로 분류합니다.
    """
    msg = message.lower()

    COUNT_KEYWORDS  = ["몇 개", "몇개", "개수", "총", "전체 수", "얼마나"]
    RECENT_KEYWORDS = ["최근", "최신", "새로운", "방금", "최근에", "요즘", "최근 공지"]
    LIST_KEYWORDS   = ["전부", "모두", "다 보여", "목록", "리스트", "전체 목록"]

    if any(k in msg for k in COUNT_KEYWORDS):
        return "count"
    if any(k in msg for k in RECENT_KEYWORDS):
        return "recent"
    if any(k in msg for k in LIST_KEYWORDS):
        return "list"
    return "search"

# ─────────────────────────────────────
# 공지 vs 규정 성향 판단
# ─────────────────────────────────────
def detect_query_type(message: str) -> str:
    """
    질문이 공지성인지 규정성인지 판단합니다.
    - notice:     일정, 신청, 모집 등 시의성 있는 정보
    - regulation: 규정, 기준, 자격 등 제도적 정보
    - both:       둘 다 관련 (기본값)
    """
    msg = message.lower()

    NOTICE_KEYWORDS = [
        "신청", "모집", "일정", "기간", "마감", "접수", "안내",
        "언제", "장학", "행사", "공모", "채용", "설명회", "특강", "공지",
        "프로젝트", "대회", "참여", "프로그램", "캠프", "공모전", "지원", "혜택"
    ]
    REGULATION_KEYWORDS = [
        "규정", "규칙", "학칙", "정관", "기준", "자격", "조항",
        "이수", "졸업요건", "졸업 요건", "휴학", "복학", "제적",
        "징계", "평점", "학점", "등록금", "수업연한", "학사경고"
    ]

    has_notice     = any(k in msg for k in NOTICE_KEYWORDS)
    has_regulation = any(k in msg for k in REGULATION_KEYWORDS)

    if has_regulation and not has_notice:
        return "regulation"
    if has_notice and not has_regulation:
        return "notice"
    return "both"

# ─────────────────────────────────────
# 공지 키워드 추출 (보조 검색용)
# ─────────────────────────────────────
def extract_notice_keywords(message: str) -> list[str]:
    """
    질문에서 공지 키워드 검색에 쓸 핵심 명사를 추출합니다.
    추상적 질문(프로젝트/대회 등)도 키워드로 잡아 보조 검색합니다.
    """
    CANDIDATES = [
        "프로젝트", "대회", "공모전", "공모", "캠프", "프로그램",
        "장학", "장학금", "인턴", "채용", "취업", "설명회", "특강",
        "세미나", "워크숍", "봉사", "동아리", "행사", "축제",
        "멘토링", "교육", "강좌", "스터디", "현장실습", "실습"
    ]
    found = [kw for kw in CANDIDATES if kw in message]
    return found

# ─────────────────────────────────────
# 조항 번호 패턴 감지
# ─────────────────────────────────────
def extract_article_keyword(message: str) -> str | None:
    """
    메시지에서 '제N조', 'N조', 'N조항' 패턴을 감지합니다.
    """
    m = re.search(r'제?(\d+)조', message)
    if m:
        return f"제{m.group(1)}조"
    return None

# ─────────────────────────────────────
# 연도 패턴 감지
# ─────────────────────────────────────
def extract_year_keyword(message: str) -> str | None:
    """
    메시지에서 연도 패턴 감지
    예: '2020년 계절학기', '2019년도 규정'
    """
    m = re.search(r'(\d{4})\s*년', message)
    if m:
        return m.group(1)
    return None
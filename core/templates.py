from fastapi.templating import Jinja2Templates

# ───────────────────
# 1. HTML 템플릿 설정
# ───────────────────
# Jinja2 엔진을 사용하여 'templates' 디렉토리 내의 HTML 파일들을 로드합니다.
templates = Jinja2Templates(directory="templates")
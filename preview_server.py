"""
preview_server.py — DB 없이 홈 화면만 렌더링하는 임시 preview 서버
실제 앱(main.py)과 무관합니다. 확인 후 삭제하세요.
실행: python preview_server.py
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

# 정적 파일 마운트 (CSS · JS · 이미지)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 실제 templates 디렉터리 사용
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    """DB 없이 mock 데이터로 홈 화면 렌더링"""
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "is_logged_in": False,   # 비로그인 상태로 렌더링
            "current_user": None,
            "schools": [],           # 셀렉트박스는 빈 목록
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)

import re
import httpx

from core.config import settings

# ─────────────────────────────────────────────────────
# 임베딩 API 호출
# ─────────────────────────────────────────────────────
async def get_embedding(text: str) -> list[float]:
    """
    임베딩 API를 호출하여 텍스트의 벡터를 반환합니다.
    """
    payload = {
        "model": settings.EMBEDDING_MODEL,
        "prompt": text,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            settings.EMBEDDING_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return data["embedding"]

# ─────────────────────────────────────────────────────
# Ollama 호출
# ─────────────────────────────────────────────────────
async def call_ollama(messages: list[dict]) -> str:
    """
    Ollama 로컬 서버에 chat completion 요청을 보냅니다.
    """
    payload = {
        "model": settings.Ollama_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature":    settings.LLM_TEMPERATURE,
            "top_k":          settings.LLM_TOP_K,
            "top_p":          settings.LLM_TOP_P,
            "repeat_penalty": settings.LLM_REPEAT_PENALTY,
            "num_predict":    settings.LLM_NUM_PREDICT,
            "num_ctx":        settings.LLM_NUM_CTX,
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.Ollama_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            print(f"[Ollama] 상태코드: {response.status_code}")
            print(f"[Ollama] 응답 내용: {response.text}")
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

# ─────────────────────────────────────
# 마크다운 강조 문법 제거 (후처리)
# ─────────────────────────────────────
def strip_markdown(text: str) -> str:
    """
    LLM 답변에서 마크다운 강조 문법을 제거합니다.
    시스템 프롬프트만으로는 모델이 마크다운을 습관적으로 생성하므로
    출력 단계에서 강제로 제거합니다.
    """
    if not text:
        return text
    # **bold**, __bold__ → 일반 텍스트
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # *italic*, _italic_ → 일반 텍스트 (단어 경계 고려)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'\1', text)
    # ### 헤더 기호 제거 (줄 시작의 # 1~6개)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    return text
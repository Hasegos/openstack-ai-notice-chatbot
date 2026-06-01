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

# ─────────────────────────────────────────────────────
# 대화 요약 호출 (compact)
# ─────────────────────────────────────────────────────
async def summarize_conversation(
    previous_summary: str,
    messages_text: str,
) -> str:
    """
    이전 요약본 + 새로 쌓인 대화를 합쳐 하나의 누적 요약본으로 압축합니다.
    Claude의 compact와 동일한 원리로, 오래된 대화를 짧게 유지하기 위해 사용합니다.

    previous_summary : 기존 요약본 (없으면 빈 문자열)
    messages_text    : 이번에 새로 요약할 원문 대화 (역할: 내용 형식)
    """
    # 요약 전용 시스템 프롬프트 (RAG 시스템 프롬프트와 별개)
    summary_system = (
        "당신은 대화 내용을 간결하게 요약하는 역할입니다. "
        "아래 이전 요약과 새 대화를 합쳐, 사용자가 무엇을 물었고 어떤 답변을 받았는지 "
        "핵심만 담은 하나의 요약으로 정리하세요. "
        "사용자의 관심 주제와 미해결 질문이 드러나도록 하고, "
        "불필요한 인사말이나 중복은 제거하세요. 최대 500자 이내로 작성하세요."
    )

    user_content = ""
    if previous_summary:
        user_content += f"[이전 요약]\n{previous_summary}\n\n"
    user_content += f"[새 대화]\n{messages_text}\n\n위 내용을 하나의 요약으로 정리하세요."

    payload = {
        "model": settings.Ollama_MODEL,
        "messages": [
            {"role": "system", "content": summary_system},
            {"role": "user",   "content": user_content},
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,    # 요약은 일관성 위해 낮게 고정
            "num_predict": 1024,   # 요약본은 짧으므로 작게
            "num_ctx":     settings.LLM_NUM_CTX,
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            settings.Ollama_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"].strip()

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
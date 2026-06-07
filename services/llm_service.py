import json, logging, httpx

from core.config import settings

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────
# 임베딩 API 호출 (Redis 캐시 적용)
# ─────────────────────────────────────────────────────
async def get_embedding(text: str) -> list[float]:
    """
    임베딩 API를 호출하여 텍스트의 벡터를 반환합니다.
    """
    logger.info(f"[Embedding] 생성: {text[:50]!r}")

    # ── BGE-M3 임베딩 서버 호출 ──
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
        embedding = data["embedding"]

    return embedding

# ─────────────────────────────────────────────────────
# Ollama 스트리밍 호출
# ─────────────────────────────────────────────────────
async def call_ollama_stream(messages: list[dict]):
    """
    Ollama에 stream=True로 요청하고 토큰 청크를 async generator로 반환합니다.
    strip_markdown은 전체 텍스트 기준 동작하므로 스트리밍에서는 적용하지 않습니다.
    """
    payload = {
        "model":   settings.Ollama_MODEL,
        "messages": messages,
        "stream":  True,
        "options": {
            "temperature":    settings.LLM_TEMPERATURE,
            "top_k":          settings.LLM_TOP_K,
            "top_p":          settings.LLM_TOP_P,
            "repeat_penalty": settings.LLM_REPEAT_PENALTY,
            "num_predict":    settings.LLM_NUM_PREDICT,
            "num_ctx":        settings.LLM_NUM_CTX,
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            settings.Ollama_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                if token:
                    yield token
                if data.get("done"):
                    return

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
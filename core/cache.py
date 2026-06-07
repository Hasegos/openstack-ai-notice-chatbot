import json
import hashlib
import logging
from typing import Optional

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis: Optional[aioredis.Redis] = None

# ─────────────────────────────────────────────────────────
# Redis 클라이언트 싱글턴
# ─────────────────────────────────────────────────────────
def _get_client() -> aioredis.Redis:
    """
    모듈 수준 싱글턴 클라이언트를 반환합니다.
    decode_responses=True 로 bytes 대신 str 반환.
    """
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            "redis://redis:6379",
            decode_responses=True,
        )
    return _redis

# ─────────────────────────────────────────────────────────
# 캐시 키 생성 — SHA-256(query_text) 16진수
# ─────────────────────────────────────────────────────────
def _make_key(query_text: str) -> str:
    digest = hashlib.sha256(query_text.encode()).hexdigest()
    return f"emb:{digest}"

# ─────────────────────────────────────────────────────────
# GET — 캐시에서 임베딩 조회
# ─────────────────────────────────────────────────────────
async def get_cached_embedding(query_text: str) -> Optional[list]:
    """
    캐시 히트 시 list[float] 반환, 미스 또는 Redis 장애 시 None 반환.
    Redis 연결 실패해도 서비스 중단 없이 fallback 처리.
    """
    try:
        client = _get_client()
        raw = await client.get(_make_key(query_text))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"[Cache] GET 실패, fallback 진행: {e}")
        return None

# ─────────────────────────────────────────────────────────
# SET — 임베딩을 캐시에 저장
# ─────────────────────────────────────────────────────────
async def set_cached_embedding(
    query_text: str,
    embedding: list,
    ttl: int = 86400,
) -> None:
    """
    임베딩을 JSON 직렬화하여 TTL과 함께 저장합니다.
    기본 TTL 86400초 (24시간).
    Redis 연결 실패 시 에러 무시하고 통과.
    """
    try:
        client = _get_client()
        await client.setex(_make_key(query_text), ttl, json.dumps(embedding))
    except Exception as e:
        logger.warning(f"[Cache] SET 실패, 무시하고 진행: {e}")

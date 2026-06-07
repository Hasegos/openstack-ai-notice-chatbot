import logging
import jwt

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import settings

logger = logging.getLogger(__name__)


def _get_user_key(request: Request) -> str:
    """
    JWT 쿠키에서 사용자 이메일(sub)을 추출해 rate limit 키로 사용합니다.
    토큰이 없거나 디코딩 실패 시 IP 주소로 fallback합니다.
    서명 검증은 get_current_user 의존성에서 이미 수행하므로 여기서는 생략합니다.
    """
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=[settings.ALGORITHM],
            )
            sub = payload.get("sub")
            if sub:
                return sub
        except Exception:
            logger.debug("Rate limit: JWT 디코딩 실패, IP 주소로 fallback")
    return get_remote_address(request)


# 기본 key_func: 인증 엔드포인트는 사용자 이메일 기준
# 로그인 엔드포인트는 @limiter.limit(..., key_func=get_remote_address) 로 IP 기준 적용
limiter = Limiter(key_func=_get_user_key)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 Too Many Requests 응답에 한국어 메시지를 반환합니다."""
    return JSONResponse(
        status_code=429,
        content={"detail": f"요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요. ({exc.detail})"},
    )

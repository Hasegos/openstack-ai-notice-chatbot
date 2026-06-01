from sqlalchemy.orm import Session

from core.config import settings
from crud.chat_crud import (
    get_messages_after,
    update_session_summary,
)
from services.llm_service import summarize_conversation

# ─────────────────────────────────────
# 토큰 수 추정
# ─────────────────────────────────────
def estimate_tokens(text: str) -> int:
    """
    글자 수 기반으로 토큰 수를 보수적으로 추정합니다.
    정확하지 않지만 트리거 판단용으로는 충분합니다.
    """
    if not text:
        return 0
    return int(len(text) * settings.CHARS_TO_TOKENS)

# ─────────────────────────────────────
# 메시지 리스트를 텍스트로 직렬화
# ─────────────────────────────────────
def messages_to_text(messages: list) -> str:
    """
    ORM 메시지 객체 리스트를 '역할: 내용' 형식의 텍스트로 변환합니다.
    요약 입력용으로 사용합니다.
    """
    lines = []
    for m in messages:
        role_label = "사용자" if m.role == "user" else "어시스턴트"
        lines.append(f"{role_label}: {m.content}")
    return "\n".join(lines)

# ─────────────────────────────────────
# compact 핵심 로직
# ─────────────────────────────────────
async def build_memory_context(
    db: Session,
    session_id: int,
    summary: str | None,
    summarized_until: int | None,
    system_prompt_len: int,
    rag_context_len: int,
) -> tuple[str, list[dict]]:
    """
    세션의 대화 맥락을 구성합니다. (Claude compact 방식)

    동작:
      1. summarized_until 이후의 원문 메시지를 조회
      2. (요약본 + 원문 + 시스템프롬프트 + RAG) 추정 토큰이 num_ctx 70% 초과 시:
         → 오래된 원문을 요약하여 summary에 누적, summarized_until 갱신
      3. 최종적으로 (요약본 + 최근 RECENT_KEEP_COUNT개 원문)을 반환

    반환:
      (memory_summary, recent_messages)
      - memory_summary  : 시스템 프롬프트에 주입할 요약본 문자열 (없으면 "")
      - recent_messages : LLM messages 배열에 넣을 최근 대화 [{role, content}, ...]
    """
    # ─────────────────────────────────────────────────
    # 1. 요약 지점 이후 원문 메시지 조회
    # ─────────────────────────────────────────────────
    after_messages = get_messages_after(db, session_id, summarized_until)
    if after_messages:
        after_messages = after_messages[:-1]

    current_summary  = summary or ""
    current_until    = summarized_until

    # ───────────────────────────────────────────────────────────────
    # 2. 토큰 추정 함수 정의 (요약 + 원문 + 시스템프롬프트 + RAG)
    # ───────────────────────────────────────────────────────────────
    def total_estimated_tokens(summ: str, msgs: list) -> int:
        summ_tokens = estimate_tokens(summ)
        msg_tokens  = sum(estimate_tokens(m.content) for m in msgs)
        fixed_tokens = estimate_tokens_from_len(system_prompt_len) + estimate_tokens_from_len(rag_context_len)
        return summ_tokens + msg_tokens + fixed_tokens

    limit_tokens = int(settings.LLM_NUM_CTX * settings.SUMMARY_TRIGGER_RATIO)

    # ────────────────────────────────────────
    # 3. 트리거 판단 + 요약 실행
    # ────────────────────────────────────────
    if total_estimated_tokens(current_summary, after_messages) > limit_tokens \
       and len(after_messages) > settings.RECENT_KEEP_COUNT:

        # ───────────────────────────────────────────────────────────
        # 3.1 오래된 부분(요약 대상) / 최근 부분(원문 유지) 분리
        # ───────────────────────────────────────────────────────────
        to_summarize = after_messages[:-settings.RECENT_KEEP_COUNT]
        keep_recent  = after_messages[-settings.RECENT_KEEP_COUNT:]

        if to_summarize:
            print(f"[Compact] 요약 트리거 — 대상 {len(to_summarize)}개 메시지 요약 시작")
            summarize_text = messages_to_text(to_summarize)
            try:
                new_summary = await summarize_conversation(current_summary, summarize_text)
                new_until = to_summarize[-1].message_id
                update_session_summary(db, session_id, new_summary, new_until)
                current_summary = new_summary
                current_until   = new_until
                print(f"[Compact] 요약 완료 — summarized_until={new_until}")
            except Exception as e:
                # 요약 실패 시: 요약 없이 원문만 사용 (안전 폴백)
                print(f"[Compact] 요약 실패, 원문 유지: {e}")
                keep_recent = after_messages[-settings.RECENT_KEEP_COUNT:]

        recent_for_llm = keep_recent
    else:
        # 한계 미만: 최근 RECENT_KEEP_COUNT개만 원문으로 사용
        recent_for_llm = after_messages[-settings.RECENT_KEEP_COUNT:]

    # ────────────────────────────────────────
    # 4. 최종 반환 형태 구성
    # ────────────────────────────────────────
    recent_messages = [
        {"role": m.role, "content": m.content}
        for m in recent_for_llm
    ]
    return current_summary, recent_messages

# ─────────────────────────────────────
# 길이(글자수)로부터 토큰 추정 (헬퍼)
# ─────────────────────────────────────
def estimate_tokens_from_len(char_len: int) -> int:
    """이미 글자 수를 알고 있을 때 토큰을 추정합니다."""
    return int(char_len * settings.CHARS_TO_TOKENS)
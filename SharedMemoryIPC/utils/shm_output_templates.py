# -*- coding: utf-8 -*-
"""Task brief and shared output templates (SSOT) for Main → Agent A → Agent B."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict, List, Tuple

from utils.shm_protocol import MARKER_DATA_UNAVAILABLE

INTENT_CODE_MODIFY = "CODE_MODIFY"
INTENT_FACT_RESEARCH = "FACT_RESEARCH"
INTENT_GENERAL_ANSWER = "GENERAL_ANSWER"
INTENT_CLARIFY = "CLARIFY"

TEMPLATE_FACT_REPORT_V1 = "FACT_REPORT_v1"
TEMPLATE_GENERAL_ANSWER_V1 = "GENERAL_ANSWER_v1"
TEMPLATE_CODE_PATCH_V1 = "CODE_PATCH_v1"

OUTPUT_LANGUAGE_KOREAN_RULE = (
    "【출력 언어】\n"
    "마크다운 산출물(.md) 본문은 **한국어(한글)** 로 작성한다.\n"
    "- 섹션 제목(## …)은 아래 양식과 동일하게 유지하고, 표·문단·불릿 **내용**은 한글로 쓴다.\n"
    "- 종목명·인명·URL·티커·숫자·영문 고유명사만 영문 허용. 본문을 영어로 쓰지 마라.\n\n"
)

FACT_RESEARCH_WORKER_RULES = (
    OUTPUT_LANGUAGE_KOREAN_RULE
    + "【사실 조사 모드】\n"
    "1. 웹 검색(인터넷)으로 **최신** 자료를 조회한 뒤 작성하라. 학습 기억의 과거 수치를 단독 근거로 쓰지 마라.\n"
    "2. 수치·시세를 적을 때 **출처 URL(https://…)** 과 **조회 기준일(YYYY-MM-DD)** 를 반드시 병기하라.\n"
    f"3. 확인 불가 항목은 임의로 채우지 말고 '{MARKER_DATA_UNAVAILABLE}' 섹션에만 적어라.\n"
    "4. 내부 추론·도구 사용 과정(영문 monologue, 'I will search' 등)은 **최종 산출물에 넣지 마라**.\n"
    "5. 아래 마크다운 양식의 섹션 제목을 **그대로** 유지하고 내용만 채워라.\n\n"
)

GENERAL_ANSWER_WORKER_RULES = (
    OUTPUT_LANGUAGE_KOREAN_RULE
    + "【일반 답변 모드】\n"
    "1. 아래 마크다운 양식의 섹션 제목을 **그대로** 유지하고 내용만 채워라.\n"
    "2. 사실 주장에는 가능하면 출처를 붙이고, 확실하지 않으면 불확실함을 명시하라.\n"
    "3. 내부 추론·도구 사용 과정 문장은 최종 산출물에 넣지 마라.\n\n"
)

CODE_PATCH_WORKER_RULES = (
    "【코드 수정 모드】\n"
    "1. 워크스페이스 AGENTS.md 및 코딩 룰을 준수하라.\n"
    "2. TODO/FIXME 없이 완결된 패치 또는 설명을 제출하라.\n\n"
)

_TEMPLATES: Dict[str, Dict[str, Any]] = {
    TEMPLATE_FACT_REPORT_V1: {
        "title": "사실·시장 조사 보고서",
        "skeleton": (
            "# {subject} — 사실 조사 보고서\n\n"
            "**조회 기준일:** {as_of_date}\n\n"
            "## 1. 요약 (Executive Summary)\n"
            "(핵심 결론 3~5문장)\n\n"
            "## 2. 데이터 수집 (웹 검색)\n"
            "| 항목 | 내용 | 출처 URL | 조회 기준일 |\n"
            "|------|------|----------|-------------|\n\n"
            "## 3. 본문 분석\n"
            "(검색 결과 기반. 학습 기억 단독 금지)\n\n"
            "## 4. 리스크·한계\n\n"
            f"## 5. {MARKER_DATA_UNAVAILABLE}\n"
            "(확인 불가한 항목만)\n"
        ),
        "required_sections": [
            "## 1. 요약",
            "## 2. 데이터 수집",
            "## 3. 본문 분석",
            "## 4. 리스크",
            f"## 5. {MARKER_DATA_UNAVAILABLE}",
        ],
        "min_criteria": [
            "산출물 본문 한국어(한글) 작성",
            "웹 검색 기반 최신 자료",
            "가격·수치 시 URL + YYYY-MM-DD",
            "내부 monologue 금지",
        ],
    },
    TEMPLATE_GENERAL_ANSWER_V1: {
        "title": "일반 답변",
        "skeleton": (
            "# {subject} — 답변\n\n"
            "## 1. 질문 재진술\n\n"
            "## 2. 핵심 답변\n\n"
            "## 3. 근거·참고 (해당 시)\n\n"
            "## 4. 한계·유의사항\n"
        ),
        "required_sections": [
            "## 1. 질문 재진술",
            "## 2. 핵심 답변",
            "## 3. 근거",
            "## 4. 한계",
        ],
        "min_criteria": [
            "산출물 본문 한국어(한글) 작성",
            "4개 섹션 모두 작성",
            "내부 monologue 금지",
            "최소 분량 150자 이상",
        ],
    },
    TEMPLATE_CODE_PATCH_V1: {
        "title": "코드 수정 결과",
        "skeleton": (
            "# 코드 수정: {subject}\n\n"
            "## 1. 변경 요약\n\n"
            "## 2. 수정 내용\n\n"
            "## 3. 검증·테스트\n"
        ),
        "required_sections": ["## 1. 변경 요약", "## 2. 수정 내용"],
        "min_criteria": ["TODO/FIXME 없음", "워크스페이스 코딩 룰 준수"],
    },
}

_INTERNAL_MONOLOGUE_MARKERS = (
    "the user requests",
    "the user wants",
    "the user provided",
    "the user's reference",
    "i will search",
    "i'll search",
    "i need to gather",
    "i need to ",
    "let me search",
    "the report will include",
    "the report will",
    "a quick search for",
    "검색 스니펫",
    "search results provide",
    "the search tool",
)

WORKER_RETRY_DELIVERABLE_RULES = (
    "\n[필수 재제출 규칙]\n"
    "- 출력 **첫 줄**은 `#` 제목 또는 `## 1.` 섹션으로 시작한다. 그 앞 문장 금지.\n"
    "- `The user`, `I need`, `I will`, `The report will` 등 영문 계획·추론 문장 금지.\n"
    "- 웹 검색·도구 사용 **과정**은 넣지 말고, 양식을 채운 **완성된 한글 보고서만** 제출한다.\n"
)


def _extract_subject(raw_msg: str, intent: str) -> str:
    text = raw_msg.strip()
    patterns = [
        r"([\w가-힣A-Za-z0-9]+)(?:\s*주식)?\s*(?:분석|조사|전망)",
        r"([\w가-힣A-Za-z0-9\s]{2,30}?)(?:\s*에\s*대해|대해)",
        r"(?:关于|about)\s+(.+?)(?:\?|？|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            subj = m.group(1).strip()
            if len(subj) >= 2:
                return subj[:40]
    if intent == INTENT_FACT_RESEARCH:
        return "조사 주제"
    if intent == INTENT_CODE_MODIFY:
        return "코드 작업"
    return "사용자 질문"


def classify_intent(raw_msg: str) -> str:
    """Rule-based intent classification (no LLM)."""
    text = raw_msg.strip()
    if len(text) < 6:
        return INTENT_CLARIFY
    if re.match(r"^(분석|조사|해줘|알려줘|설명해줘|help)$", text, re.IGNORECASE):
        return INTENT_CLARIFY

    coding_keys = ["고쳐", "수정", "에러", "구현", "코드", "fix", "refactor", "bug"]
    if any(k in text.lower() for k in coding_keys) or re.search(
        r"[\w\-_]+\.(?:py|js|mjs|html|css)", text
    ):
        return INTENT_CODE_MODIFY

    fact_keys = [
        "분석",
        "조사",
        "전망",
        "시세",
        "주가",
        "주식",
        "코인",
        "etf",
        "실적",
        "공시",
        "뉴스",
        "비교",
        "검색",
        "latest",
        "stock",
        "price",
    ]
    if any(k in text.lower() for k in fact_keys):
        return INTENT_FACT_RESEARCH

    return INTENT_GENERAL_ANSWER


def _template_for_intent(intent: str) -> str:
    if intent == INTENT_FACT_RESEARCH:
        return TEMPLATE_FACT_REPORT_V1
    if intent == INTENT_CODE_MODIFY:
        return TEMPLATE_CODE_PATCH_V1
    return TEMPLATE_GENERAL_ANSWER_V1


def build_task_brief(dto: Dict[str, Any], raw_msg: str) -> Dict[str, Any]:
    """Build Main plan text, worker prompt, and reviewer rubric for this turn."""
    intent = dto.get("intent") or classify_intent(raw_msg)
    template_id = _template_for_intent(intent)
    meta = _TEMPLATES[template_id]
    subject = _extract_subject(raw_msg, intent)
    as_of = date.today().isoformat()

    skeleton = meta["skeleton"].format(subject=subject, as_of_date=as_of)

    if intent == INTENT_CLARIFY:
        clarify = (
            "질문이 다소 짧거나 대상이 불명확합니다. 아래를 알려주시면 작업을 시작하겠습니다.\n"
            "- 무엇을 알고 싶은지 (주제·종목·파일)\n"
            "- 사실 조사 vs 설명 vs 코드 수정 중 무엇인지\n"
            "- 필요한 출력 형식(짧은 답변 / 보고서)"
        )
        return {
            "intent": intent,
            "templateId": "CLARIFY_v1",
            "subject": subject,
            "main_plan_text": f"📋 [사령관] 추가 정보 필요\n\n{clarify}",
            "worker_prompt": "",
            "required_sections": [],
            "min_criteria": [],
            "output_filename_stem": "clarify",
            "skip_worker": True,
            "clarify_response": clarify,
        }

    if intent == INTENT_FACT_RESEARCH:
        rules = FACT_RESEARCH_WORKER_RULES
    elif intent == INTENT_CODE_MODIFY:
        rules = CODE_PATCH_WORKER_RULES
    else:
        rules = GENERAL_ANSWER_WORKER_RULES

    min_criteria: List[str] = list(meta["min_criteria"])
    research_method = "none"
    if intent == INTENT_FACT_RESEARCH:
        research_method = "web_search_required"

    main_plan = (
        f"📋 [사령관 작업 지시서]\n"
        f"- 유형: {intent}\n"
        f"- 주제: {subject}\n"
        f"- 산출 양식: {template_id} ({meta['title']})\n"
        f"- 조사 방법: {research_method}\n"
    )
    if intent in (INTENT_FACT_RESEARCH, INTENT_GENERAL_ANSWER):
        main_plan += "- 출력 언어: **한국어(한글)** — .md 본문·표 내용\n"
    main_plan += (
        f"- 최소 기준:\n"
        + "".join(f"  · {c}\n" for c in min_criteria)
        + f"\n[Agent A 지시 요약]\n"
        f"아래 마크다운 골격을 채운 **완성본만** 제출하라."
    )

    worker_prompt = (
        f"{rules}"
        f"=== Task Brief ===\n"
        f"templateId: {template_id}\n"
        f"subject: {subject}\n"
        f"minCriteria: {min_criteria}\n\n"
        f"=== Output skeleton (fill every section) ===\n"
        f"{skeleton}\n\n"
        f"=== User request (context) ===\n"
        f"{raw_msg.strip()}\n"
    )

    stem = re.sub(r"[^\w가-힣]+", "_", subject).strip("_")[:30] or "response"
    if intent == INTENT_FACT_RESEARCH:
        stem = f"{stem}_fact"
    elif intent == INTENT_GENERAL_ANSWER:
        stem = f"{stem}_answer"
    elif intent == INTENT_CODE_MODIFY:
        stem = f"{stem}_code"

    return {
        "intent": intent,
        "templateId": template_id,
        "subject": subject,
        "targetFile": dto.get("targetFile"),
        "main_plan_text": main_plan,
        "worker_prompt": worker_prompt,
        "required_sections": list(meta["required_sections"]),
        "min_criteria": min_criteria,
        "output_filename_stem": stem,
        "skip_worker": False,
        "clarify_response": "",
    }


def should_persist_artifact(brief: Dict[str, Any]) -> bool:
    """CLARIFY / skip_worker flows are chat-only; do not write output/*.md."""
    if brief.get("skip_worker"):
        return False
    if brief.get("intent") == INTENT_CLARIFY:
        return False
    return True


def output_filename_from_brief(brief: Dict[str, Any], date_suffix: str) -> str:
    """Build output/*.md filename from task brief."""
    stem = brief.get("output_filename_stem", "response")
    tid = brief.get("templateId", "")
    if brief.get("intent") == INTENT_CODE_MODIFY:
        target = brief.get("targetFile")
        if target and str(target).endswith((".py", ".js", ".mjs", ".md")):
            return str(target)
        return f"{stem}_{date_suffix}.md"
    if tid == TEMPLATE_FACT_REPORT_V1:
        return f"{stem}_report_{date_suffix}.md"
    return f"{stem}_{date_suffix}.md"


def has_internal_monologue(text: str) -> bool:
    lower = text.lower()
    return any(m in lower for m in _INTERNAL_MONOLOGUE_MARKERS)


def _deliverable_start_index(text: str, required_sections: List[str]) -> int:
    """Index of first markdown deliverable anchor (H1 or required ## section)."""
    anchors: List[int] = []
    for match in re.finditer(r"(?m)^#\s+\S", text):
        anchors.append(match.start())
    for sec in required_sections:
        key = sec.split("(")[0].strip()
        idx = text.find(key)
        if idx >= 0:
            anchors.append(idx)
    return min(anchors) if anchors else -1


def sanitize_worker_output(text: str, brief: Dict[str, Any]) -> str:
    """Strip SDK preamble/monologue before the markdown deliverable."""
    raw = (text or "").strip()
    if not raw:
        return raw

    required = list(brief.get("required_sections") or [])
    start = _deliverable_start_index(raw, required)
    if start > 0:
        raw = raw[start:].lstrip()

    if has_internal_monologue(raw):
        lower = raw.lower()
        for marker in _INTERNAL_MONOLOGUE_MARKERS:
            pos = lower.find(marker)
            if pos < 0:
                continue
            tail = raw[pos:]
            retry_start = _deliverable_start_index(tail, required)
            if retry_start > 0:
                raw = tail[retry_start:].lstrip()
                break

    return raw.strip()


def is_monologue_reject_reason(reason: str) -> bool:
    return "내부 추론" in reason or "monologue" in reason.lower()

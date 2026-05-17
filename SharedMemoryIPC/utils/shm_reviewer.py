# -*- coding: utf-8 -*-
"""Agent B reviewer: template rubric, code lint, and fact-check gates."""

import logging
import re
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from utils.shm_output_templates import (
    INTENT_CODE_MODIFY,
    INTENT_FACT_RESEARCH,
    INTENT_GENERAL_ANSWER,
    has_internal_monologue,
)
from utils.shm_protocol import MARKER_DATA_UNAVAILABLE

logger = logging.getLogger("SharedMemoryIPC.Reviewer")

MIN_FACT_CHARS = 100
MIN_GENERAL_CHARS = 150
PRICE_KRW_PATTERN = re.compile(r"\d{1,3}(?:,\d{3})+\s*원")
ISO_DATE_PATTERN = re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}")
SOURCE_MARKERS = (
    "출처",
    "source:",
    "source ",
    "references:",
    "참고:",
    "조회일",
    "기준일",
    "as of",
    "as-of",
    "웹 검색",
    "web search",
    MARKER_DATA_UNAVAILABLE,
)


class ShmReviewer:
    """Reviews Agent A output against the same Task Brief rubric as Main."""

    def review(
        self,
        dto: Dict[str, Any],
        output_text: str,
        workspace: str,
        brief: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        text = output_text or ""
        if not text.strip():
            return False, "Worker 출력이 비어 있습니다."

        intent = (brief or {}).get("intent") or dto.get("intent", INTENT_GENERAL_ANSWER)
        required = (brief or {}).get("required_sections") or []

        missing = self._missing_sections(text, required)
        if missing:
            return False, f"필수 섹션 누락: {', '.join(missing[:3])}"

        if has_internal_monologue(text):
            return False, "내부 추론·검색 과정 문장이 포함되어 있습니다. 완성된 산출물만 제출하십시오."

        if intent == INTENT_CODE_MODIFY:
            return self._review_code(text, workspace)
        if intent == INTENT_FACT_RESEARCH:
            return self._review_fact(text)
        return self._review_general(text)

    def _missing_sections(self, text: str, required: List[str]) -> List[str]:
        missing = []
        for sec in required:
            key = sec.split("(")[0].strip()
            if key not in text:
                missing.append(sec)
        return missing

    def _review_code(self, text: str, workspace: str) -> Tuple[bool, str]:
        if "TODO" in text or "FIXME" in text:
            return False, "코드 내부에 미완성 주석(TODO, FIXME)이 식별되었습니다."
        ruff_reason = self._run_ruff(workspace)
        if ruff_reason:
            return False, ruff_reason
        return True, ""

    def _run_ruff(self, workspace: str) -> str:
        try:
            proc = subprocess.run(
                ["ruff", "check", workspace],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError:
            logger.warning("[Reviewer] ruff not found on PATH; skipping lint gate")
            return ""
        except subprocess.TimeoutExpired:
            return "Ruff 린트 검사가 시간 초과되었습니다."
        if proc.returncode == 0:
            return ""
        summary = (proc.stdout or proc.stderr or "").strip()
        if len(summary) > 500:
            summary = summary[:500] + "…"
        return f"Ruff 린트 검증 실패:\n{summary}"

    def _review_fact(self, text: str) -> Tuple[bool, str]:
        if MARKER_DATA_UNAVAILABLE in text:
            if self._looks_like_unsourced_prices(text):
                return (
                    False,
                    f"'{MARKER_DATA_UNAVAILABLE}'와 함께 출처 없는 가격 수치를 포함할 수 없습니다.",
                )
            return True, ""
        if len(text) < MIN_FACT_CHARS:
            return (
                False,
                "조사 보고서가 너무 짧습니다. 양식 섹션을 채우거나 DATA_UNAVAILABLE을 사용하십시오.",
            )
        if self._looks_like_unsourced_prices(text):
            return (
                False,
                "시세·가격에 웹 검색 출처 URL과 조회 기준일(YYYY-MM-DD)이 없습니다.",
            )
        return True, ""

    def _review_general(self, text: str) -> Tuple[bool, str]:
        if len(text) < MIN_GENERAL_CHARS:
            return False, f"답변이 너무 짧습니다 (최소 {MIN_GENERAL_CHARS}자)."
        return True, ""

    def _looks_like_unsourced_prices(self, text: str) -> bool:
        if not PRICE_KRW_PATTERN.search(text):
            return False
        lower = text.lower()
        has_label = any(marker.lower() in lower for marker in SOURCE_MARKERS)
        has_url = "http://" in lower or "https://" in lower
        has_as_of_date = bool(ISO_DATE_PATTERN.search(text))
        return not (has_label and has_url and has_as_of_date)

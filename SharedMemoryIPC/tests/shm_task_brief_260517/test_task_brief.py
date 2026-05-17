# -*- coding: utf-8 -*-
"""Task brief and intent classification tests."""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_output_templates import (
    INTENT_CLARIFY,
    INTENT_CODE_MODIFY,
    INTENT_FACT_RESEARCH,
    INTENT_GENERAL_ANSWER,
    TEMPLATE_FACT_REPORT_V1,
    TEMPLATE_GENERAL_ANSWER_V1,
    build_task_brief,
    classify_intent,
    has_internal_monologue,
    sanitize_worker_output,
    should_persist_artifact,
)
from utils.shm_reviewer import ShmReviewer


class TestTaskBrief(unittest.TestCase):
    def test_classify_fact_research(self):
        self.assertEqual(classify_intent("하이닉스 주식 전망 분석해줘"), INTENT_FACT_RESEARCH)

    def test_classify_general(self):
        self.assertEqual(classify_intent("인공지능의 미래에 대해 설명해줘"), INTENT_GENERAL_ANSWER)

    def test_classify_code(self):
        self.assertEqual(classify_intent("api.py 45라인 에러 고쳐줘"), INTENT_CODE_MODIFY)

    def test_classify_clarify(self):
        self.assertEqual(classify_intent("분석"), INTENT_CLARIFY)

    def test_brief_fact_has_sections_and_worker_prompt(self):
        dto = {"intent": INTENT_FACT_RESEARCH, "targetFile": None, "instruction": "삼성전자 조사"}
        brief = build_task_brief(dto, "삼성전자 최근 실적 조사해줘")
        self.assertEqual(brief["templateId"], TEMPLATE_FACT_REPORT_V1)
        self.assertIn("## 1. 요약", brief["worker_prompt"])
        self.assertIn("한국어", brief["worker_prompt"])
        self.assertIn("한국어", brief["main_plan_text"])
        self.assertFalse(brief["skip_worker"])
        self.assertIn("사령관 작업 지시서", brief["main_plan_text"])

    def test_brief_general_template(self):
        dto = {"intent": INTENT_GENERAL_ANSWER}
        brief = build_task_brief(dto, "블록체인이 뭐야?")
        self.assertEqual(brief["templateId"], TEMPLATE_GENERAL_ANSWER_V1)

    def test_brief_clarify_skips_worker(self):
        dto = {"intent": INTENT_CLARIFY}
        brief = build_task_brief(dto, "해줘")
        self.assertTrue(brief["skip_worker"])
        self.assertEqual(brief["worker_prompt"], "")
        self.assertFalse(should_persist_artifact(brief))

    def test_should_persist_artifact_for_fact_research(self):
        brief = build_task_brief(
            {"intent": INTENT_FACT_RESEARCH},
            "삼성전자 실적 조사",
        )
        self.assertTrue(should_persist_artifact(brief))

    def test_reviewer_rejects_monologue(self):
        reviewer = ShmReviewer()
        brief = build_task_brief(
            {"intent": INTENT_GENERAL_ANSWER},
            "테스트",
        )
        text = (
            "## 1. 질문 재진술\nq\n## 2. 핵심 답변\n"
            "The user requests analysis. I will search the web. "
            + "x" * 160
            + "\n## 3. 근거·참고\nn\n## 4. 한계·유의사항\nn"
        )
        ok, reason = reviewer.review({"intent": INTENT_GENERAL_ANSWER}, text, ".", brief)
        self.assertFalse(ok)
        self.assertIn("내부 추론", reason)

    def test_has_internal_monologue_helper(self):
        self.assertTrue(has_internal_monologue("The user requests foo"))

    def test_sanitize_strips_preamble_before_h1(self):
        brief = build_task_brief(
            {"intent": INTENT_FACT_RESEARCH},
            "하이닉스 분석",
        )
        raw = (
            "The user requests a factual report.\n"
            "I need to gather data.\n\n"
            "# 하이닉스 — 사실 조사 보고서\n\n"
            "## 1. 요약\n\n"
            "핵심 결론입니다." + "x" * 80
        )
        cleaned = sanitize_worker_output(raw, brief)
        self.assertTrue(cleaned.startswith("# 하이닉스"))
        self.assertFalse(has_internal_monologue(cleaned))

    def test_sanitize_keeps_code_patch_when_no_preamble(self):
        brief = build_task_brief(
            {"intent": INTENT_CODE_MODIFY},
            "api.py 수정",
        )
        body = "## 1. 변경 요약\n\nok\n\n## 2. 수정 내용\n\ncode"
        self.assertEqual(sanitize_worker_output(body, brief), body)


if __name__ == "__main__":
    unittest.main()

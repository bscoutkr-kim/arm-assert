# -*- coding: utf-8 -*-
"""ShmReviewer unit tests."""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_output_templates import INTENT_CODE_MODIFY, INTENT_FACT_RESEARCH
from utils.shm_protocol import MARKER_DATA_UNAVAILABLE
from utils.shm_reviewer import ShmReviewer

TEMP_WS = os.path.dirname(__file__)


class TestShmReviewer(unittest.TestCase):
    def setUp(self):
        self.reviewer = ShmReviewer()

    def test_rejects_todo_in_code(self):
        dto = {"intent": INTENT_CODE_MODIFY}
        brief = {"intent": INTENT_CODE_MODIFY, "required_sections": []}
        ok, reason = self.reviewer.review(dto, "x = 1  # TODO fix", TEMP_WS, brief)
        self.assertFalse(ok)
        self.assertIn("TODO", reason)

    def test_rejects_unsourced_price_in_research(self):
        dto = {"intent": INTENT_FACT_RESEARCH}
        brief = {"intent": INTENT_FACT_RESEARCH, "required_sections": []}
        ok, reason = self.reviewer.review(
            dto,
            "삼성전자 현재가 78,200원입니다. 매수 권고." + "x" * 80,
            TEMP_WS,
            brief,
        )
        self.assertFalse(ok)
        self.assertIn("URL", reason)

    def test_accepts_price_with_url_and_date(self):
        dto = {"intent": INTENT_FACT_RESEARCH}
        brief = {"intent": INTENT_FACT_RESEARCH, "required_sections": []}
        text = (
            "삼성전자(005930) 현재가 72,100원\n"
            "출처: https://finance.example.com/quote/005930\n"
            "조회 기준일: 2026-05-17\n"
            + "x" * 80
        )
        ok, _ = self.reviewer.review(dto, text, TEMP_WS, brief)
        self.assertTrue(ok)

    def test_accepts_data_unavailable_marker(self):
        dto = {"intent": INTENT_FACT_RESEARCH}
        brief = {"intent": INTENT_FACT_RESEARCH, "required_sections": []}
        text = f"{MARKER_DATA_UNAVAILABLE}\n실시장 API 미연동으로 수치 제공 불가." + "x" * 50
        ok, _ = self.reviewer.review(dto, text, TEMP_WS, brief)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()

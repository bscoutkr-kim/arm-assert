# -*- coding: utf-8 -*-
"""SharedMemoryIPC Multi-Agent Orchestrator Integration and Loop Tests.

이 테스트는 시맨틱 파서 게이트웨이 및 Agent A/B 간의 피드백 핑퐁,
자가 치유 루프의 안전 임계치 작동 여부를 정밀 입증합니다.
"""

import os
import sys
import unittest
import shutil
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.shm_orchestrator import SharedMemoryMultiAgentOrchestrator

TEMP_ORCHESTRATION_WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_orchestration_workspace")


def _code_patch_output(body: str) -> str:
    return (
        "## 1. 변경 요약\n"
        "Applied fix.\n\n"
        "## 2. 수정 내용\n"
        f"{body}\n"
    )


class TestSharedMemoryMultiAgentOrchestrator(unittest.TestCase):
    """멀티 에이전트 오케스트레이션 및 피드백 루프 검증 테스트 클래스."""

    def setUp(self):
        """임시 프로젝트 구조 및 코딩 규칙을 사전 세팅합니다."""
        if os.path.exists(TEMP_ORCHESTRATION_WS):
            shutil.rmtree(TEMP_ORCHESTRATION_WS)
        os.makedirs(TEMP_ORCHESTRATION_WS)

        # 1. 코딩 규칙 가상 파일 기입
        with open(os.path.join(TEMP_ORCHESTRATION_WS, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("# Coding Standards\n- No wrapper code allowed.\n")

        # 2. 목 테스트 활성화 환경변수 세팅
        os.environ["MOCK_TESTING"] = "true"

    def tearDown(self):
        """임시 워크스페이스 자원을 소멸시킵니다."""
        if os.path.exists(TEMP_ORCHESTRATION_WS):
            shutil.rmtree(TEMP_ORCHESTRATION_WS)
        if "MOCK_TESTING" in os.environ:
            del os.environ["MOCK_TESTING"]

    @patch("utils.shm_cursor_agent_driver.SharedMemoryCursorAgentDriver.execute_modify_task")
    def test_00_parse_intent_does_not_call_cursor(self, mock_execute):
        """0. parse_intent는 룰 기반만 사용하고 Cursor subprocess를 호출하지 않는다."""
        orch = SharedMemoryMultiAgentOrchestrator(default_workspace=TEMP_ORCHESTRATION_WS)
        orch.parse_intent("하이닉스 주식 분석해줘")
        mock_execute.assert_not_called()

    def test_01_parse_intent_coding_and_research(self):
        """1. 코딩 지시와 리서치 지시를 각각 올바른 의도 DTO 및 바이패스 상태로 유축 분류하는지 검증."""
        orch = SharedMemoryMultiAgentOrchestrator(default_workspace=TEMP_ORCHESTRATION_WS)

        # A. 코딩 지시 테스트
        dto_coding = orch.parse_intent("mystock_web의 routes/api_ai_active.py 45라인 에러 고쳐줘")
        self.assertEqual(dto_coding["intent"], "CODE_MODIFY")
        self.assertEqual(dto_coding["targetFile"], "api_ai_active.py")
        self.assertFalse(dto_coding["bypassRules"])

        # B. 단순 리서치 지시 테스트
        dto_research = orch.parse_intent("삼성전자 어제 거래량 분석해봐")
        self.assertEqual(dto_research["intent"], "FACT_RESEARCH")
        self.assertIsNone(dto_research["targetFile"])
        self.assertTrue(dto_research["bypassRules"])

    @patch("utils.shm_cursor_agent_driver.SharedMemoryCursorAgentDriver.execute_modify_task")
    def test_02_orchestration_feedback_approve_flow(self, mock_execute):
        """2. Agent A의 작업물에 결함이 없을 때 Agent B가 승인(APPROVE)하여 즉각 통과되는 정상 연동 입증."""
        orch = SharedMemoryMultiAgentOrchestrator(default_workspace=TEMP_ORCHESTRATION_WS)
        
        # Agent A의 1차 작업 결과 모의 반환 (결함이 없음)
        mock_execute.return_value = {
            "success": True,
            "text": _code_patch_output(
                "def calc_sum(a, b):\n    return a + b\n# Completed clean patch."
            ),
        }

        result = orch.run_orchestration_loop("dummy.py 에러 수정해줘", max_retries=3)

        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(len(result["feedback_history"]), 0)

    @patch("utils.shm_cursor_agent_driver.SharedMemoryCursorAgentDriver.execute_modify_task")
    def test_03_orchestration_self_healing_retry_flow(self, mock_execute):
        """3. Agent A의 1차 작업본에 결함(TODO 등)이 있어 B가 반려했을 때, 자가 치유(Retry)가 정상 기동하는지 검증."""
        orch = SharedMemoryMultiAgentOrchestrator(default_workspace=TEMP_ORCHESTRATION_WS)
        
        # 1차 실행 때는 결함(TODO)이 남아있고, 2차 실행 때 결함이 제거된 무결 코드를 내놓는 모의(Mocking) 시나리오 설계
        mock_execute.side_effect = [
            {
                "success": True,
                "text": _code_patch_output(
                    "def calc_sum(a, b):\n    # TODO: B가 이 결함을 반려할 예정\n    return a + b"
                ),
            },
            {
                "success": True,
                "text": _code_patch_output(
                    "def calc_sum(a, b):\n    return a + b\n# Patched completely clean."
                ),
            },
        ]

        result = orch.run_orchestration_loop("dummy.py 에러 수정해줘", max_retries=3)

        # 2회 차에 자가 치유에 성공하여 최종 승인 완료됨을 증명
        self.assertTrue(result["success"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(len(result["feedback_history"]), 1)
        self.assertIn("TODO", result["feedback_history"][0]["reject_reason"])


if __name__ == "__main__":
    unittest.main()

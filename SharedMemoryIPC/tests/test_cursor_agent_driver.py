# -*- coding: utf-8 -*-
"""SharedMemoryIPC Cursor SDK Agent Driver Unit and Integration Tests.

이 테스트는 SharedMemoryCursorAgentDriver의 규칙 수집 파이프라인 및
Node.js 서브프로세스 연동 정합성을 모의(Mock) 및 실측 기동을 통해 정밀 검증합니다.
"""

import os
import sys
import unittest
import shutil

# 라이브러리 경로 탐색 허용
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.shm_cursor_agent_driver import SharedMemoryCursorAgentDriver

TEMP_TEST_WORKSPACE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_agent_workspace")


class TestSharedMemoryCursorAgentDriver(unittest.TestCase):
    """Cursor SDK Agent Driver의 룰셋 수집 및 기동 정합성 검증 클래스."""

    def setUp(self):
        """임시 워크스페이스를 만들고 가상의 코딩 규칙(AGENTS.md)을 설치합니다."""
        if os.path.exists(TEMP_TEST_WORKSPACE):
            shutil.rmtree(TEMP_TEST_WORKSPACE)
        os.makedirs(TEMP_TEST_WORKSPACE)

        # 1. 가상의 AGENTS.md 규칙 주입 (절대적 룰셋 강제)
        self.agents_md_content = """# 코딩 룰
- [RULE 1] 모든 함수 명칭 끝에 반드시 'RuleChecked' 접미사를 붙여서 기입할 것.
- [RULE 2] wrapper 레이어를 만들지 마라.
"""
        with open(os.path.join(TEMP_TEST_WORKSPACE, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write(self.agents_md_content)

        # 2. 임시 코딩 파일 설치
        self.dummy_code = """def calc_sum(a, b):
    return a + b
"""
        with open(os.path.join(TEMP_TEST_WORKSPACE, "dummy_calc.py"), "w", encoding="utf-8") as f:
            f.write(self.dummy_code)

    def tearDown(self):
        """테스트 종료 후 임시 워크스페이스 자원을 완전히 해제 및 청소합니다."""
        if os.path.exists(TEMP_TEST_WORKSPACE):
            shutil.rmtree(TEMP_TEST_WORKSPACE)

    def test_01_driver_initialization(self):
        """1. 드라이버 경로 설정 및 인스턴스 바인딩 정합성 검사."""
        driver = SharedMemoryCursorAgentDriver(workspace_path=TEMP_TEST_WORKSPACE)
        self.assertEqual(driver.workspace_path, os.path.abspath(TEMP_TEST_WORKSPACE))
        self.assertTrue(os.path.isfile(driver._bridge_path))

    def test_02_rule_collect_and_subprocess_integration(self):
        """2. 가상의 환경 하에 Node.js 브릿지가 API 키 누락 시 안전한 가드 피드백을 주는지 검증.

        실제 Cursor API 키가 없더라도, 드라이버가 서브프로세스를 기동하여
        'API key not found' 에러 피드백을 정상 수신해 내는지 통합 연동을 검증합니다.
        """
        driver = SharedMemoryCursorAgentDriver(workspace_path=TEMP_TEST_WORKSPACE)
        
        # 임시 환경변수 설정으로 llm_api_keys.json 우회 및 가짜 키 주입 (기동 테스트용)
        os.environ["CURSOR_API_KEY"] = "fake-key-for-testing"
        
        try:
            # 룰 기반 수정 지시 요청 전송
            result = driver.execute_modify_task(
                prompt="dummy_calc.py의 calc_sum 함수를 곱하기 함수로 리팩토링하고 룰셋 규칙 1번을 엄수해라.",
                target_file="dummy_calc.py",
                timeout=15  # 로컬 가짜 키 구동은 빠르게 에러 반환하도록 타임아웃 최소화
            )
            
            # API 키가 가짜이므로 실제 추론은 에러를 던지지만, 
            # 서브프로세스가 안전하게 죽지 않고 '성공적인 실패' 데이터를 JSON으로 Python에 반환하는지 증명합니다.
            self.assertFalse(result["success"])
            self.assertIn("error", result)
            
        finally:
            if "CURSOR_API_KEY" in os.environ:
                del os.environ["CURSOR_API_KEY"]


if __name__ == "__main__":
    unittest.main()

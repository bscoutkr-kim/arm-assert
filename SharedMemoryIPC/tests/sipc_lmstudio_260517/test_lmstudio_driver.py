# -*- coding: utf-8 -*-
"""LM Studio driver and backend routing tests."""

import json
import os
import sys
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_lmstudio_agent_driver import (
    SharedMemoryLmStudioAgentDriver,
    extract_message_text_from_chat_response,
)
from utils.shm_output_templates import INTENT_CODE_MODIFY, INTENT_FACT_RESEARCH
from utils.sipc_worker_backend import BACKEND_CURSOR, BACKEND_LMSTUDIO, create_worker_driver, worker_backend_for_intent


class TestLmStudioExtract(unittest.TestCase):
    def test_extract_message_blocks_only(self):
        data = {
            "output": [
                {"type": "reasoning", "content": "planning..."},
                {"type": "tool_call", "tool": "search_web"},
                {"type": "message", "content": "# 보고서\n\n## 1. 요약\n\n본문"},
            ]
        }
        text = extract_message_text_from_chat_response(data)
        self.assertIn("## 1. 요약", text)
        self.assertNotIn("planning", text)


class TestWorkerBackend(unittest.TestCase):
    def test_code_always_cursor(self):
        os.environ["SIPC_WORKER_BACKEND"] = BACKEND_LMSTUDIO
        try:
            self.assertEqual(worker_backend_for_intent(INTENT_CODE_MODIFY), BACKEND_CURSOR)
        finally:
            del os.environ["SIPC_WORKER_BACKEND"]

    def test_research_lmstudio_when_configured(self):
        os.environ["SIPC_RESEARCH_WORKER_BACKEND"] = BACKEND_LMSTUDIO
        try:
            self.assertEqual(worker_backend_for_intent(INTENT_FACT_RESEARCH), BACKEND_LMSTUDIO)
            driver = create_worker_driver("/tmp/ws", INTENT_FACT_RESEARCH)
            self.assertIsInstance(driver, SharedMemoryLmStudioAgentDriver)
        finally:
            del os.environ["SIPC_RESEARCH_WORKER_BACKEND"]

    def test_default_research_cursor(self):
        self.assertEqual(worker_backend_for_intent(INTENT_FACT_RESEARCH), BACKEND_CURSOR)


class TestLmStudioDriverHttp(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_success_returns_message_text(self, mock_urlopen):
        payload = {
            "output": [
                {"type": "message", "content": "## 1. 요약\n\n테스트 본문입니다."},
            ]
        }
        response = MagicMock()
        response.read.return_value = json.dumps(payload).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = None
        mock_urlopen.return_value = response

        driver = SharedMemoryLmStudioAgentDriver(workspace_path=os.path.dirname(__file__))
        result = driver.execute_modify_task("prompt", timeout=30)

        self.assertTrue(result["success"])
        self.assertIn("## 1. 요약", result["text"])

    @patch("urllib.request.urlopen")
    def test_empty_message_fails(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = json.dumps({"output": []}).encode("utf-8")
        response.__enter__.return_value = response
        response.__exit__.return_value = None
        mock_urlopen.return_value = response

        driver = SharedMemoryLmStudioAgentDriver(workspace_path=os.path.dirname(__file__))
        result = driver.execute_modify_task("prompt", timeout=30)

        self.assertFalse(result["success"])
        self.assertIn("no message", result["error"].lower())


if __name__ == "__main__":
    unittest.main()

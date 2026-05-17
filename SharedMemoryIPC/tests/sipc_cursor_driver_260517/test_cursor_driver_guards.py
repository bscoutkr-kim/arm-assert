# -*- coding: utf-8 -*-
"""Cursor driver empty-text guard and heartbeat callback tests."""

import json
import os
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_cursor_agent_driver import SharedMemoryCursorAgentDriver

TEMP_WS = os.path.join(os.path.dirname(__file__), "temp_cursor_driver_ws")


class TestCursorDriverGuards(unittest.TestCase):
    def setUp(self):
        os.makedirs(TEMP_WS, exist_ok=True)

    def tearDown(self):
        if os.path.exists(TEMP_WS):
            for f in os.listdir(TEMP_WS):
                os.remove(os.path.join(TEMP_WS, f))
            os.rmdir(TEMP_WS)

    @patch("utils.shm_cursor_agent_driver.subprocess.Popen")
    def test_empty_text_returns_failure(self, mock_popen):
        proc = MagicMock()
        proc.communicate.return_value = (
            json.dumps({"success": True, "text": "   ", "status": "finished"}),
            "",
        )
        proc.returncode = 0
        mock_popen.return_value = proc

        driver = SharedMemoryCursorAgentDriver(workspace_path=TEMP_WS)
        result = driver.execute_modify_task("test prompt", timeout=30)

        self.assertFalse(result["success"])
        self.assertIn("empty", result.get("error", "").lower())

    @patch("utils.shm_cursor_agent_driver.subprocess.Popen")
    def test_heartbeat_callback_during_long_wait(self, mock_popen):
        os.environ["SIPC_WORKER_HEARTBEAT_SEC"] = "1"
        progress_calls: list[int] = []

        def slow_communicate(*_args, **_kwargs):
            time.sleep(3.5)
            return (
                json.dumps({"success": True, "text": "ok output", "status": "finished"}),
                "",
            )

        proc = MagicMock()
        proc.communicate.side_effect = slow_communicate
        proc.returncode = 0
        mock_popen.return_value = proc

        try:
            driver = SharedMemoryCursorAgentDriver(workspace_path=TEMP_WS)
            result = driver.execute_modify_task(
                "test",
                timeout=30,
                on_progress=lambda sec: progress_calls.append(sec),
            )
            self.assertTrue(result["success"])
            self.assertGreaterEqual(len(progress_calls), 1)
            self.assertEqual(progress_calls[0], 0)
        finally:
            if "SIPC_WORKER_HEARTBEAT_SEC" in os.environ:
                del os.environ["SIPC_WORKER_HEARTBEAT_SEC"]


if __name__ == "__main__":
    unittest.main()

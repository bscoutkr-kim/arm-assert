# -*- coding: utf-8 -*-
"""Orchestrator publishes Agent A/B events on SHM during mocked worker runs."""

import os
import shutil
import sys
import unittest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_agent_bus import ShmAgentBus
from utils.shm_ipc_driver import SharedMemoryIPCDriver
from utils.shm_orchestrator import SharedMemoryMultiAgentOrchestrator
from utils.shm_protocol import (
    CMD_REVIEW_APPROVE,
    CMD_WORKER_RESULT,
    READER_UI,
    SENDER_AGENT_A,
    SENDER_AGENT_B,
)

SHM_TEST = "sipc_orch_e2e_260517"
TEMP_WS = os.path.join(os.path.dirname(__file__), "temp_orch_e2e_ws")


def _code_patch_output(body: str) -> str:
    return (
        "## 1. 변경 요약\n"
        "Applied fix.\n\n"
        "## 2. 수정 내용\n"
        f"{body}\n"
    )


class TestOrchestratorShmEvents(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEMP_WS):
            shutil.rmtree(TEMP_WS)
        os.makedirs(TEMP_WS)
        with open(os.path.join(TEMP_WS, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("# rules\n")
        os.environ["MOCK_TESTING"] = "true"
        self.creator = SharedMemoryIPCDriver(shm_name=SHM_TEST, create=True)
        self.bus = ShmAgentBus(SHM_TEST, create=False)
        self.reader = SharedMemoryIPCDriver(shm_name=SHM_TEST, create=False)

    def tearDown(self):
        if "MOCK_TESTING" in os.environ:
            del os.environ["MOCK_TESTING"]
        self.bus.close()
        self.reader.close()
        self.creator.destroy()
        if os.path.exists(TEMP_WS):
            shutil.rmtree(TEMP_WS)

    @patch("utils.shm_cursor_agent_driver.SharedMemoryCursorAgentDriver.execute_modify_task")
    def test_orchestration_emits_agent_events(self, mock_execute):
        mock_execute.return_value = {
            "success": True,
            "text": _code_patch_output("def ok():\n    return 1\n# clean"),
        }
        orch = SharedMemoryMultiAgentOrchestrator(default_workspace=TEMP_WS, bus=self.bus)
        result = orch.run_orchestration_loop("dummy.py 수정", max_retries=2)
        self.assertTrue(result["success"])
        self.assertIn("brief", result)

        events = []
        while True:
            msg = self.reader.read_next_message(READER_UI)
            if not msg:
                break
            events.append(msg)

        senders = {e["sender_id"] for e in events}
        commands = {e["command"] for e in events}
        self.assertIn(SENDER_AGENT_A, senders)
        self.assertIn(SENDER_AGENT_B, senders)
        self.assertIn(CMD_WORKER_RESULT, commands)
        self.assertIn(CMD_REVIEW_APPROVE, commands)


if __name__ == "__main__":
    unittest.main()

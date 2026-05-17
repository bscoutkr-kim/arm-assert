# -*- coding: utf-8 -*-
"""SharedMemoryIPC multi-agent bus protocol constants (SSOT)."""

from typing import Final

SHM_DEMO_NAME: Final[str] = "sipc_demo_session"
DEFAULT_SHM_SIZE: Final[int] = 1048576

SENDER_MAIN: Final[str] = "MainAI"
SENDER_AGENT_A: Final[str] = "AgentA"
SENDER_AGENT_B: Final[str] = "AgentB"
READER_UI: Final[str] = "UI_Monitor"

CMD_GREETING: Final[str] = "GREETING"
CMD_ORCH_INTENT: Final[str] = "ORCH_INTENT"
CMD_ORCH_TASK_PLAN: Final[str] = "ORCH_TASK_PLAN"
CMD_ORCH_ACK: Final[str] = "ORCH_ACK"
CMD_WORKER_START: Final[str] = "WORKER_START"
CMD_WORKER_PROGRESS: Final[str] = "WORKER_PROGRESS"
CMD_WORKER_RESULT: Final[str] = "WORKER_RESULT"
CMD_REVIEW_REJECT: Final[str] = "REVIEW_REJECT"
CMD_REVIEW_APPROVE: Final[str] = "REVIEW_APPROVE"
CMD_ORCH_COMPLETE: Final[str] = "ORCH_COMPLETE"
CMD_ORCH_FAILED: Final[str] = "ORCH_FAILED"
CMD_ARTIFACT_SAVED: Final[str] = "ARTIFACT_SAVED"

MAX_BUS_TEXT_BYTES: Final[int] = 3600

MARKER_DATA_UNAVAILABLE: Final[str] = "DATA_UNAVAILABLE"

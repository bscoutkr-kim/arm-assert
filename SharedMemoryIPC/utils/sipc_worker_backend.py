# -*- coding: utf-8 -*-
"""Worker backend selection: Cursor SDK vs LM Studio (+ MCP)."""

import os
from typing import Final, Union

from utils.shm_cursor_agent_driver import SharedMemoryCursorAgentDriver
from utils.shm_lmstudio_agent_driver import SharedMemoryLmStudioAgentDriver
from utils.shm_output_templates import (
    INTENT_CODE_MODIFY,
    INTENT_FACT_RESEARCH,
    INTENT_GENERAL_ANSWER,
)

BACKEND_CURSOR: Final[str] = "cursor"
BACKEND_LMSTUDIO: Final[str] = "lmstudio"

WorkerDriver = Union[SharedMemoryCursorAgentDriver, SharedMemoryLmStudioAgentDriver]


def worker_backend_for_intent(intent: str) -> str:
    """CODE stays on Cursor; research/general can use LM Studio via env."""
    if intent == INTENT_CODE_MODIFY:
        return BACKEND_CURSOR

    global_backend = os.environ.get("SIPC_WORKER_BACKEND", BACKEND_CURSOR).strip().lower()
    if global_backend == BACKEND_LMSTUDIO:
        return BACKEND_LMSTUDIO

    research_backend = os.environ.get("SIPC_RESEARCH_WORKER_BACKEND", "").strip().lower()
    if intent in (INTENT_FACT_RESEARCH, INTENT_GENERAL_ANSWER) and research_backend == BACKEND_LMSTUDIO:
        return BACKEND_LMSTUDIO

    return BACKEND_CURSOR


def create_worker_driver(workspace_path: str, intent: str) -> WorkerDriver:
    if worker_backend_for_intent(intent) == BACKEND_LMSTUDIO:
        return SharedMemoryLmStudioAgentDriver(workspace_path=workspace_path)
    return SharedMemoryCursorAgentDriver(workspace_path=workspace_path)

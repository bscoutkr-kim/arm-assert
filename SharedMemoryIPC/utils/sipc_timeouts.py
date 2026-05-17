# -*- coding: utf-8 -*-
"""SharedMemoryIPC Cursor worker timeout and heartbeat constants (SSOT)."""

import os
from typing import Final

DEFAULT_CURSOR_WORKER_TIMEOUT_SEC: Final[int] = 300
DEFAULT_WORKER_HEARTBEAT_INTERVAL_SEC: Final[int] = 30


def cursor_worker_timeout_sec() -> int:
    """Max wait for Cursor SDK subprocess (main worker tasks)."""
    raw = os.environ.get("SIPC_CURSOR_WORKER_TIMEOUT", "")
    if raw.strip().isdigit():
        return max(30, int(raw.strip()))
    return DEFAULT_CURSOR_WORKER_TIMEOUT_SEC


def worker_heartbeat_interval_sec() -> int:
    """Interval for SHM WORKER_PROGRESS while subprocess is running."""
    raw = os.environ.get("SIPC_WORKER_HEARTBEAT_SEC", "")
    if raw.strip().isdigit():
        return max(5, int(raw.strip()))
    return DEFAULT_WORKER_HEARTBEAT_INTERVAL_SEC

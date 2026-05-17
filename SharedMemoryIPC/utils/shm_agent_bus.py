# -*- coding: utf-8 -*-
"""Thin publish helper for multi-agent SHM chat events."""

import json
import logging
from typing import Any, Dict, Optional

from utils.shm_ipc_driver import SharedMemoryIPCDriver
from utils.shm_protocol import MAX_BUS_TEXT_BYTES

logger = logging.getLogger("SharedMemoryIPC.AgentBus")


class ShmAgentBus:
    """Publishes orchestration events to the shared memory ring buffer."""

    def __init__(self, shm_name: str, create: bool = False, size: int = 1048576):
        self._driver = SharedMemoryIPCDriver(shm_name=shm_name, size=size, create=create)

    @property
    def driver(self) -> SharedMemoryIPCDriver:
        return self._driver

    def publish(
        self,
        sender: str,
        command: str,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> int:
        """Write one UI-visible event. Truncates text to fit the slot payload limit."""
        payload: Dict[str, Any] = {"text": text}
        if meta:
            payload["meta"] = meta

        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if len(encoded) > MAX_BUS_TEXT_BYTES:
            truncated_text = text.encode("utf-8")[: MAX_BUS_TEXT_BYTES - 200].decode(
                "utf-8", errors="ignore"
            )
            payload = {
                "text": truncated_text + "\n…(truncated for SHM slot limit)",
                "meta": {**(meta or {}), "truncated": True},
            }

        msg_id = self._driver.write_message(
            sender_id=sender,
            command=command,
            payload=payload,
        )
        logger.debug("[AgentBus] publish sender=%s cmd=%s msg_id=%s", sender, command, msg_id)
        return msg_id

    def close(self) -> None:
        self._driver.close()

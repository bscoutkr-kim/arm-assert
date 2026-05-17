# -*- coding: utf-8 -*-
"""LM Studio Agent A driver: /api/v1/chat with mcp.json integrations."""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from utils.sipc_lmstudio_config import (
    lmstudio_api_token,
    lmstudio_base_url,
    lmstudio_context_length,
    lmstudio_integrations,
    lmstudio_model_id,
)
from utils.sipc_timeouts import cursor_worker_timeout_sec

logger = logging.getLogger("SharedMemoryIPC.LmStudioDriver")

ProgressCallback = Callable[[int], None]


def extract_message_text_from_chat_response(data: Dict[str, Any]) -> str:
    """Collect final assistant message blocks from LM Studio /api/v1/chat output."""
    parts: List[str] = []
    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            content = item.get("content")
            if isinstance(content, str) and content.strip():
                parts.append(content.strip())
    return "\n\n".join(parts).strip()


class SharedMemoryLmStudioAgentDriver:
    """Calls LM Studio local server with MCP integrations enabled."""

    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    def execute_modify_task(
        self,
        prompt: str,
        target_file: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        del target_file  # LM Studio MCP handles tools; no repo bridge here.

        effective_timeout = timeout if timeout is not None else cursor_worker_timeout_sec()
        model_id = model or lmstudio_model_id()
        integrations = lmstudio_integrations()
        if not integrations:
            return {
                "success": False,
                "error": "SIPC_LMSTUDIO_INTEGRATIONS is empty; configure MCP plugins in LM Studio",
            }

        url = f"{lmstudio_base_url()}/api/v1/chat"
        payload = {
            "model": model_id,
            "input": prompt,
            "integrations": integrations,
            "context_length": lmstudio_context_length(),
            "temperature": 0.2,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        token = lmstudio_api_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        heartbeat_stop = threading.Event()
        start_time = time.time()

        def _heartbeat_loop() -> None:
            while not heartbeat_stop.wait(30):
                if on_progress:
                    on_progress(int(time.time() - start_time))

        heartbeat_thread: Optional[threading.Thread] = None
        if on_progress:
            on_progress(0)
            heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
            heartbeat_thread.start()

        try:
            logger.info(
                "[LmStudio] POST %s model=%s integrations=%s",
                url,
                model_id,
                integrations,
            )
            request = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(request, timeout=effective_timeout) as response:
                raw = response.read().decode("utf-8")
            data = json.loads(raw)
            text = extract_message_text_from_chat_response(data)
            if not text:
                logger.error("[LmStudio] empty message output: %s", raw[:500])
                return {
                    "success": False,
                    "error": "LM Studio returned no message content (check MCP + tool-capable model)",
                    "raw": data,
                }
            logger.info("[LmStudio] 완료 (text=%s chars)", len(text))
            return {
                "success": True,
                "text": text,
                "backend": "lmstudio",
                "model": model_id,
                "integrations": integrations,
            }
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
            logger.error("[LmStudio] HTTP %s: %s", e.code, detail[:500])
            return {"success": False, "error": f"LM Studio HTTP {e.code}: {detail[:300]}"}
        except urllib.error.URLError as e:
            logger.error("[LmStudio] connection failed: %s", e)
            return {
                "success": False,
                "error": (
                    f"Cannot reach LM Studio at {lmstudio_base_url()}: {e}. "
                    "Start the server and enable 'Allow calling servers from mcp.json'."
                ),
            }
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON from LM Studio: {e}"}
        except TimeoutError:
            return {
                "success": False,
                "error": f"LM Studio request timed out after {effective_timeout}s",
            }
        finally:
            heartbeat_stop.set()
            if heartbeat_thread:
                heartbeat_thread.join(timeout=2.0)

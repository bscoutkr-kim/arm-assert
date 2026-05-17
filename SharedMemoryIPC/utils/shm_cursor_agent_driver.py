# -*- coding: utf-8 -*-
"""SharedMemoryIPC Rule-Aware Cursor SDK Agent Python Driver."""

import json
import logging
import os
import subprocess
import threading
import time
from typing import Any, Callable, Dict, Optional

from utils.sipc_timeouts import cursor_worker_timeout_sec, worker_heartbeat_interval_sec

logger = logging.getLogger("SharedMemoryIPC.CursorDriver")

ProgressCallback = Callable[[int], None]


class SharedMemoryCursorAgentDriver:
    """Cursor SDK 에이전트를 Node subprocess로 구동하는 드라이버."""

    def __init__(self, workspace_path: str):
        self.workspace_path = os.path.abspath(workspace_path)
        self._bridge_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "main",
            "node_bridges",
            "shm_cursor_sdk_driver.mjs",
        )

    def execute_modify_task(
        self,
        prompt: str,
        target_file: Optional[str] = None,
        model: str = "composer-2",
        timeout: Optional[int] = None,
        on_progress: Optional[ProgressCallback] = None,
    ) -> Dict[str, Any]:
        """Cursor SDK subprocess를 구동하고 결과 텍스트를 반환합니다."""
        if not os.path.isfile(self._bridge_path):
            return {
                "success": False,
                "error": f"Cursor SDK subprocess bridge not found: {self._bridge_path}",
            }

        effective_timeout = timeout if timeout is not None else cursor_worker_timeout_sec()
        input_payload = {
            "prompt": prompt,
            "model": model,
            "cwd": self.workspace_path,
            "targetFile": target_file,
        }

        process: Optional[subprocess.Popen] = None
        heartbeat_stop = threading.Event()
        start_time = time.time()

        def _heartbeat_loop() -> None:
            interval = worker_heartbeat_interval_sec()
            while True:
                if on_progress:
                    on_progress(int(time.time() - start_time))
                if heartbeat_stop.wait(interval):
                    break

        heartbeat_thread: Optional[threading.Thread] = None
        if on_progress:
            heartbeat_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
            heartbeat_thread.start()

        try:
            logger.info(
                "[CursorAgent] 구동 - cwd=%s target=%s timeout=%ss",
                self.workspace_path,
                target_file,
                effective_timeout,
            )
            process = subprocess.Popen(
                ["node", self._bridge_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )

            stdout, stderr = process.communicate(
                input=json.dumps(input_payload, ensure_ascii=False),
                timeout=effective_timeout,
            )

            if process.returncode != 0:
                err = (stderr or stdout or "Unknown error").strip()
                logger.error("[CursorAgent] 서브프로세스 실패: %s", err)
                return {"success": False, "error": err}

            result = json.loads(stdout)
            if not result.get("success"):
                err = result.get("error") or "Cursor SDK agent execution failed"
                logger.error("[CursorAgent] 에이전트 실패: %s", err)
                return {"success": False, "error": err}

            text = (result.get("text") or "").strip()
            if not text:
                logger.error("[CursorAgent] 빈 텍스트 응답")
                return {
                    "success": False,
                    "error": "Cursor SDK returned empty text",
                    "status": result.get("status"),
                }

            logger.info("[CursorAgent] 완료 (text=%s chars)", len(text))
            return {
                "success": True,
                "text": text,
                "status": result.get("status"),
                "agentId": result.get("agentId"),
            }

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                process.communicate()
            logger.error("[CursorAgent] 타임아웃 (%ss)", effective_timeout)
            return {
                "success": False,
                "error": (
                    f"Cursor SDK subprocess timed out after {effective_timeout} seconds "
                    f"(SIPC_CURSOR_WORKER_TIMEOUT)"
                ),
            }
        except json.JSONDecodeError as e:
            logger.error("[CursorAgent] stdout JSON 파싱 실패: %s", e)
            return {"success": False, "error": f"Invalid JSON from Cursor bridge: {e}"}
        except Exception as e:
            logger.error("[CursorAgent] 예기치 못한 에러: %s", e)
            return {"success": False, "error": str(e)}
        finally:
            heartbeat_stop.set()
            if heartbeat_thread:
                heartbeat_thread.join(timeout=2.0)

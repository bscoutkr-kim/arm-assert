# -*- coding: utf-8 -*-
"""SharedMemoryIPC Webview Real-time Multi-Agent Orchestration Messenger.

3각 에이전트(Main AI, Agent A, Agent B) 챗은 공유 메모리 버스(SSOT)를 통해 UI에 표시됩니다.
"""

import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime
from typing import Optional

import webview

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.shm_agent_bus import ShmAgentBus
from utils.shm_ipc_driver import SharedMemoryIPCDriver
from utils.shm_output_templates import output_filename_from_brief, should_persist_artifact
from utils.shm_orchestrator import SharedMemoryMultiAgentOrchestrator
from utils.shm_protocol import (
    CMD_ARTIFACT_SAVED,
    CMD_GREETING,
    CMD_ORCH_ACK,
    CMD_ORCH_FAILED,
    DEFAULT_SHM_SIZE,
    READER_UI,
    SENDER_AGENT_A,
    SENDER_AGENT_B,
    SENDER_MAIN,
    SHM_DEMO_NAME,
)

logger = logging.getLogger("SharedMemoryIPC.WebviewOrchestrator")
logging.basicConfig(level=logging.INFO)

DEFAULT_WORKSPACE = os.environ.get("MYSTOCK_WORKSPACE", r"c:\Work\mystock_web")

stop_event = threading.Event()
window_ready = threading.Event()
window = None

driver_master_ref = None
orchestrator: Optional[SharedMemoryMultiAgentOrchestrator] = None
agent_bus: Optional[ShmAgentBus] = None

shm_poller_stop = threading.Event()
shm_poller_thread: Optional[threading.Thread] = None
_poller_lock = threading.Lock()


def _sender_to_js(sender: str) -> str:
    if sender == SENDER_MAIN:
        return "Main_AI"
    if sender == SENDER_AGENT_A:
        return "Agent_A"
    if sender == SENDER_AGENT_B:
        return "Agent_B"
    return sender


def _shm_ui_poller_loop(api_ref: "WebViewApi") -> None:
    """Read SHM chat events and render via pywebview (SSOT for agent bubbles)."""
    logger.info("[SHMPoller] UI 리스너 스레드 가동.")
    try:
        listener = SharedMemoryIPCDriver(
            shm_name=SHM_DEMO_NAME, size=DEFAULT_SHM_SIZE, create=False
        )
    except Exception as e:
        logger.error("[SHMPoller] SHM 바인딩 실패: %s", e)
        return

    while not shm_poller_stop.is_set():
        try:
            msg = listener.read_next_message(READER_UI)
            if not msg:
                time.sleep(0.08)
                continue

            sender = msg.get("sender_id", "Unknown")
            text = msg.get("payload", {}).get("text", "")
            if not text or not window:
                continue

            js_sender = _sender_to_js(sender)
            if "REJECT" in text or "반려" in text:
                window.evaluate_js(
                    "addSystemMessage("
                    + json.dumps("[Reviewer] 결함 적발 — 반려 피드백 수신")
                    + ");"
                )

            window.evaluate_js(
                f"addMessage({json.dumps(js_sender)}, {json.dumps(text)});"
            )
            api_ref.log_message(js_sender, text)
        except Exception as e:
            logger.debug("[SHMPoller] 폴링 예외: %s", e)
            time.sleep(0.08)

    try:
        listener.close()
    except Exception:
        pass
    logger.info("[SHMPoller] UI 리스너 종료.")


def ensure_shm_ui_poller(api_ref: "WebViewApi") -> None:
    """Start the global SHM→UI poller once per session."""
    global shm_poller_thread
    with _poller_lock:
        if shm_poller_thread and shm_poller_thread.is_alive():
            return
        shm_poller_stop.clear()
        shm_poller_thread = threading.Thread(
            target=_shm_ui_poller_loop, args=(api_ref,), daemon=True
        )
        shm_poller_thread.start()


class WebViewApi:
    """Javascript 브릿지에 노출할 파이썬 실시간 연동 API."""

    def __init__(self):
        self.driver = None
        self.chat_history_logs = []
        os.makedirs("log", exist_ok=True)
        os.makedirs("output", exist_ok=True)

    def set_driver(self, driver: SharedMemoryIPCDriver):
        self.driver = driver

    def resolve_api_key(self) -> Optional[str]:
        if os.environ.get("CURSOR_API_KEY"):
            return os.environ.get("CURSOR_API_KEY")

        config_root = os.environ.get("MYSTOCK_CONFIG_ROOT") or os.path.join(
            os.path.expanduser("~"), "auto-trading-test-config"
        )
        keys_path = os.path.join(config_root, "APIKEY", "llm_api_keys.json")
        if os.path.isfile(keys_path):
            try:
                with open(keys_path, "r", encoding="utf-8-sig") as f:
                    keys = json.load(f)
                    api_key = keys.get("cursor", {}).get("apiKey")
                    if api_key:
                        logger.info(
                            "[APIKeyResolver] 홈폴더 설정(%s)에서 Cursor API Key 획득.",
                            keys_path,
                        )
                        return api_key
            except Exception as e:
                logger.warning("[APIKeyResolver] 설정 파싱 실패 (%s): %s", keys_path, e)
        return None

    def log_message(self, sender: str, text: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] [{sender}] {text}"
        self.chat_history_logs.append(log_entry)
        logger.info(log_entry)

    def save_chat_logs(self):
        if not self.chat_history_logs:
            return
        filename = datetime.now().strftime("log/%Y%m%d_%H%M%S.log")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(self.chat_history_logs))
            if window:
                window.evaluate_js(
                    f"addSystemMessage('💾 대화 내역 저장: {filename}');"
                )
        except Exception as e:
            logger.error("대화 로그 저장 실패: %s", e)

    def send_user_message(self, message_text: str):
        if not message_text.strip():
            return

        if window:
            window.evaluate_js(f"addMessage('User', {json.dumps(message_text)});")
        self.log_message("User", message_text)

        if not self.driver or not self.driver.shm:
            if window:
                window.evaluate_js(
                    "addSystemMessage('오류: 공유 메모리 세션이 닫혀 있습니다.');"
                )
            return

        threading.Thread(
            target=self._run_orchestrator_background,
            args=(message_text,),
            daemon=True,
        ).start()

    def _run_orchestrator_background(self, message_text: str):
        global orchestrator, agent_bus

        ensure_shm_ui_poller(self)

        if not agent_bus:
            agent_bus = ShmAgentBus(SHM_DEMO_NAME, create=False)
        if not orchestrator:
            orchestrator = SharedMemoryMultiAgentOrchestrator(
                default_workspace=DEFAULT_WORKSPACE,
                bus=agent_bus,
            )

        cursor_key = self.resolve_api_key()
        if cursor_key:
            os.environ["CURSOR_API_KEY"] = cursor_key
        else:
            config_root = os.environ.get("MYSTOCK_CONFIG_ROOT") or os.path.join(
                os.path.expanduser("~"), "auto-trading-test-config"
            )
            keys_path = os.path.join(config_root, "APIKEY", "llm_api_keys.json")
            err_msg = (
                "❌ [구동 실패 - API Key 누락]\n"
                "Cursor SDK 가동이 불가능합니다.\n"
                f"- CURSOR_API_KEY 환경 변수\n- 홈 설정: {keys_path}\n"
                "가짜(Mock) 연출 없이 기동을 중단합니다."
            )
            agent_bus.publish(SENDER_MAIN, CMD_ORCH_FAILED, err_msg)
            return

        agent_bus.publish(
            SENDER_MAIN,
            CMD_ORCH_ACK,
            "지시를 접수했습니다. 오케스트레이션 루프를 기동합니다.",
        )

        try:
            result = orchestrator.run_orchestration_loop(message_text, max_retries=3)

            if not result.get("success"):
                return

            brief = result.get("brief") or {}
            if not should_persist_artifact(brief):
                self.save_chat_logs()
                return

            final_output = result.get("final_output", "")
            date_suffix = datetime.now().strftime("%Y%m%d")
            output_file = output_filename_from_brief(brief, date_suffix)

            output_path = os.path.join("output", output_file)
            with open(output_path, "w", encoding="utf-8") as cf:
                cf.write(final_output)

            abs_path = os.path.abspath(output_path)
            agent_bus.publish(
                SENDER_MAIN,
                CMD_ARTIFACT_SAVED,
                (
                    f"📁 산출물 저장 완료\n"
                    f"- 경로: {abs_path}\n"
                    f"- 시도 횟수: {result.get('attempts', 1)}\n"
                    f"(내용은 Cursor SDK 응답이며, 시세 API 미연동 시 DATA_UNAVAILABLE 규칙을 따릅니다.)"
                ),
                meta={"output_path": abs_path, "attempts": result.get("attempts")},
            )
            self.save_chat_logs()

        except Exception as e:
            logger.exception("[Orchestrator] 런타임 예외")
            if agent_bus:
                agent_bus.publish(
                    SENDER_MAIN,
                    CMD_ORCH_FAILED,
                    f"❌ [런타임 Exception] {e}",
                )


def start_welcome_chat_sequence(stop_evt: threading.Event):
    """Publish Main / Agent A / Agent B welcome messages on the SHM bus."""
    global driver_master_ref, agent_bus

    logger.info("[WelcomeChat] SHM 웰컴 시퀀스 기동.")

    try:
        driver_master = SharedMemoryIPCDriver(
            shm_name=SHM_DEMO_NAME, size=DEFAULT_SHM_SIZE, create=True
        )
        driver_master_ref = driver_master
        api.set_driver(driver_master)
        agent_bus = ShmAgentBus(SHM_DEMO_NAME, create=False)
    except Exception as e:
        logger.error("[WelcomeChat] 공유 메모리 개설 실패: %s", e)
        return

    window_ready.wait(timeout=10.0)
    if stop_evt.is_set():
        return

    ensure_shm_ui_poller(api)
    time.sleep(0.2)

    greetings = [
        (
            SENDER_MAIN,
            "🤖 시스템 버스(sipc_demo_session)에 Main AI · Worker · Reviewer가 바인딩되었습니다.\n"
            "지시 접수부터 산출물 저장·로그 보존까지 SHM 버스로 연동됩니다.",
        ),
        (
            SENDER_AGENT_A,
            "Agent A (Worker) 대기 중입니다. Cursor SDK 코딩·리서치 작업을 수행합니다.",
        ),
        (
            SENDER_AGENT_B,
            "Agent B (Reviewer) 대기 중입니다. Ruff·리서치 정직성 규칙으로 검증합니다.",
        ),
    ]

    for sender, text in greetings:
        if stop_evt.is_set():
            break
        agent_bus.publish(sender, CMD_GREETING, text)
        time.sleep(0.35)


api = WebViewApi()


def on_webview_closed():
    logger.info("[WebView] 창 종료 — SHM 리소스 정리.")
    stop_event.set()
    shm_poller_stop.set()
    if driver_master_ref:
        try:
            driver_master_ref.destroy()
        except Exception as e:
            logger.warning("자원 파괴 실패: %s", e)
    if agent_bus:
        try:
            agent_bus.close()
        except Exception:
            pass


def on_webview_loaded():
    logger.info("[WebView] DOM 로드 완료.")
    window_ready.set()


if __name__ == "__main__":
    ui_html_path = os.path.join(os.path.dirname(__file__), "ui", "index.html")
    try:
        with open(ui_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except Exception as e:
        logger.error("[Loader] UI 로드 실패: %s", e)
        sys.exit(1)

    welcome_thread = threading.Thread(
        target=start_welcome_chat_sequence, args=(stop_event,), daemon=True
    )
    welcome_thread.daemon = True
    welcome_thread.start()

    window = webview.create_window(
        title="SIPC Multi-Agent Real-time Orchestrator",
        html=html_content,
        js_api=api,
        width=950,
        height=780,
        resizable=True,
    )

    window.events.closed += on_webview_closed

    gui_backend = None
    if sys.platform == "win32":
        if "--mshtml" in sys.argv:
            gui_backend = "mshtml"
        elif "--edge" not in sys.argv:
            gui_backend = "edgehtml"

    webview.start(on_webview_loaded, gui=gui_backend, debug=False)

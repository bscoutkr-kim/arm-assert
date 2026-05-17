# -*- coding: utf-8 -*-
"""SharedMemoryIPC Multi-Agent Orchestrator & Semantic Parser Gateway."""

import logging
import os
import re
from typing import Any, Dict, Optional

from utils.shm_agent_bus import ShmAgentBus
from utils.shm_output_templates import (
    INTENT_CLARIFY,
    INTENT_CODE_MODIFY,
    WORKER_RETRY_DELIVERABLE_RULES,
    build_task_brief,
    classify_intent,
    is_monologue_reject_reason,
    sanitize_worker_output,
)
from utils.shm_protocol import (
    CMD_ORCH_COMPLETE,
    CMD_ORCH_FAILED,
    CMD_ORCH_TASK_PLAN,
    CMD_REVIEW_APPROVE,
    CMD_REVIEW_REJECT,
    CMD_WORKER_PROGRESS,
    CMD_WORKER_RESULT,
    CMD_WORKER_START,
    SENDER_AGENT_A,
    SENDER_AGENT_B,
    SENDER_MAIN,
)
from utils.shm_reviewer import ShmReviewer
from utils.sipc_timeouts import cursor_worker_timeout_sec
from utils.sipc_worker_backend import BACKEND_LMSTUDIO, create_worker_driver, worker_backend_for_intent
from utils.sipc_lmstudio_config import lmstudio_model_id
from utils.sipc_worker_models import worker_model_for_intent

logger = logging.getLogger("SharedMemoryIPC.Orchestrator")


class SharedMemoryMultiAgentOrchestrator:
    """Gateway Parser, Agent A (Worker), Agent B (Reviewer) 간의 자율 협업 루프를 조율하는 오케스트레이터."""

    def __init__(self, default_workspace: str, bus: Optional[ShmAgentBus] = None):
        self.default_workspace = os.path.abspath(default_workspace)
        self.bus = bus
        self.reviewer = ShmReviewer()

    def _publish(
        self,
        sender: str,
        command: str,
        text: str,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.bus:
            self.bus.publish(sender, command, text, meta=meta)

    def parse_intent(self, raw_msg: str) -> Dict[str, Any]:
        """Rule-based intent DTO (no Cursor LLM)."""
        logger.info(f"[Gateway] 🔍 의도 분류: '{raw_msg}'")
        intent = classify_intent(raw_msg)
        file_match = re.search(r"([\w\-_]+\.(?:py|js|mjs|html|css))", raw_msg)
        target_file = file_match.group(1) if file_match else None

        dto: Dict[str, Any] = {
            "intent": intent,
            "workspace": self.default_workspace,
            "targetFile": target_file,
            "instruction": raw_msg.strip(),
            "bypassRules": intent != INTENT_CODE_MODIFY,
        }
        logger.info(f"[Gateway] 🎯 DTO: {dto}")
        return dto

    def _worker_progress(self, elapsed_sec: int) -> None:
        self._publish(
            SENDER_AGENT_A,
            CMD_WORKER_PROGRESS,
            f"⏳ Agent A 작업 중… ({elapsed_sec}초 경과)",
            meta={"elapsed_sec": elapsed_sec},
        )

    def run_orchestration_loop(self, raw_msg: str, max_retries: int = 3) -> Dict[str, Any]:
        dto = self.parse_intent(raw_msg)
        brief = build_task_brief(dto, raw_msg)
        dto["templateId"] = brief["templateId"]

        self._publish(
            SENDER_MAIN,
            CMD_ORCH_TASK_PLAN,
            brief["main_plan_text"],
            meta={
                "intent": brief["intent"],
                "templateId": brief["templateId"],
                "subject": brief["subject"],
            },
        )

        if brief.get("skip_worker"):
            self._publish(
                SENDER_MAIN,
                CMD_ORCH_COMPLETE,
                brief["clarify_response"],
                meta={"intent": INTENT_CLARIFY},
            )
            return {
                "success": True,
                "final_output": brief["clarify_response"],
                "feedback_history": [],
                "attempts": 0,
                "dto": dto,
                "brief": brief,
            }

        workspace = dto.get("workspace") or self.default_workspace
        target_file = dto.get("targetFile")
        backend = worker_backend_for_intent(brief["intent"])
        driver = create_worker_driver(workspace, brief["intent"])
        feedback_history: list = []
        current_worker_prompt = brief["worker_prompt"]

        logger.info(
            "[Orchestrator] 루프 시작 intent=%s template=%s backend=%s",
            brief["intent"],
            brief["templateId"],
            backend,
        )

        if backend == BACKEND_LMSTUDIO:
            worker_model = lmstudio_model_id()
        else:
            worker_model = worker_model_for_intent(brief["intent"])
        logger.info(
            "[Orchestrator] Worker backend=%s model=%s intent=%s",
            backend,
            worker_model,
            brief["intent"],
        )

        for attempt in range(1, max_retries + 1):
            logger.info(f"[Orchestrator] 🔄 Attempt {attempt}/{max_retries}")

            self._publish(
                SENDER_AGENT_A,
                CMD_WORKER_START,
                (
                    f"🚀 [Agent A] {brief['templateId']} 작성 시작 "
                    f"(시도 {attempt}/{max_retries}, backend={backend}, model={worker_model})"
                ),
                meta={
                    "attempt": attempt,
                    "templateId": brief["templateId"],
                    "backend": backend,
                    "model": worker_model,
                },
            )

            worker_res = driver.execute_modify_task(
                prompt=current_worker_prompt,
                target_file=target_file,
                model=worker_model,
                timeout=cursor_worker_timeout_sec(),
                on_progress=self._worker_progress,
            )

            if not worker_res["success"]:
                err = worker_res.get("error", "unknown")
                logger.error(f"[Orchestrator] ❌ Agent A 오류: {err}")
                self._publish(
                    SENDER_MAIN,
                    CMD_ORCH_FAILED,
                    f"❌ [오케스트레이션 실패] Agent A: {err}",
                    meta={"attempt": attempt},
                )
                return {
                    "success": False,
                    "error": f"Agent A failed: {err}",
                    "feedback_history": feedback_history,
                    "dto": dto,
                    "brief": brief,
                }

            a_output = sanitize_worker_output(worker_res.get("text", "") or "", brief)
            preview = a_output if len(a_output) <= 2000 else a_output[:2000] + "\n…"
            self._publish(
                SENDER_AGENT_A,
                CMD_WORKER_RESULT,
                f"📦 [Agent A 결과]\n{preview}",
                meta={"attempt": attempt, "size": len(a_output)},
            )

            is_approved, reject_reason = self.reviewer.review(dto, a_output, workspace, brief)

            if is_approved:
                self._publish(
                    SENDER_AGENT_B,
                    CMD_REVIEW_APPROVE,
                    f"🏆 [APPROVE] {brief['templateId']} — 시도 {attempt} 통과",
                    meta={"attempt": attempt},
                )
                self._publish(
                    SENDER_MAIN,
                    CMD_ORCH_COMPLETE,
                    f"✅ [완료] {brief['templateId']} 승인. 산출물 저장 대기 중.",
                    meta={"attempt": attempt, "success": True},
                )
                return {
                    "success": True,
                    "final_output": a_output,
                    "feedback_history": feedback_history,
                    "attempts": attempt,
                    "dto": dto,
                    "brief": brief,
                }

            logger.warning(f"[Orchestrator] ⚠️ Agent B 반려: {reject_reason}")
            self._publish(
                SENDER_AGENT_B,
                CMD_REVIEW_REJECT,
                f"⚠️ [REJECT] {reject_reason}",
                meta={"attempt": attempt},
            )
            feedback_history.append(
                {"attempt": attempt, "output": a_output, "reject_reason": reject_reason}
            )
            retry_tail = (
                f"[Reviewer 반려 — 시도 {attempt}]\n{reject_reason}\n"
                "위 Task Brief·양식·최소 기준을 모두 충족하는 수정본만 다시 제출하라."
            )
            if is_monologue_reject_reason(reject_reason):
                retry_tail += WORKER_RETRY_DELIVERABLE_RULES
            current_worker_prompt = f"{brief['worker_prompt']}\n\n{retry_tail}"

        err = f"Failed to pass Agent B's review after {max_retries} attempts."
        self._publish(SENDER_MAIN, CMD_ORCH_FAILED, f"❌ [오케스트레이션 실패] {err}")
        return {
            "success": False,
            "error": err,
            "feedback_history": feedback_history,
            "dto": dto,
            "brief": brief,
        }

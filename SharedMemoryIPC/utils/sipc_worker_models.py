# -*- coding: utf-8 -*-
"""Cursor SDK worker model selection by task intent (SSOT)."""

import os
from typing import Final

from utils.shm_output_templates import (
    INTENT_CODE_MODIFY,
    INTENT_FACT_RESEARCH,
    INTENT_GENERAL_ANSWER,
)

# FACT/GENERAL: templated markdown + web search — lighter model is usually enough.
DEFAULT_RESEARCH_WORKER_MODEL: Final[str] = "gpt-5-mini"
# CODE: tool use, repo edits — keep the coding-oriented default.
DEFAULT_CODE_WORKER_MODEL: Final[str] = "composer-2"


def worker_model_for_intent(intent: str) -> str:
    """Resolve Cursor SDK model id from intent and optional env overrides."""
    if intent in (INTENT_FACT_RESEARCH, INTENT_GENERAL_ANSWER):
        override = os.environ.get("SIPC_RESEARCH_WORKER_MODEL", "").strip()
        return override or DEFAULT_RESEARCH_WORKER_MODEL
    if intent == INTENT_CODE_MODIFY:
        override = os.environ.get("SIPC_CODE_WORKER_MODEL", "").strip()
        return override or DEFAULT_CODE_WORKER_MODEL
    override = os.environ.get("SIPC_RESEARCH_WORKER_MODEL", "").strip()
    return override or DEFAULT_RESEARCH_WORKER_MODEL

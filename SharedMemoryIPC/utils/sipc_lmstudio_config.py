# -*- coding: utf-8 -*-
"""LM Studio worker endpoint and MCP integration settings (SSOT)."""

import os
from typing import Final, List

DEFAULT_LMSTUDIO_BASE_URL: Final[str] = "http://127.0.0.1:1234"
DEFAULT_LMSTUDIO_MODEL: Final[str] = "google/gemma-4-e2b:2"
DEFAULT_LMSTUDIO_CONTEXT_LENGTH: Final[int] = 16384
DEFAULT_LMSTUDIO_INTEGRATIONS: Final[str] = "mcp/web-search-mcp,mcp/alphavantage"


def lmstudio_base_url() -> str:
    raw = os.environ.get("SIPC_LMSTUDIO_BASE_URL", "").strip()
    return (raw or DEFAULT_LMSTUDIO_BASE_URL).rstrip("/")


def lmstudio_model_id() -> str:
    raw = os.environ.get("SIPC_LMSTUDIO_MODEL", "").strip()
    return raw or DEFAULT_LMSTUDIO_MODEL


def lmstudio_api_token() -> str:
    return (
        os.environ.get("SIPC_LMSTUDIO_API_TOKEN", "").strip()
        or os.environ.get("LM_API_TOKEN", "").strip()
    )


def lmstudio_context_length() -> int:
    raw = os.environ.get("SIPC_LMSTUDIO_CONTEXT_LENGTH", "").strip()
    if raw.isdigit():
        return max(4096, int(raw))
    return DEFAULT_LMSTUDIO_CONTEXT_LENGTH


def lmstudio_integrations() -> List[str]:
    """MCP plugin ids from mcp.json (e.g. mcp/web-search-mcp)."""
    raw = os.environ.get("SIPC_LMSTUDIO_INTEGRATIONS", "").strip()
    source = raw or DEFAULT_LMSTUDIO_INTEGRATIONS
    return [part.strip() for part in source.split(",") if part.strip()]

"""Human-readable markdown transcripts for multi-agent TradingAgents debates."""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from tradingagents.dataflows.utils import safe_ticker_component

DEFAULT_MAX_TRANSCRIPTS_PER_TICKER = 30
DEBATE_PHASE_FIRST = "1st"
DEBATE_PHASE_SECOND = "2nd"
_VALID_DEBATE_PHASES = frozenset({DEBATE_PHASE_FIRST, DEBATE_PHASE_SECOND})

logger = logging.getLogger(__name__)


def normalize_debate_phase(phase: str) -> str:
    """Normalize debate phase for transcript filenames (ASCII: 1st | 2nd)."""
    normalized = (phase or DEBATE_PHASE_FIRST).strip().lower()
    if normalized in _VALID_DEBATE_PHASES:
        return normalized
    return DEBATE_PHASE_FIRST


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value).strip()


def _md_section(title: str, body: Any) -> str:
    text = _normalize_text(body)
    if not text:
        return f"## {title}\n\n_(empty)_\n"
    return f"## {title}\n\n{text}\n"


def build_debate_transcript_markdown(
    ticker: str,
    trade_date: str,
    final_state: Dict[str, Any],
    *,
    saved_at: Optional[datetime] = None,
) -> str:
    """Render final LangGraph state as a human-readable markdown document."""
    saved_at = saved_at or datetime.now()
    inv = final_state.get("investment_debate_state") or {}
    risk = final_state.get("risk_debate_state") or {}

    parts = [
        "# TradingAgents Debate Transcript",
        "",
        f"- **Ticker**: `{ticker}`",
        f"- **Trade date**: {trade_date}",
        f"- **Saved at**: {saved_at.strftime('%Y-%m-%d %H:%M:%S.%f')}",
        "",
        "---",
        "",
        _md_section("Market Analyst Report", final_state.get("market_report")),
        _md_section("Sentiment Analyst Report", final_state.get("sentiment_report")),
        _md_section("News Analyst Report", final_state.get("news_report")),
        _md_section("Fundamentals Analyst Report", final_state.get("fundamentals_report")),
        _md_section("Investment Debate (Bull vs Bear — full thread)", inv.get("history")),
        _md_section("Bull Analyst (cumulative)", inv.get("bull_history")),
        _md_section("Bear Analyst (cumulative)", inv.get("bear_history")),
        _md_section("Research Manager Decision", inv.get("judge_decision")),
        _md_section("Investment Plan", final_state.get("investment_plan")),
        _md_section("Trader Plan", final_state.get("trader_investment_plan")),
        _md_section("Risk Debate (full thread)", risk.get("history")),
        _md_section("Aggressive Risk Analyst", risk.get("aggressive_history")),
        _md_section("Conservative Risk Analyst", risk.get("conservative_history")),
        _md_section("Neutral Risk Analyst", risk.get("neutral_history")),
        _md_section("Risk Judge Decision", risk.get("judge_decision")),
        _md_section(
            "Portfolio Manager — Final Trade Decision",
            final_state.get("final_trade_decision"),
        ),
        "",
    ]
    return "\n".join(parts)


def _prune_old_files(directory: Path, pattern: str, max_files: int) -> None:
    if max_files <= 0 or not directory.is_dir():
        return
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime)
    if len(files) <= max_files:
        return
    for path in files[:-max_files]:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass


def write_debate_transcript_md(
    root_dir: str | Path,
    ticker: str,
    trade_date: str,
    final_state: Dict[str, Any],
    *,
    debate_phase: str = "1st",
    max_files_per_ticker: int = DEFAULT_MAX_TRANSCRIPTS_PER_TICKER,
) -> Path:
    """Write a timestamped markdown transcript under ``root_dir/{safe_ticker}/``."""
    phase = normalize_debate_phase(debate_phase)
    safe_ticker = safe_ticker_component(ticker)
    now = datetime.now()
    directory = Path(root_dir) / safe_ticker
    directory.mkdir(parents=True, exist_ok=True)

    out_path = directory / f"{now.strftime('%y%m%d_%H%M%S_%f')}_debate_{phase}.md"
    content = build_debate_transcript_markdown(
        ticker, trade_date, final_state, saved_at=now
    )

    tmp_fd, tmp_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(tmp_name, out_path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise

    _prune_old_files(directory, "*.md", max_files_per_ticker)
    return out_path


def load_latest_debate_transcript_excerpt(
    root_dir: str | Path,
    ticker: str,
    phase: str = "1st",
    max_chars: int = 4000,
) -> str:
    """Load the latest transcript for a ticker/phase and extract RM and PM decision sections.
    
    If no new pattern matching *_debate_{phase}.md is found and phase is '1st',
    we look for legacy transcripts (*.md files without '_debate_' in their names)
    as a backward compatibility fallback.
    """
    safe_ticker = safe_ticker_component(ticker)
    directory = Path(root_dir) / safe_ticker
    if not directory.is_dir():
        return ""

    pattern = f"*_debate_{phase}.md"
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    selected_file = None
    is_legacy = False

    if files:
        selected_file = files[0]
    elif phase == "1st":
        # Look for old legacy files without debate phases in their names
        legacy_files = sorted(
            [p for p in directory.glob("*.md") if "_debate_" not in p.name],
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        if legacy_files:
            selected_file = legacy_files[0]
            is_legacy = True

    if not selected_file:
        return ""

    try:
        content = selected_file.read_text(encoding="utf-8")
        if is_legacy:
            logger.info(f"[Debate 2nd] loaded legacy transcript: {selected_file.name}")
        else:
            logger.info(f"[Debate 2nd] loaded 1st transcript: {selected_file.name}")

        lines = content.splitlines()
        pm_section = []
        rm_section = []
        in_pm = False
        in_rm = False

        for line in lines:
            if line.startswith("## Research Manager Decision"):
                in_rm = True
                in_pm = False
                rm_section.append(line)
                continue
            elif line.startswith("## Portfolio Manager"):
                in_pm = True
                in_rm = False
                pm_section.append(line)
                continue
            elif line.startswith("## ") and (in_rm or in_pm):
                in_rm = False
                in_pm = False

            if in_rm:
                rm_section.append(line)
            elif in_pm:
                pm_section.append(line)

        excerpt_parts = []
        if rm_section:
            excerpt_parts.append("\n".join(rm_section))
        if pm_section:
            excerpt_parts.append("\n".join(pm_section))

        excerpt = "\n\n".join(excerpt_parts).strip()
        if not excerpt:
            # Fallback to full file if RM/PM sections not found
            excerpt = content.strip()

        if len(excerpt) > max_chars:
            excerpt = excerpt[:max_chars] + "\n... (truncated)"

        return excerpt
    except Exception as e:
        logger.warning(f"Failed to load debate transcript excerpt from {selected_file}: {e}")
        return ""

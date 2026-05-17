---
name: graphify
description: >
  Graphify knowledge graph: read GRAPH_REPORT before planning or editing app source;
  run graphify update after code changes. Use for architecture navigation, implementation
  plans, bugfixes, refactors, and post-change graph maintenance.
---

# Graphify Workflow

**Read-before-plan/write, update-after-change:**
→ `.agent/skills/graphify/reference.md`

## Purpose

1. **Navigation (Read-First)** — Before **planning** or **first edit** to app source, use `graphify-out/GRAPH_REPORT.md` (God Nodes, relevant Communities) to pick entry files and hubs.
2. **Maintenance (Update-Post)** — After app source changes, run AST-only `graphify update .` (no API cost).

## When to Run

- **Before** `/implementation-plan` or **before** first change to `static/`·`routes/`·`templates/`·`mystock_web.py`.
- **After** modifying app source in the session.
- When architecture questions need hub/community context (not only `rg`).

## Rules

1. **Read-First** — `graphify-out/GRAPH_REPORT.md` (date + God Nodes + 1–3 Communities). 리포트 날짜가 **현재 날짜와 다르거나(stale)**, 또는 HEAD와 어긋나면 **`graphify update .`** 후 재확인. Not optional for normal app-source work; narrow exemptions in `reference.md` §3.
2. **Update-Post** — Repository root, **PATH `graphify` CLI** (`npx graphify` forbidden). Windows: `$env:PYTHONUTF8='1'` recommended.
3. **Wiki-Nav** — If `graphify-out/wiki/index.md` exists, use it per reference.
4. **Evidence** — Plan: `Graphify Context`; write: `Graphify Evidence` (hub/Community name required unless exempt).

## Related

- **`implementation-plan`**, **`code-writing-guard`**: Mandatory read + evidence.
- **`manage-skills`**: Orchestration chain §0.3.

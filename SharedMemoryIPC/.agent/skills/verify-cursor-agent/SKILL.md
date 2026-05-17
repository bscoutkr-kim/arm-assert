---
name: verify-cursor-agent
description: >
  Rule-Aware Cursor SDK Agent Driver 및 Main AI, Agent A(Worker), Agent B(Reviewer) 간의
  3자 비동기 자가치유 피드백 루프와 실시간 모니터링 챗 UI 연동 정합성을 검증합니다.
argument-hint: "[Optional: run-test|lint-check]"
---

# verify-cursor-agent — Rule-Aware Cursor SDK & 3-Agent Orchestrator 검증 스킬

## Purpose

이 스킬은 `SharedMemoryIPC` 내에 신설되는 `utils/shm_cursor_agent_driver.py` 및 `utils/shm_orchestrator.py`, 그리고 데스크톱 모니터링 UI인 `main/app_webview.py` 모듈이 **Main AI (Orchestrator Manager)**, **Agent A (Worker)**, **Agent B (Reviewer)** 의 3각 편대 비동기 피드백 챗 버블 흐름을 유기적으로 통제 및 실시간 시각화 연동하는지 검증하고 감사하는 단일 진실 공급원(SSOT)입니다.

## When To Use

- `shm_cursor_sdk_driver.mjs` (Node.js 에이전트 브릿지) 소스 수정 시
- `shm_cursor_agent_driver.py` 및 `shm_orchestrator.py` 오케스트레이터 코어 수정 시
- `main/app_webview.py` 의 3자 에이전트 실시간 비동기 챗 렌더링 로직 수정 시
- `tests/test_shm_orchestrator.py` 및 `tests/test_cursor_agent_driver.py` 유닛 테스트를 기동하여 검증할 때

## Related Files

- `main/node_bridges/shm_cursor_sdk_driver.mjs`
- `utils/shm_cursor_agent_driver.py`
- `utils/shm_orchestrator.py`
- `main/app_webview.py`
- `main/ui/index.html`
- `tests/test_shm_orchestrator.py`
- `docs/architecture/rule_aware_agent_architecture_260517.md`

## Full Reference

→ `.agent/skills/verify-cursor-agent/reference.md`

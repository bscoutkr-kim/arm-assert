# Rule-Aware AI Agent Driver & Multi-Agent 3-Agent Team Orchestration Architecture Note

- **작성일**: 2026-05-17
- **분류**: 장기 구조 · 연동 · 도메인 개요 (Architecture)

---

## 1. 개요 (Overview)

본 문서는 `SharedMemoryIPC` 분산 에이전트 시스템에서 외부 대상 프로젝트(예: `mystock_web`)의 코딩 변경 또는 주식/코인 투자 리서치를 자율 수행하는 코딩 에이전트 드라이버와 **Main AI & Multi-Agent 3각 편대 오케스트레이터(3-Agent Team Orchestrator)** 아키텍처를 정의합니다.

특히, 사용자와 직접 의사소통을 전담하는 **Main AI (Orchestrator Manager)** 와, 실제 Cursor SDK 자율 코딩 작업을 수행하는 **Agent A (Worker)**, 그리고 결과물의 팩트 체크와 린트 정합성을 철저히 감사하는 **Agent B (Reviewer)** 간의 유기적 피드백 시각화 챗 루프를 실시간 데모 환경 상에 표출하는 것에 그 목적이 있습니다.

---

## 2. 경계 및 인터페이스 (Boundary & Interface)

### 2.1 현재 구현 상태 (2026-05-17)

| 항목 | 구현 |
|------|------|
| 챗 UI SSOT | `sipc_demo_session` SHM → `UI_Monitor` 폴러 → `index.html` |
| Agent A | 동일 프로세스, `SharedMemoryCursorAgentDriver` → Node `@cursor/sdk` |
| Agent B | `utils/shm_reviewer.py` (TODO/FIXME, ruff, 리서치 정직성) |
| 웰컴·오케스트 이벤트 | `utils/shm_agent_bus.py` → `write_message` |
| Worker 백엔드 | `SIPC_WORKER_BACKEND` / `SIPC_RESEARCH_WORKER_BACKEND`: **`lmstudio`** (FACT/GENERAL) 또는 **`cursor`** (기본·CODE) |
| Worker 모델 | Cursor: `gpt-5-mini` / `composer-2` · LM Studio: `SIPC_LMSTUDIO_MODEL` + `SIPC_LMSTUDIO_INTEGRATIONS` (MCP) |
| Worker 타임아웃 | 기본 **300초** (`SIPC_CURSOR_WORKER_TIMEOUT`) |
| 작업 중 표시 | **30초**마다 `WORKER_PROGRESS` (`SIPC_WORKER_HEARTBEAT_SEC`) |
| Gateway 의도 파싱 | **룰·키워드** → `FACT_RESEARCH` / `GENERAL_ANSWER` / `CODE_MODIFY` / `CLARIFY` |
| Task Brief | `utils/shm_output_templates.build_task_brief` → SHM `ORCH_TASK_PLAN` |
| 공용 산출 양식 | `FACT_REPORT_v1`, `GENERAL_ANSWER_v1`, `CODE_PATCH_v1` |
| Agent A 별도 OS 프로세스 | **미구현** (추후 별도 계획) |

시스템 제어부는 네 가지 물리적 경계(Boundary)로 격리됩니다:

1. **사용자/통신 인터페이스 레이어 (`main/app_webview.py` & `main/ui/index.html`)**:
   - 사용자 입력만 로컬 렌더링. **Main / Agent A / Agent B 챗은 SHM 버스 경유만** 표시합니다.
2. **시맨틱 파서 & 오케스트레이터 레이어 (`utils/shm_orchestrator.py`)**:
   - DTO 파싱, Worker 루프, Reviewer 호출, 단계별 SHM 이벤트 게시.
3. **에이전트 제어 드라이버 레이어 (`utils/shm_cursor_agent_driver.py`)**:
   - 파이썬 백엔드에서 서브프로세스를 동적으로 스폰하고 제어하는 래퍼 컨트롤러입니다.
4. **자율 코딩 수행 브릿지 레이어 (`main/node_bridges/shm_cursor_sdk_driver.mjs`)**:
   - Node.js 기반 `@cursor/sdk`를 활용하여 타겟 파일의 맥락을 분석하고, 룰 가드를 얹어 코드를 기입하거나 외부 리서치 도구를 자율 구동하여 정보를 채웁니다.

---

## 3. 3자 피드백 데이터 흐름 (3-Agent Team Feedback Loop)

```
 👤 사용자 (User Input)
       │
       ▼
 🤖 [Main AI (Orchestrator)]  ──(의도 DTO 파싱 및 지시이관)──>  🚀 [Agent A (Worker)]
       ▲                                                           │
       │ (최종 승인 보고)                                           │ (1차 작업본 송출)
       │                                                           ▼
 🧐 [Agent B (Reviewer)]   <──(반려/승인 피드백 Chaining)───  [결함 정밀 심사]
```

1. **Main AI (Orchestrator)**: 사용자의 질문 접수 ➔ Gateway DTO 의도 분석 및 발표 ➔ Agent A에게 지시 이관 챗 송출.
2. **Agent A (Worker)**: Cursor SDK 기반 1차 작업본(TODO 결함) 챗 버블 송출.
3. **Agent B (Reviewer)**: TODO 결함 적발 ➔ 위반 사유 REJECT 반려 피드백 챗 버블 송출.
4. **Agent A (Worker)**: 자가 치유(Self-Healing) 보정 패치 2차 정제본 챗 버블 재송출.
5. **Agent B (Reviewer)**: 2차 정제본 무결 검증 통과 ➔ 최종 승인(APPROVE) 챗 버블 공표.
6. **Main AI (Orchestrator)**: 최종 무결 패치 수립 성공 종결 리포트 챗 버블 완결 보고.

---

## 4. 관련 코드 경로 (Code Paths)

- **SHM 프로토콜 SSOT**: `utils/shm_protocol.py`
- **SHM 게시 헬퍼**: `utils/shm_agent_bus.py`
- **Reviewer (Agent B)**: `utils/shm_reviewer.py`
- **UI 메인 챗**: `main/app_webview.py` & `main/ui/index.html`
- **오케스트레이션 코어**: `utils/shm_orchestrator.py`
- **IPC 드라이버**: `utils/shm_ipc_driver.py`
- **Node.js 브릿지**: `main/node_bridges/shm_cursor_sdk_driver.mjs`
- **Python Cursor 드라이버**: `utils/shm_cursor_agent_driver.py`
- **유닛·E2E 테스트**: `tests/test_shm_orchestrator.py`, `tests/shm_orchestration_e2e_260517/`
- **Mock 잔재 아카이브**: `docs/archive/mock_sessions_260517/`
- **구현 계획**: `docs/plan/multi_agent_shm_orchestration_fix_260517.md`

# verify-cursor-agent — Reference Guide

Companion to `SKILL.md`. Rule-Aware Cursor SDK Agent Driver 및 **3각 편대 멀티 에이전트 오케스트레이터(Main AI, Worker, Reviewer)**의 구현 명세, 챗 UI 실시간 연동 규격, 검증 체크리스트 및 트러블슈팅을 다룹니다.

---

## 1. Core Architecture Specifications

본 검증 스킬은 `SharedMemoryIPC`에서 자연어 지시를 받아 자율 수정을 수행하고 이를 모니터링하는 다중 에이전트 시스템의 다음 3각 편대 아키텍처 규칙을 보증합니다:

1. **3각 에이전트 편대 (Three-Agent Orchestration)**:
   - **Main AI (Orchestrator)**: 사용자의 지시를 수신하여 Gateway Parser를 기동하고, 의도 DTO 분석 결과를 발표하며 Agent A에게 작업을 지시 및 최종 완결 리포트를 전송합니다.
   - **Agent A (Worker)**: 메인 AI의 지시를 수신해 Cursor SDK 기반 1차 작업본(TODO 결함 함유) 및 반려 시 자가치유를 통해 2차 정제본 코드를 송출합니다.
   - **Agent B (Reviewer)**: A의 결과물을 엄격히 심사해 반려(REJECT) 또는 승인(APPROVE)을 발표합니다.
2. **실시간 Zero-Shot 태스크 분해 계획 발표 (Dynamic Planning)**:
   - 사용자가 임의의 자연어를 주입하면, 메인 AI가 스스로 맥락을 시맨틱 분석하여 **"하위 Actionable 태스크 2단계 이행 계획"**을 스스로 기획해 챗 버블로 선제 공표해야 합니다.
3. **무한 범용성 (GENERAL_TALK) 연동 체인**:
   - 코딩이나 주식 분석 외의 범용 질문 유입 시, 메인 AI가 "의견서 자율 초안 기획(Worker) ➔ 논리 정합성 및 블릿 시각화 가독성 감사(Reviewer)" 태스크로 실시간 분해하여 자율 핑퐁 감사를 전개합니다.
4. **최종 완성 산출물(Artifact) 물리 보존 (`output/` 폴더)**:
   - 최종 승인 시, 메인 AI가 결과물의 물리 속성(코드, 보고서, 일반의견 등)을 식별하여 **`output/` 폴더 하위에 적합한 확장자 및 파일명(`.md`, `.js`, `.py` 등)으로 자동 영구 보존** 관리합니다.
5. **실시간 대화 이력 영구 보존 (`log/` 폴더)**:
   - 웰컴 챗부터 완결 보고에 이르기까지 나눈 전체 대화 데이터를 타임스탬프와 함께 수급하여, 세션 완수 즉시 **`log/YYYYMMDD_HHMMSS.log` 날짜/시간/초 규격 파일로 자동 플러시 저장**해야 합니다.
6. **실시간 비동기 UI 버블 Chaining**:
   - `app_webview.py` 백그라운드 스레드에서 `evaluate_js`를 호출하여 메인 UI 스레드 동결(Freeze) 없이 비동기식으로 실시간 챗 버블을 송출해야 합니다.

---

## 2. Verification Checklist

오케스트레이터와 게이트웨이 파서를 수정하거나 기동할 때, 관리자(`GEMINI.md`)는 아래 체크리스트를 정밀 감사해야 합니다:

- [ ] 세션 기동 즉시 **Main AI ➔ Agent A ➔ Agent B** 순으로 펼쳐지는 3자 릴레이 웰컴 메시지가 UI 화면에 리얼하고 웅장하게 렌더링되는지 확인.
- [ ] 입력창에 자연어 주입 시 **Main AI (Orchestrator)**가 DTO 분석 결과에 따라 **실시간 2단계 하위 태스크 지행 계획**을 선언하는지 확인.
- [ ] 일반 대화 입력 시 **`GENERAL_TALK` 범용 분기**로 스위칭되어 Worker의 문단 초안 송출 및 Reviewer의 블릿 시각화 반려(REJECT)가 맞물려 기동되는지 검증.
- [ ] Worker의 2차 자가치유 보완 의견 송출 및 Reviewer의 최종 APPROVE, Main AI의 완결 브리핑 버블이 순차적으로 정상 송출되는지 확인.
- [ ] 최종 세션 완결과 동시에 **`output/` 하위에 적절한 속성의 물리 파일**이, **`log/` 하위에 영구 로그 파일**이 날짜 포맷에 맞춰 안전하게 보관되는지 파일 시스템 무결성 검증.
- [ ] `tests/test_shm_orchestrator.py` 및 `tests/test_shm_broadcast.py` 통합 연동 테스트가 모두 합격(OK)되는지 확인.

---

## 3. Troubleshooting & Smoke Test

### 3.1. 웹뷰 UI 동결(Freeze) 오류
- **현상**: 사용자가 입력창에 전송 버튼을 누르면 UI가 수 초간 먹통이 되며 챗 스크롤이 움직이지 않음.
- **조치**: pywebview API 함수 내에서 직접 LLM/SDK 및 대기 딜레이를 유발하는 오케스트레이터를 호출하지 말고, 반드시 **`threading.Thread` 백그라운드 데몬 스레드**로 분리 스폰하여 기동하십시오.

### 3.2. 에이전트 챗 버블 색상 미반영 오류
- **현상**: 메인 AI나 에이전트 A, B의 메시지가 모두 회색의 일반 버블로 똑같이 표현되어 3자 격리가 되지 않음.
- **조치**: `index.html` 의 `addMessage` 내부 `sender` 문자열 스몰라이즈 맵핑 시 `main_ai`, `agent_a`, `agent_b` 구분이 CSS 클래스 `main-ai`, `agent-a`, `agent-b` 와 정확히 일치하는지 확인하십시오.

### 3.3. 산출 파일 생성 쓰기 결함 (NameError)
- **현상**: 최종 승인 후 `output/` 폴더에 파일이 기입되지 않고 `af.write` 관련 런타임 Exception이 유도됨.
- **조치**: `app_webview.py` 내의 파일 라이터 컨텍스트 블록 변수명(`cf` vs `af`) 매핑이 정상적으로 정비되어 `cf.write(clean_code)` 로 호출되는지 코드 정합성을 필히 교차 심사하십시오.

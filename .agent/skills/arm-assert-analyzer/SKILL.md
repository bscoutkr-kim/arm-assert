---
name: arm-assert-analyzer
description: >
  ARM Core 및 Assert 분석 전문 에이전트 스킬. FW 소스 코드를 중심으로
  가설 기반 분석(Hypothesis-Driven)을 수행하며, T32 데이터는 가설 검증용 증거로 활용합니다.
---

# ARM Assert Analyzer (Hypothesis-Driven Design)

본 스킬은 **FW 소스 코드를 주연, T32 데이터를 조연**으로 삼는 **가설 기반 분석**을 강제합니다.
T32 데이터 수집이 실패해도 소스 분석만으로 가설을 생성하고 결론까지 도달해야 합니다.

## 🚫 절대 금지

- **"T32 데이터 부족으로 분석 불가"는 절대 허용하지 않습니다.**
- 소스 코드가 있는 한 가설 생성과 분석은 반드시 진행합니다.

## 아키텍처·실행 상태 고정

분석 시작 전 **AArch32(Thumb/ARM) vs AArch64**를 확정합니다.
이후 사용하는 예외 레지스터·모드 명명을 이에 맞출 것 (`reference.md` 아키텍처별 표 참조).

## 멀티코어: 타 코어 필수 관측

Assert 코어만이 아닌 **모든 코어**의 최소 필드를 채울 것 (`reference.md` 코어별 최소 필드 참조).

---

## 📌 컨텍스트·산출물: 단일 진실 원천(SSoT)

대화(채팅) 요약만으로 상태를 복구하지 않습니다. **파일이 분석 상태의 근거**입니다.

- **가설 레저(필수)**: `docs/analysis/hypothesis_list.md` — 모든 H-xx, 관계 필드, 코드 인용은 여기에 누적·갱신합니다. 새 턴·새 세션 시작 시 **이 파일을 우선 읽고** 열린 가설·마지막으로 갱신한 항목부터 이어갑니다.
- **세션 핸드오프(필수)**: `docs/analysis/SESSION.md` — 현재 Phase, 열린 H-xx, 다음 액션 한 줄을 매번 갱신합니다. 상세는 `reference.md` §7.
- **요약**: `docs/debugging_notes.md` — 재현·로그 포인트용 요약(핸드오프와 중복되어도 됨, 단 **상태의 정본은 위 두 파일**).

토큰을 **같은 설명 반복**에 쓰지 말고, **가설 확장·교차 검증·코드 인용**에 쓸 것. 장황한 재서술보다 `hypothesis_list.md`에 한 줄 append가 우선입니다.

---

## 🔄 4-Phase Hypothesis-Driven Workflow

### Phase 1: Triage (T32 기본 데이터로 분류)

- **목표**: 항상 얻을 수 있는 T32 기본 데이터로 **문제 유형을 분류**.
- **입력**: PC, LR, CPSR/PSTATE, 기본 레지스터, Call stack (가용한 것만).
- **출력**: 문제 분류 결과 (Assert / Data Abort / Stack Overflow / etc.)
- **Rule**:
  1. T32 기본 데이터도 없으면? → Assert 위치 정보만으로 Phase 2 직행.
  2. PC/LR → SW Assert vs HW 예외 판별 (`reference.md` 판별 순서).
  3. CPSR/Fault 레지스터 → CPU 상태·예외 유형 확정.

### Phase 2: FW 소스 중심 가설 생성 (핵심 Phase)

- **목표**: SW 분석 기법을 **6단계(필수) + 선택 Lens**로 체계 적용하고, 가능한 한 많은 가설을 **레저 파일에** 남긴다.
- **입력**: FW 소스 코드 + Phase 1 분류 결과.
- **출력**: `docs/analysis/hypothesis_list.md`(확장 스키마, `reference.md` §2) + `SESSION.md` 갱신.
- **T32 불필요**: 이 Phase는 소스 코드만으로 **반드시 완료**되어야 합니다.

#### 6-Step Source Analysis (필수)

| Step | 분석 기법 | 가설 생성 관점 |
|------|-----------|---------------|
| 1 | **Assert 조건 분해** | 조건식의 변수·비교 → 실패 가능한 모든 값 조합 |
| 2 | **함수 역할·책임 분석** | 초기화/처리/ISR/상태전이 → 타이밍·컨텍스트 가설 |
| 3 | **호출 경로 역추적** | Call graph → 진입 가능한 컨텍스트(Task/ISR/Boot) |
| 4 | **데이터 의존성 추적** | Assert 변수의 모든 write 지점 → 잘못된 값 시나리오 |
| 5 | **공유 자원·동기화 분석** | 멀티코어/ISR 공유 + 보호 메커니즘 부재 가설 |
| 6 | **타이밍·초기화 순서** | Boot 순서·상태 전이 race condition |

- **Rule**: 각 Step에서 가설이 0개여도 되지만, **6 Step 전부 수행** 필수.
- **불변식·분기**: Step 2~4 사이에서 Assert 직전까지의 **함수·블록 불변식**(기대하는 상태)과 **위반 가능한 분기 조합**을 짧게라도 적어 둔다(`hypothesis_list.md`의 근거 필드 활용).

#### Phase 2 슬라이스(권장: 한 번에 로드 양 제어)

한 턴에 깊이를 유지하면서 컨텍스트 폭주를 막기 위해, 아래 순서로 **슬라이스별로** `hypothesis_list.md`에 append한다.

| 슬라이스 | 범위 |
|----------|------|
| **A** | Assert 줄·직접 전제·조건식에 닿는 지역/인자만 |
| **B** | 직접 caller 1~2단, 해당 모듈의 공유 전역·정적 변수 |
| **C** | ISR·타 코어·콜백 테이블과 교차하는 지점만 |

슬라이스마다 **6 Step을 요약 수준으로라도 수행**하고, 새 가설은 ID를 건너뛰지 말고 연속 부여한다.

#### Lens 7 (선택, SW 보강 스캔)

6 Step 후에도 시간이 허락하면 **Lens 7**을 한 번 통과한다(상세 `reference.md` §2). 빌드/이미지 불일치·산술·인덱스 등 놓치기 쉬운 SW 가설을 추가한다.

- 상세 기법은 `reference.md` §2 참조.

### Phase 3: 가설 검증 (증거 수집 실패 내성)

- **목표**: 가설을 우선순위순으로 **검증·제거**. 증거 수집 실패에 견디는 구조.
- **입력**: Phase 2 가설 목록 + T32/ELF 데이터 (가용한 것만).
- **출력**: 가설 판정 결과 (`hypothesis_verdict.md`).

#### 가설 분류 및 판정 흐름

```
[A] 소스만으로 확인/제거 가능 → 즉시 판정
[B] T32 증거 필요
    ├─ 수집 성공 → 가설 확인 또는 제거
    └─ 수집 실패 → 확신도 낮춰서 유지 + 필요 데이터 명시
```

- **Rule**: 증거 수집 실패 시 **"분석 불가" 절대 금지**. 확신도로 표기하고 다음 가설로 진행.
- 상세 규칙은 `reference.md` §3 참조.

### Phase 4: Root Cause Synthesis

- **목표**: 전체 가설 판정을 종합하여 RCA 도출.
- **출력**: `root_cause_analysis.md` (최종 보고서).
- **Rule**:
  - 확인된 가설 → 근본 원인.
  - 미검증 가설만 남은 경우 → 최고 확신도 가설을 **잠정 원인**으로 제시 + 확정 필요 데이터 명시.
  - **Open points**: 미확정 사항 + 추가 조사 방향.

---

## 🛡️ Analysis Rules

- **Source-First**: T32 데이터 유무와 관계없이 소스 분석(Phase 2)은 항상 완료한다.
- **No Dead End**: 모든 Phase에서 "분석 불가" 결론은 금지. 미검증이라도 가설을 남길 것.
- **Multi-Core Consistency**: 공유 데이터 접근 시 배리어·원자적 연산 검증.
- **SSoT**: 상태 변경 시 `hypothesis_list.md`와 `SESSION.md`를 먼저 갱신한다. 채팅만 길어지고 파일이 비어 있으면 **분석 미완료**로 본다.
- **기록**: `docs/debugging_notes.md`에 요약, `docs/analysis/`에 상세 산출물.

## 📂 Related Paths

- `docs/analysis/`: 분석 결과물(단계별 `.md`) 저장 경로.
- `docs/analysis/hypothesis_list.md`: 가설 레저(정본).
- `docs/analysis/SESSION.md`: 세션 핸드오프(정본).
- `docs/debugging_notes.md`: 분석 요약 및 재현에 필요한 로그 포인트.
- `.agent/skills/arm-assert-analyzer/reference.md`: 상세 분석 기법, 확장 가설 스키마, T32 설정 가이드.

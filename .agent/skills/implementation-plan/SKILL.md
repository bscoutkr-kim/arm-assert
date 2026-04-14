---
name: implementation-plan
description: >
  Plan → implement → verify; plan types (bugfix vs feature vs verification/analysis); bugfixes
  prioritize minimal symptom/root-cause patches—no “fix by new feature” unless minimal path fails
  and user approves a separate feature plan. Use when the user wants an implementation plan
  (e.g. 계획서, 구현 계획, 계획을 작성, implementation plan).
---

# Implementation Plan

**전체 워크플로우, 출력 형식, 관련 스킬 상세:**
→ `.agent/skills/implementation-plan/reference.md`

## Purpose (요약)

코드 변경의 전체 흐름을 **계획 → 구현 → 검증** 3단계로 체계화합니다.

1. **범위 준수** — 사용자가 요청한 기능·수정만 계획에 넣는다. 요청과 무관한 **새 기능·리팩터·“개선”**을 넣으려면 **반드시 사용자에게 알리고 승인**받은 뒤에만 범위에 포함한다. (임의 추가는 새 불량을 만들기 쉽다.)
2. **제거/대체 대상(Deprecation & Cleanup List) 필수** — 기능을 대체하거나 통일할 경우, **어떤 함수/모듈/로직이 제거될 것인지**를 계획서에 명시하고, 구현 시 이를 철저히 준수하여 코드 비대화를 방지한다.
3. **계획 유형 구분** — **버그 수정**, **신규 기능**, **검증·분석**(리뷰·로그·원장·재현 조사 등)을 구분해 계획서에 명시한다. 한 번에 여러 유형이 필요하면 **주 유형**을 먼저 밝히고, 나머지는 **별도 소절**로 분리한다. (상세: `reference.md` Scope 절.)
4. **버그 수정 = 현상·원인 위주 최소 수정 우선** — **신규 기능·새 동작으로 버그를 우회·대체하지 않는다.** 재현·원인에 맞는 **최소 패치로 불량을 닫는 안**을 먼저 제시·실행한다. 최소안이 **불가·불충분**할 때만 **신규 기능(동작 확장) 계획**을 **별도 안**으로 작성해 사용자 승인을 받은 뒤 진행한다. 개선·리팩터는 수정 검증 후 **제안**으로만 분리한다.
5. **계획 단계**: `code-writing-guard`로 중복·호환성 코드를 방지하고 수정 범위를 확정
6. **구현 단계**: 승인된 계획에 따라 직접 구현 — 규칙 위반 즉시 수정
7. **검증 단계**: `verify-implementation` 또는 관련 `verify-*` 스킬로 규칙 준수 확인
8. **테스트 코드 위치(필수)**: **새로 작성하는 모든 테스트 코드**는 저장소 루트 **`tests/`** 이하에만 둔다. **신규 묶음은** **`tests/<역할요약>_YYMMDD/`** 서브폴더를 만들고 그 안에서 진행한다 (`code-writing-guard` `reference.md` §12). 계획서·구현 시 경로도 **`tests/<이름>_YYMMDD/...`** 형태로 적는다.

## When to Run

- 새 기능 구현 시작 전
- 대규모 수정 또는 리팩토링 계획 시
- 버그 픽스 계획 시

## Related Skills

| 역할 | 스킬 |
|------|------|
| 계획 단계 가드 | `code-writing-guard` |
| 최종 통합 검증 | `verify-implementation` |
| 도메인 검증 | `verify-grid-algorithm`, `verify-order-execution`, `verify-api-routes` 등 |
| 산출물을 `docs/` 파일로 남길 때 | `document-authoring` (`*_YYMMDD.md`, 폴더 분류) |

## Workflow (outline)

1. **PLANNING** — 요청 범위 확정, (불량이면) 수정 최소안 vs 개선안 분리, 중복 검색, 계획 문서 작성 (→ `reference.md`)
2. **EXECUTION** — 승인된 범위만 구현, 위반 즉시 수정, JSDoc 작성 (→ `reference.md`)
3. **VERIFICATION** — `/verify-implementation` 실행, 결과 보고 (→ `reference.md`)

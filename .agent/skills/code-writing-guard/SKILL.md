---
name: code-writing-guard
description: >
  코드 작성 및 수정 시 클린 코드 원칙과 프로젝트 표준을 강제합니다.
  중복 코드 금지, 래퍼/레거시 코드 제거, 매직 넘버 상수화 등을 포함합니다.
  코드 수정을 요청받았을 때(수정, 구현, 추가, 변경, fix, implement, modify 등) 항상 참조하십시오.
---

# Code Writing Guard

**Examples, `rg` commands, DTO/fallback nuance, OS abstraction, Grid UI (GridConfigManager vs ViewModel), runtime config/logs/stockInfo/grid_trade_logs paths (`reference.md` §11), automated tests under `tests/<name>_YYMMDD/` (`reference.md` §12), optional verify-by-area table:**  
→ `.agent/skills/code-writing-guard/reference.md`

## Purpose

1. **중복 구현 금지 (Mandatory search)** — 수정/추가 전 파일 내 관련 키워드를 반드시 검색하여 기존 로직/변수와의 중복을 확인한다. 중복 변수 생성을 금지한다.
2. **래퍼/호환성/레거시 계층 금지 (Active Deletion)** — 실제 구현부를 직접 호출하고, 이전의 호환성 코드는 완전히 제거한다.
3. **불필요한 로직 제거** — 함수나 로직 교체 시, 기존 로직이나 중복된 검증 로직은 반드시 제거한다.
4. **Data Integrity Deep Guard** — 객체의 중첩 속성(nested properties) 참조 시, 최하위 속성까지 안전한 폴백(fallback)을 갖춰 런타임 에러를 차단한다.
5. **명확한 에러 처리 (No silent fallbacks)** — 중요한 데이터 처리 시 조용한 폴백 대신 로그나 알림을 통해 예외 상황을 고지한다.
6. **매직 넘버/스트링 금지** — 명명된 상수(Named Constants)나 설정을 사용한다.
7. **일관된 네이밍 규칙** — 프로젝트 관례에 맞는 네이밍(예: camelCase 등)을 유지한다.
8. **분석 가능한 로깅** — 비즈니스 로직(분기, 상태 전이 등)은 사후 분석이 가능하도록 충분한 컨텍스트를 로깅한다.

## When To Use

- Before new functions, classes, modules, or shared helpers.
- Before non-trivial refactors (also follow **`/refactoring-safety`** when large).
- When the user asks to **apply review or inspection findings** from the same thread (e.g. `/verify-implementation` **수정·개선 필요** 목록) — treat as **implementation work** and run this skill end-to-end (plan per **`CLAUDE.md`** if required, then edit code/docs).

---

## Debugging notes (**required** after substantive code work)

When you **finish** a code change or improvement that is **non-trivial** (bugfix, behavior change, refactor, new feature slice), you **must** add a **brief** entry to **`docs/debugging_notes.md`** — not optional. Keep it to **~5 lines**, **newest-first** under the template, fields **`when` / `topic` / `change` / `test` / `evidence` / `next`**. Format and examples: **`reference.md` §1**; policy: **`CLAUDE.md`**.

Pure typo-only or comment-only edits may skip an entry **only if** they change no behavior (team discretion).

---

## Git commit / push (**user request only**)

- **Do not** commit, push, or run **`/git-push-workflow`** unless the **user explicitly** asks to commit and/or push (see **`CLAUDE.md`**).
- When asked, use **`git-push-workflow`** (Korean commit message, project workflow) — details in **`.agent/skills/git-push-workflow/SKILL.md`**.

---

## Skills that directly support **writing** (use when applicable)

| Skill | Use when |
|-------|----------|
| `/logging-standards` | 로그 추가/수정 시 |
| `/jsdoc-standards` | 공개 API 또는 함수 문서화 시 |
| `/refactoring-safety` | 대규모 구조 변경 시 |

`/verify-implementation`은 통합 검증 단계에서 사용하며, 모든 작은 수정마다 실행할 필요는 없습니다.

---

## Workflow (concise)

1. **Understand** scope and **`CLAUDE.md`** constraints.
2. **`rg` / search (Essential)** — 수정하려는 변수명, 로직 키워드로 파일 전체를 조회하여 중복 및 연관 로직을 사전 파악한다 (`reference.md` §4).
2.5. **Domain Guard Analysis (사전 분석)** — 수정 대상 파일과 관련된 **`verify-*` 스킬(`SKILL.md` 및 `reference.md`)**을 읽고, 해당 도메인의 설계 원칙, 금지 패턴, 필수 로직을 파악하여 구현 설계에 반영한다 (`reference.md` §3).
3. **Deep Guard Implementation** — 중첩 속성 참조 시 `reference.md` §6.1 에 정의된 안전 패턴을 적용한다.
4. **Reject** wrappers/compat; **reject** silent `||` defaults for real business data (`reference.md` §5–6).
5. **Replace** magic values with constants/settings (`reference.md` §7).
6. **Python:** no scattered `sys.platform` — use project abstraction (`reference.md` §8).
7. Run **writing** skills from the table above that match your edits.
8. **After-Write Gate (필수 — "완료" 선언 전 반드시 통과)** — `reference.md` §9 전체 체크리스트 실행:
   - **중복 변수**: 같은 참조를 다른 이름으로 선언했는가? (`const a = x; const b = x;`) → 하나 제거
   - **중복 검사**: 동일 보정·검증이 두 곳에 있는가? → 나중 것 제거
   - **Deep Guard 완전성**: `if (!x) { x = fallback }` 후 `x.prop` 접근이 있다면 fallback도 undefined일 때 최종 하드코딩 가드 필요 (`reference.md §6.1`)
   - **로그 메시지 정확성**: 메시지가 현재 실행 단계(Render/Collect/Save)를 정확히 설명하는가?
   - **실제 데이터 에러 가시성**: `hasStock === true` 등 실제 데이터 처리 시 에러가 로그에만 묻히지 않는가?
10. **New test code** — place under **`tests/<name>_YYMMDD/`** (new subfolder per batch; `YYMMDD` = creation date) inside repo-root **`tests/`** only (`reference.md` §12); record the command in **`docs/debugging_notes.md`** `test` when substantive.
11. **Append `docs/debugging_notes.md`** if the change is substantive (§ above).
12. **Skill Listing (필수)** — 응답 마지막에 `📋 사용된 스킬:`을 작성할 때, 본 스킬(`/code-writing-guard`)뿐만 아니라 작업 중 실제로 읽거나 실행한 모든 하위 스킬(/logging-standards, /jsdoc-standards, 도메인 `/verify-*` 등)을 누락 없이 나열한다.

---

## Never Do

- Global `window.*` helpers / “compat” shims (see **`CLAUDE.md`**).
- Fill gaps with guesses — if data is missing, **error or user-visible failure**.
- Add a **new** verify skill to this file’s “must read” list without cause — **optional map stays in `reference.md` §3**.
- **Commit/push** without the **user’s explicit request**.

---

## Related

- **`reference.md`**: 검색 패턴, 폴백 예시, 디버깅 노트 템플릿 등.
- **`git-push-workflow`**: push 작업 시 (사용자 명시 요청 시에만).
- **`CLAUDE.md`**: 프로젝트 절대 원칙 (한글).

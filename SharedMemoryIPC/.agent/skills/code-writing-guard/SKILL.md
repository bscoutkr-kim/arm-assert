---
name: code-writing-guard
description: >
  Enforces mystock_web JS/Python authoring rules: no duplicate or wrapper code, explicit errors
  instead of silent defaults, constants over magic numbers, and project conventions in SKILL.md.
  Use when the user asks to write, change, or implement code (e.g. 수정해줘, 코드 수정, 구현해줘,
  코드 작성, 추가해줘, 변경해줘, fix, implement, modify).
  Also use when applying prior review or verification output as code/doc changes (e.g. 위의 검토 내용을 반영해줘,
  검토 내용 반영, 리뷰 이슈 반영, 수정·개선 필요 반영, 피드백 반영, apply the review, implement the review feedback).
---

# Code Writing Guard

**Examples, `rg` commands, DTO/fallback nuance, OS abstraction, Grid UI (GridConfigManager vs ViewModel), runtime config/logs/stockInfo/grid_trade_logs paths (`reference.md` §11), automated tests under `tests/<name>_YYMMDD/` (`reference.md` §12), optional verify-by-area table:**  
→ `.agent/skills/code-writing-guard/reference.md`

## Purpose

1. **No duplicate implementation (Mandatory search)** — 수정/추가 전 파일 내 관련 키워드를 반드시 `rg`로 검색하여 기존 로직/변수와의 중복을 확인한다. 동일 객체 참조 중복 변수(`gDef` vs `globalDef` 등) 생성을 금지한다.
2. **No compatibility/wrapper/legacy layers (Active Deletion)** — call the real implementation; update call sites; **remove the old code entirely**.
3. **No residual/redundant logic** — 함수나 로직 교체 시, 기존 로직이나 중복된 검증 로직은 반드시 제거한다. 한 파일 내 동일한 검사 로직의 중복 배치를 금지한다.
4. **Data Integrity Deep Guard** — 객체의 중첩 속성(nested properties) 참조 시, 최하위 속성까지 안전한 폴백(fallback)을 갖춰 `TypeError` 크래시를 원천 차단한다.
5. **No silent business fallbacks for Real Data** — 빈 슬롯이 아닌 실제 데이터(`hasStock === true`) 처리 시에는 조용한 폴백 대신 반드시 로그(`warn`/`error`)나 UI 알림을 통해 사용자에게 예외 상황을 고지한다.
6. **No unexplained magic numbers/strings** — named constants, settings, or shared config.
7. **camelCase** for internal/domain fields and APIs you control (not raw exchange payloads).
8. **Grid UI split** — **표시·설정**은 **`gridConfigManager.js`** SSOT; **진행 화면**은 **`auto_trade_grid_viewmodel.js`**에서 데이터를 받는다. 상세·검증 매핑은 **`reference.md` §10** · **`verify-grid-viewmodel`**.
9. **저장·로그 경로** — `stockInfo`, `grid_trade_logs`, 설정 JSON 위치는 **`reference.md` §11** (SSOT는 `path_utils` / `logging_utils` / `api_utils`).
10. **Analysis-Ready Logging & 진단 가능한 실패 메시지** — 비즈니스 로직(분기, 상태 전이)은 **`/logging-standards` `reference.md` §2.1** 처럼 분석 가능한 컨텍스트로 로깅한다. **실패·경고·텔레그램·운영 알림**에도 **원인 추적 맥락**(모듈, 심볼·식별자, HTTP·외부 오류 요약; 민감값 제외)을 넣고 **고정 문구 단독**을 피한다 — **`/logging-standards` `reference.md` §14.2** (HTTP JSON은 §14.1).
11. **브라우저 → Flask HTTP** — 기본은 **`window.api_fetchAPIData`**. 예외적 `fetch`는 주석으로 이유 명시. 상세: **`reference.md` §5.5**.
12. **브로커·시장 구분** — `exchangeProvider` / `api_isCrypto` / `api_getMarketType` SSOT. 상세: **`reference.md` §5.6**.
13. **가격 참조** — DGO·UI 평가 기준은 오더북 매수 1호가(`bid_price`/`bid`) 우선, 실제 매수 주문 트리거는 매도 1호가(`ask_price`/`ask`)가 타점 이하일 때만 체결 가능 진입으로 본다. 상세: **`reference.md` §10**.
14. **Karpathy-Style Coding Principles** — 구현 단계에서도 **Think Before Coding**(가정·`rg` 선검색·트레이드오프), **Simplicity First**(직접적 해법 우선), **Surgical Changes**(수정 범위 최소화), **Goal-Driven Execution**(검증 가능 성공 기준 기반)을 준수한다.
15. **종목 코드 정규화 (Normalization) — SSOT 의무** — 모든 종목 코드(`stockCode`) 비교, Map 키 참조, 예외 목록 검사 시 반드시 **`api_normalizeSymbol`** (JS) 또는 프로젝트 표준 정규화 함수를 사용하여 데이터 불일치를 원천 차단한다. 상세: **`reference.md` §14**.
16. **Graphify·지식 그래프 (선행 READ + 갱신, 증적 필수)** — **`static/`·`routes/`·`templates/`·`mystock_web.py` 등 앱 소스를 첫 수정하기 전** `graphify-out/GRAPH_REPORT.md`에서 God Nodes·관련 Community를 확인한다(`reference.md` §2.6·§9.F). **수정 후** 저장소 루트 **PATH `graphify` CLI**로 **`graphify update .`** (`npx` 금지). 완료 보고 `Graphify Evidence`에 **확인 날짜·활용한 허브/Community(최소 1개 또는 허용 예외)**·갱신 여부를 반드시 남긴다.
17. **알고리즘 UI ↔ 엔진 단일 경로 (위반 시 무의미)** — 자동매매·분석 **알고리즘과 연결된 UI**(후보 선별·필터 Pass/Fail·진행 단계·“매수 가능” 등 **매매 의미가 있는 표시**)는 **`autoTradeCore_Var_*`·`Var_Portfolio` 등 코어 전역만 읽어 별도 규칙으로 재판정하지 않는다.** 반드시 해당 알고리즘의 **문서화된 SSOT**(엔진·스냅샷·`gridConfigManager`/ViewModel 계약 등)만 호출한다. UI만 따로 두면 사용자에게 **거짓 신호**를 보여 주므로 **금지** — 상세·예시는 **`reference.md` §2.5**.

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
| `/logging-standards` | Adding/changing JS logs |
| `/jsdoc-standards` | New/changed public JS API |
| `/module-registration` | New module / global registration |
| `/html-registration` | New browser JS file |
| `/refactoring-safety` | Large structure changes |
| `/graphify` | 앱 소스 **첫 수정 전** `GRAPH_REPORT.md` Read · 수정 후 **PATH** `graphify update .` (§2.6·§9.F) |

Do **not** run the **entire** `/verify-implementation` batch or every `verify-*` checklist yourself on **trivial** edits unless the user asks or §0 mandates it. **However:** `manage-skills/reference.md` **§0.1** still requires **cross-`Read`** of the **`verify-*/reference.md`** that match the files you **Read**/**change** (domain audit). Functional lifecycle checks for grid orders are **`verify-grid-order-lifecycle`** (+ **`verify-order-execution`** for OrderManager). **`/verify-implementation`** remains an optional **merge/PR gate**.

---

## Workflow (concise)

1. **Understand** scope and **`CLAUDE.md`** constraints.
2. **Graphify Read (필수, 앱 소스 수정 시)** — `GRAPH_REPORT.md`에서 God Nodes·관련 Community 확인 후 수정 범위를 좁힌다 (`reference.md` §2.6). 스킬·문서만이면 생략 가능.
3. **`rg` / search (Essential)** — Graphify·도메인 `verify-*` reference와 함께, 변수명·로직 키워드로 중복·연관 로직을 사전 파악한다 (`reference.md` §4).
4. **Deep Guard Implementation** — 중첩 속성 참조 시 `reference.md` §6.1 에 정의된 안전 패턴을 적용한다.
5. **Reject** wrappers/compat; **reject** silent `||` defaults for real business data (`reference.md` §5–6).
6. **Replace** magic values with constants/settings (`reference.md` §7).
7. **Python:** no scattered `sys.platform` — use project abstraction (`reference.md` §8).
8. Run **writing** skills from the table above that match your edits (**`/logging-standards`** + **`reference.md` §2.1 표준 로그** when touching `logMgr_ModuleLog`).
9. **After-Write Gate (작성 표준 검사)** — `reference.md` §9(A–F) 체크리스트 실행:
   - **중복 변수**: 같은 참조를 다른 이름으로 선언했는가?
   - **중복 검사**: 동일 보정·검증이 두 곳에 있는가?
   - **Deep Guard 완전성**: 최종 하드코딩 가드 필요 여부 확인
   - **로그 메시지 정확성**: 단계(Render/Collect 등) 설명이 정확한가?
   - **실제 데이터 에러 가시성**: `hasStock === true` 경로 확인
10. **Graphify update (필수)** — 앱 소스 의미 변경 후 `graphify update .` (PATH CLI; Windows `$env:PYTHONUTF8='1'` 권장). §9.F `Graphify Evidence` 미작성 시 gate 실패.
11. **Append `docs/debugging_notes.md`** if the change is substantive.
12. **Skill Listing** — 응답 마지막에 `📋 사용된 스킬:` 작성.

> **주의**: 기능적 정합성 및 생명주기 검증은 **Antigravity Manager (`GEMINI.md`)**가 자동으로 병렬 실행하는 `verify-*` 스킬에서 담당합니다. 작성 스킬은 오직 **작성 표준(Quality)**에 집중합니다.

---

## Never Do

- **알고리즘 전용 “화면 안에서만 통과/실패” 로직** — 엔진 SSOT 없이 매매 의미 있는 표시를 만들 것 (**`reference.md` §2.5**).
- Global `window.*` helpers / “compat” shims (see **`CLAUDE.md`**).
- Fill gaps with guesses — if data is missing, **error or user-visible failure**.
- Add a **new** verify skill to this file’s “must read” list without cause — **optional map stays in `reference.md` §3**.
- **Commit/push** without the **user’s explicit request**.

---

## Related

- **`reference.md`**: `rg` snippets, DTO note, verify-by-area table, **§2.1 표준 로그**, **§2.5 알고리즘 UI SSOT**, **§10 Grid UI** (GridConfigManager vs ViewModel), debugging notes template.
- **`verify-grid-viewmodel`**: 진행 화면·ViewModel 검증 — **`reference.md` §10**과 짝.
- **`git-push-workflow`**: push workflow — **only when user asks**.
- **`CLAUDE.md`**: absolute project rules (Korean), including git and debugging notes.
- **`/graphify`**: `graphify-out/` 유지·아키텍처 탐색 — **`graphify/SKILL.md`**, **`.cursor/rules/graphify.mdc`**.
- **`debug-log-analysis`** (`SKILL.md` **Core heuristics**): symptoms vs root cause, duplicate handler registration.

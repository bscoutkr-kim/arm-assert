---
name: logging-standards
description: >
  Defines frontend logMgr_ModuleLog patterns and Python logging; bans console.* in JS.
  Use when adding or changing logs or MODULE_NAME logging (e.g. 로그, 로깅 규칙).
---

# Logging Standards Skill

**Code samples, `rg` snippets, level table, exceptions, agent template:**  
→ `.agent/skills/logging-standards/reference.md`

## Purpose

1. **No `console.log` / `warn` / `error` / `info`** in frontend app code — use **`window.logMgr_ModuleLog`** (see **`reference.md` §1** for allowed exceptions).
2. **Analysis-Ready Logging (Mandatory)**: All critical state changes, branching decisions (especially "Skip" or "No-action" branches), and strategic transitions must be logged with enough context (symbol, round, price) for offline analysis.
3. **Levels:** `'info'` | `'warn'` | `'error'` | `'high'` | `'debug'` — see **`reference.md` §3**.
4. **Prices/amounts:** format with **`window.marketUtils_FormatPriceWithDecimal`** and currency from **`market_getCurrencyInfo`** — **`reference.md` §4**.
5. **Module name:** use a **`MODULE_NAME`** constant (or class static), not ad-hoc strings — **`reference.md` §5**.
6. **Python:** standard library **`logging`** in `routes/*.py` — never `window.*`.
7. **표준 로그 (프로젝트 정책)** — 프론트에서 **새로 추가하거나 의미 있게 수정**하는 `logMgr_ModuleLog` 메시지는 **`/code-writing-guard`** `reference.md` **§2.1** 과 본 스킬을 **함께** 따른다. (세션·원장 분석 시 과거 로그와 혼용: **`/log-analysis-workflow`** `reference.md` §1.4.)
8. **`error` 레벨·ErrorCollector** — `Error` 객체를 그대로 넘기면 장애 알림에 `{}`만 보일 수 있음. **`reference.md` §14** 및 **`verify-log-standards` Step 7** 준수.
9. **HTTP/JSON 실패 응답** — Flask는 업무 실패 시 **`error` + `detail`(구체 원인)** 을 함께 내려주고, `api_client.js`는 `detail`을 사용자·장애 알림 문자열에 병합한다. 고정 문구만으로 끝내지 않음 — **`reference.md` §14.1**.
10. **실패·경고·운영 알림 전반** — API뿐 아니라 **`error`/`warn` 로그**, **Python 로깅**, **텔레그램·장애 알림**에도 **원인 추적 가능한 맥락**(무엇·왜·어디서 재현할 식별자, 민감값 제외)을 넣는다. 고정 문구 단독 금지 — **`reference.md` §14.2** (고빈도 루프는 §13 예외).

## When To Use

- Adding or changing log lines in **`static/js`**.
- Reviewing PRs for stray **`console.*`**.
- New modules that emit logs.

## Related paths

| Path | Role |
|------|------|
| `static/js/utils/log_manager.js` | `logMgr_ModuleLog`, ErrorCollector 직렬화 |
| `static/js/utils/api_client.js` | `api_fetchAPIData` 실패 문자열·`detail` 병합 |
| `routes/api_notification.py` 등 | 실패 시 `error` + `detail` (§14.1) |
| `static/js/utils/market_utils.js` | Price formatting helpers |
| `static/js/**/*.js` | Application code |
| `routes/*.py` | Python `logging` |

---

## Workflow (concise)

1. **`rg`** for **`console.(log|warn|error|info)`** — remove or replace (**`reference.md` §1, §7**).
2. Ensure **`logMgr_ModuleLog(moduleName, message, level)`** — **`reference.md` §2**.
3. Money in messages → **format** per **§4** in reference.
4. **`MODULE_NAME`** for first argument — **§5** in reference.
5. Python changes → **`logging`** module, appropriate level.

---

## Rules (never do)

- Ship new **`console.*`** in production paths without meeting **`reference.md` §8**.
- Log raw numeric **price/amount** strings when formatted helpers exist for that context.
- **Log Flooding**: 고빈도 반복 루프(Loop)나 1초 단위 폴링 로직 내에서 매번 `'info'` 이상의 로그를 남기는 행위. 상태 변화가 있을 때만 남기거나, `'debug'` 레벨을 사용하십시오 (**`reference.md` §13**).
- Invent **module** strings per call — use one **constant** per file/module.
- 새/수정 **Flask JSON 오류 응답**에 **`detail` 없이** 고정 `error` 문구만 넣고 끝내기 (**`reference.md` §14.1** 금지).
- **실패·경고·텔레그램**에 “실패함/확인하세요” 등 **고정 문구만** 남기고, 알려진 원인·식별자를 빼기 (**`reference.md` §14.2** 금지).

---

## Related

- **`reference.md`**: wrong/right examples, fallback pattern, full snippet §6, detection §7, exceptions §8, output table §9.
- **`/verify-log-standards`** — optional project check for log structure (when touching many log lines).

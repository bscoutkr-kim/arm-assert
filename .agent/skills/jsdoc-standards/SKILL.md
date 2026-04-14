---
name: jsdoc-standards
description: >
  공개 API 및 함수에 대한 JSDoc 문서화(@param, @returns, @typedef 등) 및 @ts-check 표준을 정의합니다.
  새로운 함수 추가나 API 변경 시 항상 참조하십시오.
---

# JSDoc Standards Skill

**Examples, bash snippets, full templates, verification table, exception details:**  
→ `.agent/skills/jsdoc-standards/reference.md`

## Purpose

1. Document **public** functions/classes with **`@param`**, **`@returns`** (and **`@throws`** when relevant).
2. Model structured data with **`@typedef`** / **`@property`** instead of vague `{Object}` when the shape matters.
3. Type **`Window`** / globals via JSDoc (`@type`, `import()`) and/or **`global.d.ts`** (see `reference.md` §4).
4. Enable checking with **`// @ts-check`** on files you touch or new files.

## When To Use

- New or changed **public** functions, class constructors, module exports.
- New **`window.*`** assignments or global consumers.
- New **`global.d.ts`** or `static/js/types` entries.

## Scope (Files)

| Area | Notes |
|------|--------|
| `static/js/**/*.js` | Main application code |
| `global.d.ts` | Declarations if the repo uses them |
| `static/js/types/` | Shared typedefs / `.d.ts` fragments if present |

---

## Rules (concise)

### `@ts-check`

- Add **`// @ts-check`** at the **first line** of new files or files undergoing meaningful type/doc work.
- Fix reported issues or narrow types; do not silence without cause.

### Public functions

- Every **exported** or **prototype** method intended for external use: summary line + **`@param`** for each parameter + **`@returns`** (use `@returns {void}` if nothing returned).
- Use **`[optional]`** and describe defaults in text or JSDoc default syntax where applicable.

### Complex objects

- Prefer **`@typedef`** + **`@property`** for repeated or important shapes; reference the typedef in **`@param`** / **`@returns`**.

### Classes

- Class-level description; **`@property`** for notable instance/static fields when it helps consumers; **constructor** and **public methods** documented.

### Globals

- **`window.foo = ...`**: document with **`@type`** or project **`global.d.ts`** — see **`reference.md` §4**.

---

## Workflow (order)

1. **`@ts-check`** on the file if missing and appropriate.
2. **Public API** — complete JSDoc for changed signatures.
3. **`@typedef`** — add or update when parameters/returns are structured objects.
4. **Globals** — JSDoc and/or `global.d.ts` consistent with actual runtime.
5. Run **`read_lints`** / IDE diagnostics on edited files.

**Detection / search commands** — **`reference.md` §8**.

---

## Exceptions (summary)

Full list: **`reference.md` §10**. Typically relaxed: **private** module helpers, **tests**, minimal **IIFE** wrappers, trivial accessors, obvious inline callbacks — still document anything **non-obvious** or **risky**.

---

## Agent Output (when “verifying” JSDoc)

Use the **markdown table skeleton** in **`reference.md` §9** — summarize what was checked; list gaps with **file + symbol + issue**.

---

## Related

- **`reference.md`**: JSDoc 예시 및 예외 사항.
- 프로젝트 규칙: 로그 작성 시 `logging-standards` 스킬 참조.

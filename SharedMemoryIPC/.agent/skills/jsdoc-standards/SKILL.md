---
name: jsdoc-standards
description: >
  Defines JSDoc @param/@returns/@typedef and @ts-check for mystock_web public JS APIs.
  Use when documenting new exports or public APIs (e.g. JSDoc, 타입 주석).
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

- **`reference.md`**: code samples §1–7, `rg` §8, output template §9, exceptions §10, file map §11.
- Project rule: **`console.*` forbidden** — use `window.logMgr_ModuleLog` (see `logging-standards` skill); JSDoc does not replace that.

# JSDoc Standards — Reference

Companion to `SKILL.md`. Examples, detection commands, and templates.

---

## 1. `@ts-check`

Place at the **very top** of the file (before other code).

```javascript
// @ts-check
/**
 * @file Grid configuration manager
 */
class GridConfigManager {
    // ...
}
```

---

## 2. Function JSDoc

```javascript
// Bad: no JSDoc
function calculateTotal(price, quantity) {
    return price * quantity;
}

// Good
/**
 * Calculate total price for an order.
 * @param {number} price - Unit price
 * @param {number} quantity - Order quantity
 * @returns {number} Total price
 */
function calculateTotal(price, quantity) {
    return price * quantity;
}
```

---

## 3. `@typedef`

```javascript
/**
 * @typedef {Object} GridConfig
 * @property {string} code - Stock code
 * @property {string} name - Stock name
 * @property {number} maxRounds - Maximum rounds
 * @property {boolean} enabled - Whether enabled
 */

/**
 * @param {GridConfig} config
 * @returns {boolean}
 */
function validateConfig(config) {
    return config.maxRounds > 0;
}
```

Prefer `@typedef` over bare `@param {Object}` when the shape is stable and reused.

---

## 4. Window / globals

**Option A — JSDoc at assignment site**

```javascript
/**
 * @typedef {import('./grid').GridAlgorithm} GridAlgorithmClass
 */

/**
 * @type {GridAlgorithmClass}
 */
// window.GridAlgorithm = GridAlgorithm;
```

**Option B — `global.d.ts` (when used project-wide)**

```typescript
import { GridAlgorithm } from './static/js/core/algorithms/grid/grid';

declare global {
  interface Window {
    GridAlgorithm: typeof GridAlgorithm;
  }
}

export {};
```

Paths and imports must match the project layout.

---

## 5. Class JSDoc

```javascript
/**
 * Grid configuration manager.
 * @property {string} MODULE_NAME - Module identifier
 * @property {Map<string, GridConfig>} configs - Config storage
 */
class GridConfigManager {
    static MODULE_NAME = 'GridConfigManager';

    /**
     * @param {Object} options
     * @param {number} options.maxRounds - Default max rounds
     */
    constructor(options = {}) {
        this.configs = new Map();
        this.maxRounds = options.maxRounds || 50;
    }
}
```

---

## 6. Standard function template

```javascript
/**
 * Brief description.
 * @param {Type} paramName - Description
 * @param {Type} [optionalParam] - Optional
 * @param {Type} [paramWithDefault='default'] - Default value
 * @returns {ReturnType} What is returned
 * @throws {ErrorType} When this throws
 * @example
 * const result = myFunction(arg1, arg2);
 */
function myFunction(paramName, optionalParam, paramWithDefault) {}
```

---

## 7. `import()` typedef pattern

```javascript
/**
 * @typedef {import('./path/to/module').ExportedType} LocalTypeName
 */

/**
 * @param {LocalTypeName} param
 */
function useType(param) {}
```

---

## 8. Detection commands (ripgrep)

From repo root; adjust paths if needed.

```bash
# Files using @ts-check
rg -l "@ts-check" static/js

# @ts-check line samples
rg -n "^// @ts-check" static/js | head -20

# @typedef count / samples
rg -n "@typedef" static/js | head -30

# @param on Object (candidates for typedef)
rg -n "@param\s*\{Object\}" static/js | head -20

# Window assignments
rg -n "window\.\w+\s*=" static/js | head -30

# import() in typedefs
rg -n "@typedef\s*\{import" static/js | head -20
```

Heuristic “functions missing JSDoc” one-liners are fragile; prefer manual review or IDE tooling for enforcement.

---

## 9. Verification output template (for agents)

```markdown
## JSDoc Standards Result

### Summary
- @ts-check: N files (target: new/changed files)
- @param / @returns: reviewed for changed public APIs
- @typedef: N types touched
- Window / global.d.ts: as needed

### Checks
| Check | Status | Notes |
|-------|--------|-------|
| @ts-check | | |
| Public function JSDoc | | |
| @typedef for complex shapes | | |
| Window / global types | | |

### Gaps (if any)
| File | Symbol | Issue |
|------|--------|-------|
```

---

## 10. Exceptions (detail)

Not required to fully document:

- **Private** helpers used only inside a module (still encouraged for complex logic).
- **`tests/`**, `*.test.js` — project policy may differ.
- **Thin IIFE registration** — module id / registration may be documented instead of every inner name.
- **Trivial one-line** getters/setters (team discretion).
- **Inline anonymous callbacks** — document the outer function; inner callback only if non-obvious.

---

## 11. Related project files

| Location | Role |
|----------|------|
| `static/js/**/*.js` | Application JS |
| `global.d.ts` | Project-wide `Window` / globals (if present) |
| `static/js/types/` | Shared types (if present) |

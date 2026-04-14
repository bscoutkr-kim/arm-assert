# Code Writing Guard — Reference

Companion to `SKILL.md`. Examples, `rg` snippets, optional verification map, debugging notes detail.

---

## 1. Debugging notes (`docs/debugging_notes.md`) — **required**

After **substantive** code work (bugfix, behavior change, refactor, new feature slice), a brief entry is **mandatory** — same rules as **`CLAUDE.md`**.

- **Length:** ~**5 lines** of substance (not a full diary).
- **Order:** Newest first — **reverse chronological**, directly under the template at the top.
- **Fields:** `when`, `topic`, `change`, `test`, `evidence`, `next`
- **Skip** only for edits that do **not** change behavior (e.g. pure typo/comment), at discretion.

**Git:** use **`git-push-workflow`** only when the **user explicitly** requests commit/push — never push as part of default coding flow.

---

## 2. Skills to use **while writing** (not optional for those tasks)

| Skill | When |
|-------|------|
| `/logging-standards` | 로그 추가/수정 시 |
| `/jsdoc-standards` | 공개 API 문서화 시 |
| `/refactoring-safety` | 대규모 파일 이동/분리 시 |

These are **authoring** skills, not post-hoc test suites.

### 2.1 표준 로그

1. **분석 가능한 로그** — 비즈니스 이벤트에는 식별자, 상태 전이 맥락을 넣는다. 식별자 없이 감상만 있는 로그는 지양한다.
2. **구조 권장** — `grep`/스크립트 필터가 쉽게 하되, 기존 프로젝트 관례와 충돌하면 해당 파일 스타일을 우선한다.

---

## 3. Reference & Verification (수정 전 분석 및 수정 후 검증)

수정할 파일이 특정 도메인에 해당하면, 코드 작성 전에 관련 문서를 읽고 설계 원칙을 분석해야 합니다.

`Meta:` /verify-implementation은 전체 검증 체인을 실행합니다. 대규모 변경 후 또는 머지 전에 사용하며, 모든 작은 수정마다 전제 조건으로 두지 않습니다.

---

## 4. Search before implement (`rg`)

```bash
rg -n "keyword" path/to/dir
```

**Decision:** reuse/extend vs new — same naming style.

---

## 5. Wrapper / compat ban

**Forbidden:** names/uses suggesting `wrapper`, `compat`, `legacy`, `alias`; thin delegates.

**Do:** change call sites to the real implementation; improve the real API if needed.

```bash
rg -n "compat|legacy|wrapper|deprecated|alias" static/js
```

---

---

## 5.5. Protocol & API Rules

**Default:** 프로젝트의 표준 API 클라이언트가 있다면 이를 우선 사용합니다. 에러 처리 및 일관성을 위해 직접적인 호출(예: `fetch`)은 자제하고 표준 방식을 따릅니다.

---

## 6. Fallback / default — prefer explicit errors

**Avoid:** silent `value || 1234`, `config.timeout || 1000` for business rules.

**DTO exception:** Server payload builders may use required DTO shapes (e.g. `{ price }`) **only inside the builder**; do not propagate ambiguous objects into domain/UI/logs — use `orderPrice` / `tradePrice` / `currentPrice` etc. See `/verify-code-standards`.

**Internal keys:** `camelCase` for business logic, logs, UI models, JSON you own.

**Prefer:**

```javascript
if (!requiredValue) {
    throw new Error('Required value missing');
}
```

```bash
rg -n "\|\|\s*['\"]?[0-9A-Za-z_]+" static/js
```

### 6.1. Data Integrity Deep Guard (크래시 방지)

객체의 하위 속성을 참조할 때, 부모 객체가 존재하더라도 하위 속성이 `undefined`일 수 있음을 항상 가정해야 합니다.

**안티패턴 (TypeError 위험):**
```javascript
let roundDist = window.GridConfigManager?.CONSTANTS?.DEFAULT_ROUND_DISTRIBUTIONS?.standard[maxRounds];
if (!roundDist) {
    roundDist = window.GridConfigManager?.CONSTANTS?.DEFAULT_ROUND_DISTRIBUTIONS?.standard[40]; // 40회차도 없으면?
}
const start = roundDist.p1; // 💥 roundDist가 undefined이면 TypeError 발생
```

**권장 패턴 (Safe Fallback):**
```javascript
// 1단계: 1차 폴백
let roundDist = window.GridConfigManager?.CONSTANTS?.DEFAULT_ROUND_DISTRIBUTIONS?.standard[maxRounds] || 
                window.GridConfigManager?.CONSTANTS?.DEFAULT_ROUND_DISTRIBUTIONS?.standard[40];

// 2단계: 최종 하드코딩 가드 (시스템 크래시 차단)
if (!roundDist) {
    roundDist = { p1: 10, p2: 20, p3: 10 }; // 엔진 규격에 맞는 최소한의 구조 보장
    window.logMgr_ModuleLog(module, '데이터 정의 누락으로 하드코딩된 기본 분배를 사용합니다.', 'error');
}
const start = roundDist.p1; // ✅ 안전
```

---

## 7. Constants instead of magic numbers

```javascript
const MAX_RETRY = 3;
const TIMEOUT_MS = 1000;
```

---

## 8. Operating System Abstraction

플랫폼별(Windows/Linux 등) 분기가 필요한 경우, 직접적인 OS 확인보다는 프로젝트의 추상화 계층을 사용합니다.

---

## 9. After-Write Gate — "완료" 선언 전 필수 통과

**규칙:** 코드 블록을 작성한 직후, 응답으로 "완료"·"수정했습니다" 등을 출력하기 **전에** 아래 5가지를 순서대로 확인한다. 하나라도 해당하면 **즉시 수정** 후 재확인.

### A. 중복 변수 / 중복 참조
같은 참조를 다른 이름으로 선언한 쌍이 없는가?
```bash
# 예: const gDef = X; const globalDef = X; → globalDef 제거
rg -n "const \w+ = window\.GridConfigManager" static/js/ui/grid
```

### B. 중복 보정·검증 로직
같은 필드에 대해 동일한 보정·검증이 두 군데 이상 있는가?
- 수집(collect) 단계에서 보정했다면 렌더(render) 단계에서 같은 보정 반복 → 나중 것 제거
- 동일 함수 내 `if (x <= 0) { x = default; }` 패턴이 두 번 등장 → 하나 제거

### C. Deep Guard 완전성 (`§6.1` 패턴 적용)
`if (!x) { x = fallback; }` 이후에 `x.prop`를 접근하는 코드가 있는가?
- **fallback도 undefined일 수 있으면** → 최종 하드코딩 가드(`x = { prop: hardcodedValue }`) 필수
- 예: `roundDist = standard[40]` 이후 `roundDist.p1` 접근 → standard[40]도 없으면 크래시

### D. 로그 메시지 단계 정확성
로그 메시지가 **현재 실행 단계**를 정확히 설명하는가?
- collect 함수 안에서 "렌더링 시점에 다시 시도됩니다" → **금지**
- render 함수 안에서 "저장 후 확인하세요" → **금지**
- 단계 단어 예: `[Render]`, `[Collect]`, `[Save]`, `[Update]`

### E. 실제 데이터 에러 가시성

중요한 비즈니스 로직 처리 시:
- 에러·경고가 단순히 로그로만 남지 않고 사용자나 관리자가 인지할 수 있도록 처리한다.
- 불분명한 보정보다는 명시적인 에러 처리를 우선한다.

---

```bash
# 글로벌 스윕 (compat/legacy/wrapper 잔재)
rg -n "compat|legacy|wrapper|deprecated|alias" static/js
# 암묵적 || 기본값 (business logic에서 금지)
rg -n "\|\|\s*['\"]?[0-9A-Za-z_]+" static/js
```

After the gate: run **only** the **writing** skills you touched (logging, jsdoc, module, html) and **optional** domain verify from §3 if applicable.

---

---

## 12. Automated tests (`tests/`)

**필수(위치):** **신규 테스트 코드는 반드시 저장소 루트 `tests/` 디렉터리(및 그 하위)에만 작성한다.** 프로젝트 루트·`static/`·`routes/` 등 다른 경로에 `test_*`·`*_test.*`·검증 전용 스크립트를 두지 않는다.

**필수(서브폴더·신규 추가):** **새로 테스트 묶음을 추가할 때는** `tests/<역할요약>_YYMMDD/` **서브폴더를 새로 만들고**, 스크립트·픽스처·보조 파일은 **그 폴더 안에만** 둔다. `YYMMDD`는 **생성(추가)일** 6자리(`document-authoring`의 날짜 접미와 동일 규칙). 예: `grid_boot_recovery_260404/`, `upbit_adapter_fee_260404/`. 기존에 이미 루트나 고정 하위(`unit/` 등)에 있는 자산을 **확장**할 때만 그 구조를 따른다.

**저장소 루트의 `tests/`** 는 **실행 가능한 검증·회귀·시뮬 스크립트**의 기본 위치다. 로그 분석으로만 증명하기 어렵거나, `/verify-implementation`·도메인 `verify-*`와 별도로 **재현 가능한 자동 체크**를 두고 싶을 때 여기에 둔다.

| 규칙 | 내용 |
|------|------|
| **위치** | 과제(저장소) 루트의 **`tests/`** — `static/`·`routes/`·프로젝트 루트에 임시 `test_*.js`·`verify_*.py` 를 흩뿌리지 말 것 |
| **신규 서브폴더** | **`tests/<이름>_YYMMDD/`** 를 만들고 그 안에서 작업(위 **필수(서브폴더)** 참고) |
| **언제** | 수정 후 회귀 방지, 버그 재현 축소, 그리드/주문 로직 **시뮬·단위** 확인, 검토·일괄 수정 전후 **동일 스크립트로 비교** |
| **이름·구조** | **신규:** 위 날짜 접미 서브폴더 우선. **기존 트리**(`verify_*.py` 루트, `unit/`, `execute_buy_test/` 등)는 유지·같은 배치 내 확장 시 기존 패턴을 따른다. 파일명은 `verify_*.py`, `*_test.js` 등 기존 관례에 맞출 것 |
| **문서화** | `docs/debugging_notes.md` 의 **`test`** 필드에 실행한 명령(예: `node tests/run_grid_tests_node.js`, `python tests/my_feature_260404/run_checks.py`)을 남긴다 |

**러너:** 저장소 전체 일괄 실행용 `tests/run_*.js` 등 **공용 엔트리**는 루트 `tests/` 에 둘 수 있다. **새 시나리오 전용 코드**는 원칙적으로 **`tests/<name>_YYMMDD/`** 안에 두고, 필요하면 루트 러너가 해당 폴더를 호출한다.

---

## 13. Related project rules

- `CLAUDE.md` — no wrappers, no silent fallbacks, approval workflow, debugging notes
- **`/document-authoring`** — `docs/` 하위 폴더(plan/review/…)·신규 파일명 **`_YYMMDD.md`** — 프로젝트 설계/리뷰 **문서** (실행 스크립트는 위 §12 `tests/`)
- `debug-log-analysis` / `SKILL.md` **Core heuristics** — duplicate event/callback handling

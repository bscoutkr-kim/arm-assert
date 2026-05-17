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
| `/logging-standards` | Adding or changing JS logs (`window.logMgr_ModuleLog`) |
| `/jsdoc-standards` | New/changed public JS API |
| `/module-registration` | New global module / IIFE registration |
| `/html-registration` | New `static/js` file loaded in dashboard |
| `/refactoring-safety` | Large moves/splits (copy → verify → delete) |

These are **authoring** skills, not post-hoc test suites.

### 2.1 표준 로그 (`logMgr_ModuleLog`)

**적용:** `static/js`에서 **새로 추가**하거나 **의미 있게 변경**하는 모든 `window.logMgr_ModuleLog` 호출. (오타·레벨만 바꾸는 등 동작·문맥이 동일한 1줄 수정은 팀 재량으로 생략 가능.)

**원칙**

1. **`/logging-standards`** 전반을 따른다: `MODULE_NAME`, 로그 레벨, 금액·가격은 **`marketUtils_FormatPriceWithDecimal`** + **`market_getCurrencyInfo`** (`logging-standards/reference.md` §4), Analysis-Ready 패턴(`logging-standards/reference.md` §11), 고빈도 구간 §13.
2. **분석 가능한 한 줄** — 주문·체결·스킵·복구 등 비즈니스 이벤트에는 종목 식별(코드 또는 `[표시명]`), 필요 시 **라운드**(`R1` 등), **`orderId`**, 상태 전이 맥락을 넣는다. **식별자 없이 감상만 있는 로그**는 지양한다.
3. **구조 권장** — 동일 파일에서는 `|` 또는 `key=value` 조각으로 `grep`/스크립트 필터가 쉽게 하되, 기존 모듈 관례와 충돌하면 해당 파일 스타일을 우선한다.
4. **텔레그램** (`sendTelegramMessageOnly`, HTML 알림 등) 문구와 **동일할 필요 없음** — 로그는 세션·원장 분석 우선.

**분석 측:** 과거 세션 로그와의 혼용은 **`/log-analysis-workflow`** `reference.md` §1.4.

---

### 2.5 알고리즘 UI ↔ 트레이딩 엔진 SSOT (**분리 구현 금지 · 매우 강함**)

**원칙:** 자동매매·분석 **알고리즘과 연결된 모든 UI 구성**(모달·패널·테이블·배지·진행 문구 등)은 **화면만의 규칙으로 “통과/탈락/후보”를 결정하면 안 된다.** 그렇게 하면 사용자에게 **엔진이 실제로 하지 않는 행위를 보여 주는 연출**이 되어 **기능적으로 무의미**하며, 신뢰를 깨뜨린다.

**필수:**

1. **단일 진실 공급원** — 매매 의미가 있는 표시는 해당 알고리즘의 **공식 경로**만 호출한다.  
   - 예: AI 능동 후보 게이트는 엔진의 **`snapshot.evaluateStockAgainstScanGate(stock, engine)`** 와 동일 분기만 사용한다. 이벤트 밖 보조 호출은 **`evaluateScanGateForUi`** (`ai-active-trading` reference §0.A).  
   - **진행 탭 등 후보 행 목록**은 **`snapshot.getAiUnifiedCandidateStocksForUi(engine)`** / 정적 **`AICommonMarketSnapshot.getAiUnifiedCandidateStocksForUi()`** 로 통일한다. **후보 스캔 모달**은 **`autoTrade_AiScan_*`** 로 엔진이 **`getCandidateList()`** 순회·게이트 결과를 중계한 것만 표시한다. 진행 탭과 모달이 **`autoTrade_RisingStocks_Refreshed`의 raw `detail.stocks`** 나 코어 Var 조합만으로 **서로 다른 풀·판정**을 만들면 **표류(FAIL)** (`verify-implementation` Step 2.A).  
   - 그리드 실행 화면은 **`gridConfigManager` / `auto_trade_grid_viewmodel`** 계약 준수(**§10**).
2. **금지** — UI 파일에서만 `autoTradeCore_Var_Portfolio`·`Var_TradingCandidates`·예외 맵 등을 조합해 **엔진의 `scanAndEvaluate`/`getCandidateList`/`handlePriceUpdate`와 다른 판정**을 새로 만드는 것.
3. **계획·리뷰** — 새 UI나 필터 시각화를 추가할 때 **“어떤 엔진 메서드/스냅샷 API와 1:1인가”**를 먼저 명시하지 않으면 구현하지 않는다.
4. **1:1 매핑 표 (리뷰·검증)** — 매매 의미가 있는 각 UI 요소마다 **SSOT 한 줄**(공식 API·엔진 상태·문서화 필드)을 붙일 수 있어야 한다. PR/검증 시 **`verify-implementation` Step 2.A**의 표 형식을 따른다. 식별자 문자열 동일 여부가 아니라 **출처·의미 일치**가 기준이다.

**검증:** `/verify-implementation` Step 2의 **알고리즘 UI 표류 검사**(표 매핑 포함) 및 도메인 스킬과 교차한다.

---

### 2.6 Graphify — 작성 전 구조 참고 (**필수, 앱 소스 수정 시**)

**역할:** `rg`는 심볼·문자열, **Graphify는 모듈 묶음·허브·진입점** — `/implementation-plan`과 동일하게 **첫 파일 수정 전**에 수행한다. Graphify는 AST·추론 엣지를 포함하므로 **`verify-*`·`rg`를 대체하지 않는다.**

**필수 (앱 소스: `static/`·`routes/`·`templates/`·`mystock_web.py` 등):**

1. `graphify-out/GRAPH_REPORT.md` — 상단 **리포트 날짜**, **God Nodes**, 요청·수정 대상 키워드로 찾은 **Community 1~3개** (통독 불필요).
2. 리포트가 **리포트 날짜가 현재 날짜와 다르거나(stale)**, 또는 HEAD와 어긋나면 저장소 루트에서 **`graphify update .`** 후 재확인 (PATH CLI; `npx graphify` 금지).
3. 완료 보고 **`Graphify Evidence`** (`§9.F`) — **허브 또는 Community 이름 최소 1개**, 없으면 허용 예외만.

**`해당 없음(사유)` 허용 예외** (`/implementation-plan`과 동일):

- `.agent/`·`docs/`·스킬·주석만 변경
- 단일 파일·약 10행 이내·동작 불변(오타 등)

---

### 2.7. UX 공백 방지 및 반응형 UI (**필수**)

1. **에러 vs 빈 데이터 구분**: 
    - API 호출 실패(`catch`) 시와 성공했으나 결과가 없는 경우(`length === 0`)의 메시지를 반드시 분리한다.
    - 사용자에게 "내가 데이터가 없는 것인지 시스템이 고장난 것인지"를 명확히 알린다.
2. **종속 상태 변경 시 즉시 갱신 (Reactive UI)**: 
    - 모달 등에서 상위 설정(예: 알고리즘, 시장 타입)이 변경되면, 이에 영향을 받는 하위 UI(예: 예외 주식 목록, 관련 옵션)를 즉시 재계산하거나 갱신 트리거를 호출한다.
    - 저장 전 과도기 상태(`Transient State`)를 처리할 수 있도록 함수가 인자(예: `options.algorithm`)를 받을 수 있게 설계한다.
3. **로딩 가시성**: 
    - 비동기 작업 시 사용자에게 로딩 중임을 알리거나 최소한의 자리 표시자(Placeholder)를 제공한다.

---

## 3. Domain Reference & Manager Audit (작성 전 참고 및 관리자 검증)

수정할 파일이 아래 영역에 해당하면, **코드 작성 전**에 해당 스킬의 **`SKILL.md` 및 `reference.md`**를 읽고 설계 의도를 분석한다. 이는 오류를 사전에 방지하기 위한 **Authoring Reference**이다.

**실제 검증(Verify)**은 **Antigravity Manager(`GEMINI.md`)**가 `code-writing-guard` 발동 시 자동으로 관련 스킬을 병렬 실행하여 수행한다.

| Area | Skill | Typical paths |
|------|--------|----------------|
| Orders / Grid Lifecycle | `verify-grid-order-lifecycle` | `gridExec*.js`, `order_manager.js` |
| Grid math/state | `verify-grid-algorithm` | `grid*.js` |
| Settings UI/cache | `verify-settings-consistency` | `settings_manager.js`, `gridConfigManager.js` |
| Grid running / progress | `verify-grid-viewmodel` | `auto_trade_grid_viewmodel.js` |

---

## 4. Search before implement (`rg`)

```bash
rg -n "grid" static/js
rg -n "order manager|OrderManager" static/js
rg -n "calculateBuyTargets|reconcile|settingsCache" static/js
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

## 5.5. Browser HTTP to Flask (`api_fetchAPIData`)

**Default:** 대시보드(브라우저)에서 동일 오리진 백엔드(`/api/...`)를 호출할 때는 **`window.api_fetchAPIData`** (`static/js/utils/api_client.js`)를 씁니다. `marketType`/`X-Market-Type`, 해외 KIS 시 쿼리·헤더 보강, **localhost → 127.0.0.1 1회 재시도**, JSON 파싱·에러 객체 일관 처리가 한곳에 모여 있습니다.

**Exceptions:** **`fetch` 직접 사용**은 **주석으로 이유**를 남긴 경우만 허용합니다. 저장소에 이미 있는 예: `settings_manager.js` — 응답이 `api_fetchAPIData`가 가정하는 JSON 형태와 다를 수 있는 경로.

**그리드·복구·대사:** `gridBootRecoveryHandler.js`, `gridReconcile.js` 등 엔진/복구 코드도 예외가 아니면 **`api_fetchAPIData`**로 통일합니다 (`verify-boot-recovery`, `verify-grid-algorithm`과 함께 참고).

```bash
rg -n "\bfetch\s*\(" static/js/core/algorithms/grid
```

---

## 5.6. Exchange provider & market mode (SSOT)

**브로커(연결 주체)** 와 **시장 슬라이스(crypto / domestic / overseas)** 를 코드 곳곳에서 임의 문자열로 비교하면 복구·대사·주문 파라미터가 어긋납니다. 아래를 **표준**으로 쓰고, 새 분기는 여기서 파생합니다.

| 구분 | 표준 | 비고 |
|------|------|------|
| 현재 브로커 코드 | `window.setMgr_settingsCache.exchangeProvider` | 정규화: **`.toUpperCase()`**. 설정기준 허용 값 예: `UPBIT`, `KIS`, `KIWOOM` (`settings_manager.js` `validProviders`와 동일 계열). |
| 업비트(코인) 여부 | `window.api_isCrypto()` | 구현부: `api_client.js` — `exchangeProvider === 'UPBIT'`(대소문자 무시). |
| 설정 객체만 있을 때 | `window.api_isCryptoFromSettings(settings)` | `settings.exchangeProvider`만 사용; **`settings.provider`와 혼용하지 않음** (레거시 필드가 남아 있어도 신규 코드는 `exchangeProvider`). |
| 앱 전역 시장 타입 | `window.api_getMarketType()` | `setMgr_settingsCache.marketType` → `'crypto' \| 'domestic' \| 'overseas'` (`api_client.js`). |
| 종목/그리드 행 단위 | `gridSetting.marketType` 우선, 없으면 `window.market_getMarketType(gridSetting.marketType)` 등 | API 쿼리(`marketType=`)·헤더는 **`api_fetchAPIData`**가 캐시 기준으로 보강; 종목별 값이 있으면 그리드 설정을 먼저 본다. |

**금지·주의**

- `marketType === 'UPBIT'` 또는 `marketType === 'KIS'` 같이 **시장 타입 자리에 브로커 이름을 넣는 식**의 분기(의미 혼동).
- `window.api_isCrypto?.() ?? true` 같이 **코인 쪽을 기본값으로 두는 기본 인자** — 함수 미탑재/실패 시 주식 모드가 코인 규칙으로 처리될 수 있음. **`api_isCrypto() === true` 형태** 또는 `typeof window.api_isCrypto === 'function' && window.api_isCrypto()`처럼 **명시적으로** 처리.
- 동일 로직에서 `exchangeProvider` / `provider` / 임의 키를 **파일마다 다르게** 읽지 않기.

```bash
rg -n "exchangeProvider|api_isCrypto|api_getMarketType|market_getMarketType" static/js/core/algorithms/grid
rg -n "\.provider\b" static/js/core/algorithms/grid
```

**복구·부트:** `verify-boot-recovery` `reference.md`의 파이프라인 절과 함께 적용.

### 5.6.1. 복구 시점에서 표준 API·프로바이더가 성립하는 전제

그리드 부트 복구(`GridBootRecovery.bootRecoveryProcessHandler`)는 **대시보드 초기화 이후** `dashBoard_AutoTrade_Start` → `autoTradeCore_Register_Events` → `analysisAlgorithmEngine.recover('grid')` 경로에서 호출되는 것이 정상이다 (`dashboard.js`, `auto_trade_core.js`).

| 전제 | 이유 |
|------|------|
| `window.setMgr_settingsCache` 존재 | `api_fetchAPIData`가 캐시의 `marketType`/`exchangeProvider`로 헤더·KIS 해외 쿼리를 보강하고, `api_isCrypto`·`api_normalizeSymbol`이 업비트 심볼(`KRW-`)을 올바르게 처리한다. 캐시가 비면 기본값이 **주식(domestic) 쪽**으로 기울어 코인/해외 요청이 어긋날 수 있다. |
| `window.api_fetchAPIData` 로드됨 | `api_client.js`가 대시보드 번들에서 먼저 로드되어야 한다. |

**코드 가드:** `gridBootRecoveryHandler.js` `Step0_1_Initialize`에서 위 둘이 없으면 복구를 **즉시 중단**하고 체크포인트를 남긴다(비정상 진입·테스트 누락 조기 발견).

**캐시는 있으나 필드만 비어 있는 경우**는 서버/설정 저장 이슈에 가깝다. 특정 API 호출만 캐시보다 신뢰할 `marketType`/`provider`가 있으면 `api_fetchAPIData(url, { marketType, provider, … })`로 **명시 전달**할 수 있다(`api_client.js` 주석: 부팅 초기 캐시 미로드 대응).

**테스트/노드:** `setMgr_settingsCache`·`api_fetchAPIData`를 모킹하지 않으면 위 가드 또는 잘못된 분기에 걸린다. 복구 통합 테스트는 캐시 스냅샷을 맞출 것.

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
const MAX_GRID_RETRY = 3;
const RETRY_DELAY_MS = 200;
```

```bash
rg -n "MAX_|RETRY" static/js
rg -n "URL|PATH|ENDPOINT" .
```

---

## 8. Python: no raw OS checks in app paths

**Forbidden in scattered code:**

```python
if sys.platform == "win32":
if platform.system() == "Windows":
```

**Use** platform abstraction (e.g. `path_utils` / project pattern):

```python
from routes.standard.path_utils_impl import get_path_utils_impl
result = get_path_utils_impl().method_name(args)
```

```bash
rg -n "sys\.platform|platform\.system\(\)" routes/ utils/ mystock_web.py --glob "*.py"
```

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

### E. 실제 데이터 에러 가시성 (`hasStock` / 유효 데이터 경로)
`hasStock === true` 또는 실제 종목이 있는 슬롯의 처리 경로에서:
- 에러·경고가 `logMgr_ModuleLog` warn/error로만 끝나는가? → 필요 시 UI 알림도 고려
- 완전히 조용히 보정(`silentCorrection`)되고 있는가? → CLAUDE.md §2 위반

### F. UX 정교화 및 반응성 (§2.7)
- 에러 상황과 빈 데이터 상황이 UI에서 구분되는가?
- 상위 설정 변경 시 하위 UI가 즉시 반응(Reactive)하는가?
- 저장 전 과도기 상태(Transient Value)가 로직에 반영되었는가?

### G. Graphify (§2.6) 및 `.cursor/rules/graphify.mdc`

**워크스페이스 룰(`graphify.mdc`, `alwaysApply`)과 동일 목표를 스킬로도 정리한다.** 상세 워크플로는 **`/graphify`** (`.agent/skills/graphify/SKILL.md`).

1. **앱 소스 수정·구현 계획 수립 전 (필수 READ)** — `static/`·`routes/`·`templates/`·`mystock_web.py` 등을 **첫 수정하기 전**, `graphify-out/GRAPH_REPORT.md`에서 God Nodes·관련 Community를 확인한다(`§2.6`). 아키텍처 질문만이 아니라 **버그 수정·리팩터·기능 구현**에도 동일. `graphify-out/wiki/index.md`가 있으면 스킬 문서대로 우선 탐색.
2. **앱 소스 의미 변경 후 (필수 UPDATE)** — 이번 세션에서 위 경로를 수정한 경우 **저장소 루트**에서 **PATH `graphify` CLI**로 **`graphify update .`** (Windows: `$env:PYTHONUTF8='1'` 권장 — cp949 Tip 출력 오류 방지). **`npx graphify update .` 금지**. **순수 스킬/md/주석만** 바꾼 턴은 update 생략 가능.
3. **CLI 미설치·오프라인·사용자 거부** 등 — `manage-skills` **`reference.md` §0.4.1** `📋 적용 룰:`에 사유 기록.
4. **증적(필수, gate)** — 아래 3행을 완료 보고에 반드시 남긴다. **`활용 근거`에 God Node 또는 Community 이름이 없고** 허용 예외도 아니면 **미통과**.

```markdown
Graphify Evidence
- GRAPH_REPORT 확인: [YYYY-MM-DD — 선행 Read / stale 후 update·재확인 / 미확인(사유)]
- 활용 근거: [**God Node 또는 Community 이름 최소 1개** — 예: Community 7, `GridSettingsUI` / 허용 예외만 해당 없음(사유)]
- graphify update .: [실행 완료 / 해당 없음(스킬·문서만) / 미실행(사유)]
```

After the gate: run **only** the **writing** skills you touched (logging, jsdoc, module, html) and **optional** domain verify from §3 if applicable; **§9.F**에 해당하면 **`/graphify`** 절차(또는 불가 사유 기록)까지 마친 뒤 완료를 선언한다.

```bash
# 글로벌 스윕 (compat/legacy/wrapper 잔재)
rg -n "compat|legacy|wrapper|deprecated|alias" static/js
# 암묵적 || 기본값 (business logic에서 금지)
rg -n "\|\|\s*['\"]?[0-9A-Za-z_]+" static/js
```

---

## 10. Grid UI: `GridConfigManager` (표시·설정) vs ViewModel (진행)

**Do not mix these two data paths** when adding or wiring grid UI.

| Concern | Source of truth / entry | Consumed by |
|--------|-------------------------|-------------|
| **표시 방법·그리드 관련 설정** (어떻게 보일지, 알고리즘/표시 옵션) | **`static/js/core/algorithms/grid/gridConfigManager.js`** — 설정 UI·저장·엔진과 맞춘 SSOT | 설정 모달, collect, 알고리즘 초기화 |
| **진행(실행) 화면 데이터** (실시간/스냅샷) | **`static/js/ui/grid/auto_trade_grid_viewmodel.js`** — 엔진 출력을 조립한 ViewModel | **`auto_trade_running_grid_ui.js`** 등 실행 중 그리드 UI |

**Authoring rules**

- New **settings or display-behavior** fields: extend **`GridConfigManager`** (and settings pipeline); do not push domain rules into ViewModel.
- New **running-row / progress** fields: add to **ViewModel** snapshots; UI reads **`viewModel`** only — see **`verify-grid-viewmodel`**.
- **가격 기준 통일**: 그리드 UI·DGO 평가 기준은 체결가(`currentPrice`)보다 오더북 매수 1호가(`msgMgr_orderbookCache`의 `bid_price|bid`)를 우선 사용한다. 단, 실제 매수 주문 진입은 대기열 진입을 줄이기 위해 매도 1호가(`ask_price|ask`)가 타점 이하일 때만 오더북 트리거로 본다.
- **DGO 비교 연산자 주의**: DGO(`dynamicGapOverride`) 또는 동적 조정 로직 작성 시, 비교 연산자는 반드시 **`===`**를 사용하여 단일 라운드 격리(Round Isolation)를 보장해야 한다. `roundIndex >= startIdx`와 같이 범위를 후속으로 넓히는 방식은 전염 버그를 유발하는 금지 패턴이다. (2026-04-06 v2.5 확정)
- Quick scan:

```bash
rg -n "GridConfigManager|gridConfigManager" static/js/core/algorithms/grid/gridConfigManager.js static/js/ui/
rg -n "buildStaticSnapshot|buildRealtimeSnapshot" static/js/ui/grid/auto_trade_grid_viewmodel.js
```

---

## 11. Runtime paths — config, logs, `stockInfo`, grid trade logs

**SSOT for path helpers:** `routes/standard/path_utils.py` (`get_logs_path`, `get_config_path`, `get_settings_file_path`, `get_provider_base_path`).  
**Unified data root (typical):** `~/auto-trading-test-config/{PROVIDER_ID}/` — `PROVIDER_ID` from CLI (`--upbit`, `--kis`, …) / `path_utils.PROVIDER_ID`.

| What | Path pattern (under provider base unless noted) | Code / API |
|------|-----------------------------------------------|------------|
| **매매 설정 JSON** | `{config}/auto_trade_settings.json` | `get_settings_file_path()` |
| **로그 베이스** | `{logs}/` | `get_logs_path()` |
| **일별 통합 거래 로그** | `{logs}/trade_logs_YYYY-MM-DD.json` | `routes/logging_utils.py` — `/api/trade_logs`, `save_trade_log` |
| **그리드 종목별 거래 로그** (매수·매도 등 배열 JSON) | `{logs}/grid_trade_logs/grid_{SAFE_STOCK}.json` (성공), `grid_{SAFE_STOCK}_canceled.json` (취소). `SAFE` = 종목코드 정규화 (`/`→`_`, `-`→`_`, upper) | `logging_utils` — `/api/grid_trade_logs/<stock_code>` |
| **`stockInfo` 영속 + 백업** | `{logs}/stock_info/stock_info_{SAFE}.json`; 백업 `{logs}/stock_info/backup/stock_info_{SAFE}_yyMMdd_HHMMSS.json` (종목당 최대 30개 롤링) | `routes/api_utils.py` — `save_stock_info`, `get_stock_info` |
| **세션 로그** (당일 `api.log` / `frontend.log`) | `{logs}/yy-mm-dd_HH-MM-SS/` | `logging_utils.get_or_create_session_dir()` |

**디버깅:** 세부 로그 분석 워크플로는 **`/debug-log-analysis`**, **`/log-analysis-workflow`** — `trade_logs`·세션 폴더 우선.

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
---

## 14. 종목 코드 정규화 (Ticker Normalization) — SSOT 의무

업비트(KRW-BTC), KIS(005930), 해외(TSLA) 등 시장마다 종목 코드의 포맷이 다르며, 특히 암호화폐는 `BTC`와 `KRW-BTC`가 혼용되어 데이터 불일치(Data Mismatch)를 유발하기 쉽습니다. 이를 방지하기 위해 아래 규칙을 **의무적**으로 적용합니다.

### 14.1 JS 표준: `api_normalizeSymbol`
- **사용 지점**:
    - `Array.includes()`로 예외 목록을 검사할 때
    - `Map.get()` 또는 `Map.has()`로 종목 데이터를 조회할 때
    - 서로 다른 소스에서 온 두 종목 코드를 비교(`===`)할 때
- **권장 패턴**:
```javascript
// [Bad] 정규화 없이 비교 (BTC vs KRW-BTC 매칭 실패 위험)
if (exceptionList.includes(stockCode)) return true;

// [Good] 입력값과 목록 아이템을 모두 정규화하여 비교
const key = window.api_normalizeSymbol(stockCode);
const isException = exceptionList.some(item => window.api_normalizeSymbol(item) === key);
```

### 14.2 가드 포인트 (After-Write Gate)
- 코드 수정 후, 종목 코드를 다루는 모든 로직에서 "이 코드가 정규화된 키인가?"를 스스로 질문한다.
- 특히 `market_utils.js` 등 공용 유틸리티를 수정할 때는 정규화가 누락되지 않았는지 2중으로 검사한다.
- 정규화되지 않은 키를 Map의 키로 사용할 경우, 나중에 데이터를 찾지 못하는 "유령 데이터"의 원인이 됨을 인지한다.

### 14.3 예외 종목(거래 제외) 판정 SSOT
- **단일 함수:** `market_utils.market_isExceptionStock` — UI·코어·AI 스냅샷·구독 필터가 별도 예외 배열을 파싱하지 않는다.
- **`analysisAlgorithm === 'grid'`:** 사용자 `exceptionStocks*`만 스킵; **`permanentDeniedStocks`는 계속 적용**. 표·검증: **`verify-settings-consistency/reference.md`** Exception stocks by algorithm.

---

# Logging Standards — Reference

Companion to `SKILL.md`. Examples, `rg` commands, tables, agent output template.

**Scope:** **Frontend JS** unless stated. **Python** uses the standard `logging` module — not `window.logMgr_*`.

---

## 1. Ban `console.*` (frontend)

**Forbidden:** `console.log`, `console.warn`, `console.error`, `console.info` in normal code.

**Detection:**

```bash
rg -n "console\.(log|warn|error|info)" static/js | grep -v "Module Registration" | grep -v "TODO" | grep -v "//.*console"
```

**Replace with** `window.logMgr_ModuleLog(moduleName, message, level)` — see §5.

**Example — wrong vs right:**

```javascript
// Wrong
console.log('Price:', price);

// Correct pattern (with price formatting — §4)
if (typeof window.logMgr_ModuleLog === 'function') {
    const currency = window.market_getCurrencyInfo
        ? window.market_getCurrencyInfo(config.marketType).currency
        : 'KRW';
    const priceStr = window.marketUtils_FormatPriceWithDecimal
        ? window.marketUtils_FormatPriceWithDecimal(price, currency)
        : String(price);
    window.logMgr_ModuleLog('ModuleName', `[${stockName}] 메시지: price=${priceStr}`, 'warn');
} else {
    console.warn(`[ModuleName][${stockName}] 메시지: price=${price}`);
}
```

Fallback `console` only when `logMgr_ModuleLog` is missing — see **Exceptions** §8.

---

## 2. `logMgr_ModuleLog` signature

```javascript
window.logMgr_ModuleLog(moduleName, message, level);
```

| Parameter | Type | Notes |
|-----------|------|--------|
| `moduleName` | string | Prefer **`MODULE_NAME`** constant matching the file/module |
| `message` | string | Include formatted prices/amounts when logging money |
| `level` | string | `'info'` \| `'warn'` \| `'error'` \| `'high'` \| `'debug'` |

```bash
rg -n "logMgr_ModuleLog" static/js | head -30
rg -n "marketUtils_FormatPriceWithDecimal" static/js
```

---

## 3. Log levels

| Level | Use |
|-------|-----|
| `info` | Normal informational |
| `warn` | Warnings (ignored data, validation failed, etc.) |
| `error` | Errors, unrecoverable issues |
| `high` | Important business events (fills, position changes) |
| `debug` | Verbose diagnostics |

---

## 4. Prices / amounts in messages

Use **`window.marketUtils_FormatPriceWithDecimal(price, currency)`** after resolving **`currency`** via **`window.market_getCurrencyInfo`** (or project equivalent).

**수익·손익 금액(차액)** 은 가격과 **같은 `currency`** 로 **`window.marketUtils_FormatCurrency(amount, currency)`** 를 쓴다. `…toLocaleString()}원` 처럼 통화를 하드코딩하지 않는다. (가격은 소수·자릿수 규칙이 있고, 통화 금액은 `FormatCurrency`가 KRW/USD 단위를 맞춘다.)

**`logMgr_SimpleLog`** 등 사용자에게 보이는 한 줄 메시지에서도 동일: 예) 그리드 체결 요약 `gridPendingOrderHandler.js` — `currencyInfo = market_getCurrencyInfo()` 후 금액·수익에 `marketUtils_FormatPriceForLog` / `marketUtils_FormatCurrency` 사용. 주문·체결 도메인 세부는 **`verify-order-execution`** Block C(통화 포맷 단락)와 맞출 것.

```javascript
// Wrong
window.logMgr_ModuleLog('ModuleName', `Price: ${price}`, 'info');

// Correct
const currency = window.market_getCurrencyInfo(marketType).currency;
const formattedPrice = window.marketUtils_FormatPriceWithDecimal(price, currency);
window.logMgr_ModuleLog('ModuleName', `Price: ${formattedPrice}`, 'info');
```

```javascript
// 수익 금액 예 (동일 currency)
const profitStr = window.marketUtils_FormatCurrency(Math.floor(profitAmt), currencyInfo.currency);
```

```bash
rg -n "logMgr_ModuleLog.*price\s*=" static/js | grep -v "FormatPriceWithDecimal"
```

---

## 5. Module name constants

```javascript
// Wrong — ad-hoc string casing
logMgr_ModuleLog('gridConfigManager', 'message', 'info');

// Correct
const MODULE_NAME = 'GridConfigManager';
// or static MODULE_NAME on class
window.logMgr_ModuleLog(MODULE_NAME, 'message', 'info');
```

```bash
rg -n "logMgr_ModuleLog\s*\(\s*['\"]" static/js | grep -v "MODULE_NAME"
```

(Heuristic — review manually.)

---

## 6. Full example (pattern)

```javascript
const MODULE_NAME = 'MyModule';

function logMessage(stockName, price, marketType) {
    if (typeof window.logMgr_ModuleLog !== 'function') {
        console.warn(`[${MODULE_NAME}] logMgr not available`);
        return;
    }

    const currency = window.market_getCurrencyInfo
        ? window.market_getCurrencyInfo(marketType).currency
        : 'KRW';
    const priceStr = window.marketUtils_FormatPriceWithDecimal
        ? window.marketUtils_FormatPriceWithDecimal(price, currency)
        : String(price);

    window.logMgr_ModuleLog(MODULE_NAME, `[${stockName}] Price updated: ${priceStr}`, 'info');
}
```

---

## 7. Detection commands (summary)

```bash
rg -n "console\.(log|warn|error|info)" static/js | grep -v "Module Registration"
rg -n "logMgr_ModuleLog" static/js
rg -n "marketUtils_FormatPriceWithDecimal" static/js
```

---

## 8. Exceptions (allowed `console`)

1. **Module registration** IIFE — registration banner at file end (project convention).
2. **Temporary debug** — with `// TODO: remove after debugging`.
3. **Fallback** — only if `typeof window.logMgr_ModuleLog !== 'function'` first (see §1 example).
4. **Python** — `logging` module, not this skill’s JS API.

---

## 9. Agent output template

```markdown
## Logging Standards Result

### Summary
- console.*: N violations / 0
- logMgr_ModuleLog: usage reviewed
- Price formatting: ok / gaps
- MODULE_NAME: ok / gaps

### Violations
| File | Line | Issue | Fix |
|------|------|-------|-----|
```

---

## 10. 거래 이벤트 텔레그램 메시지 스키마

`sendTelegramMessageOnly` 직접 호출 시 아래 포맷을 따른다.  
`[UPBIT]` / `[국내주식]` / `[해외주식]` 접두어는 `infoAlertsManager.sendTelegramMessageOnly`가 `marketType`으로 **자동 추가** — 본문에 거래맥락 중복 금지.

### 이모지 체계

| 이모지 | 유형 |
|--------|------|
| `▶️` | 시작 알림 |
| `📤` | 발주 알림 (주문 접수 완료) |
| `📈` | 매수 체결 알림 |
| `📉` | 매도 체결 알림 |
| `🚫` | 취소 / 정리 알림 |
| `🔄` | 부트 복구 요약 |

### 1행 포맷 (필수)

```
{이모지} [{종목명}] {유형} {라운드} | {수량}주 @ {가격}원
```

- **라운드**: `R1`, `R2` ... (Round: N 표기 금지)
- **구분자**: ` | ` (공백 포함 파이프)
- **가격**: `Number(price).toLocaleString()원` 또는 `marketUtils_FormatPriceWithDecimal`

### 부가줄 (선택)

```
└ 목표매도가 {가격}원 (+{수익률}%)
└ DGO 기본 {기본가}원 → {적용가}원
└ 사유: {reason}
└ ID: {orderId 앞 8자리}
```

### 유형별 예시

```
// 발주 (log_manager.js)
📤 [에이다] 매수 발주 R2 | 10주 @ 430원 | 사유: 진입 조건 충족
└ DGO 기본 450원 → 430원
└ ID: ABC12345

// 매수 체결 (gridPendingOrderHandler.js)
📈 [에이다] 매수 체결 R2 | 10주 @ 430원
└ 목표매도가 473원 (+10.00%)
└ DGO 기본 450원 → 430원

// 매도 체결 (gridPendingOrderHandler.js)
📉 [삼성전자] 매도 체결 R1 | 5주 @ 75,000원
└ 사유: 목표가 도달

// 취소 알림 (gridExecBuy/Sell, gridHandler, gridReconcile, gridBootRecoveryLoader)
🚫 [에이다] 미체결 매수 일괄 취소 — 신규 매수 전 | ID: ABC12345
🚫 [에이다] 장기 미체결 자동 취소 · 매도 | ID: ABC12345
```

- **참고:** 다건·임시 취소 ID를 붙일 때는 ` (ID: a, b)` 형태로 **1행 인라인**을 쓰는 호출부가 있다 (`gridExecBuy`/`gridExecSell` 등). 스키마의 `| ID:` 한 줄과 **혼용**될 수 있음 — 신규 코드는 가능하면 §10 한 줄 규칙에 맞출 것.

### 현행 유지 (포맷 적용 제외)

- `auto_trade_core.js` 시작 알림 — HTML bold 포함, 별도 포맷
- `gridBootRecoveryHandler.js` 복구 요약 — 멀티라인 트리 구조, 별도 포맷

---

## 11. Analysis-Ready Logging Patterns (New)

로깅 시 향후 로그만으로 원인 분석이 가능하도록 충분한 컨텍스트를 포함해야 합니다.

- **조건문 분기**: 특정 조건을 만족하지 않아 동작을 건너뛰는 경우(`if (!condition) return`), 반드시 **'Why'**와 **'Current State'**를 로그로 남깁니다.
  - 예: `[KRW-ADA] Skip buy (Reason: price too high, current: 430, target: 400)`
- **N/A 또는 초기 상태**: 데이터가 비어 있는 상태로 진입하거나 유지될 때 로그를 남깁니다.
  - 예: `[KRW-ADA] Initializing round R2 as N/A (Reason: no trade history found in local buffer)`
- **상태 전이**: 중요한 상태 변경(pending -> filled) 시 관련 ID(orderId)를 포함하여 타임라인 추적이 가능하게 합니다.
- **거래소 시각차 대응 (Upbit)**: 업비트 API는 `created_at`(주문 생성 시각)을 반환하며, 이는 실제 체결 시각과 수 시간 이상의 차이가 날 수 있습니다. 사용자 혼동 방지를 위해 타임스탬프 뒤에 **`[주문생성]`** 라벨을 명시합니다.
  - 예: `2026-04-03 21:30:11 [주문생성]`

## 12. Self-Analysis Audit (Must Check)

코드를 완료하기 전, 작성된 로그를 보며 다음 질문을 자문하십시오:
1. "이 로그만 보고 장애 발생 시 타임라인을 1초 단위로 재구성할 수 있는가?"
2. "특정 종목(symbol)의 로그만 필터링했을 때 전체 비즈니스 로직(판단 -> 주문 -> 체결 -> 반영)이 끊기지 않고 보이는가?"
3. "성공 로그를 제외했을 때(NoNoiseFilter 적용 시), 오류 상황이 명확히 드러나는가?"

---

## 13. High-Frequency & Loop Logging (Flooding Prevention)

반복문이나 고빈도 폴링 로직에서는 로그 홍수(Log Flood)를 방지해야 합니다.

### 13.1 상태 변화 시에만 로깅 (State-Change Only)
매번 출력하지 말고, 이전 값과 다를 때만 출력하십시오.
```javascript
// Good
if (this.lastState !== newState) {
    window.logMgr_ModuleLog(MODULE_NAME, `State changed: ${this.lastState} -> ${newState}`, 'info');
    this.lastState = newState;
}
```

### 13.2 고빈도 데이터는 `debug` 레벨 사용
1초 단위 시세 업데이트 등은 `'info'`가 아닌 `'debug'`를 사용하십시오.
```javascript
// Good
window.logMgr_ModuleLog(MODULE_NAME, `Current price: ${price}`, 'debug');
```

### 13.3 반복문 내 에러/경고 요약
루프 내부에서 수백 개의 로그를 남기는 대신, 결과를 취합하여 루프 종료 후 한 번만 남기십시오.

---

## 14. API 실패 로그, `Error` 객체, ErrorCollector (필수)

마지막 인자가 `'error'`인 `logMgr_ModuleLog` 호출은 `window.errorCollector`(및 소켓 경유 텔레그램 장애 알림)로 문자열이 전달됩니다.

- **`Error`를 그대로 넘기면** 과거 구현에서 `JSON.stringify` 경로를 탈 경우 **`{}`만 표시**될 수 있습니다. 앱 코드에서는 **`message`를 합친 단일 문자열**로 넘기거나, **`log_manager.js`**의 **`_logMgr_FormatErrorCollectorValue`** 규칙을 따릅니다.
- **`api_fetchAPIData`** 실패 시 권장 패턴: `static/js/utils/api_client.js` — **`[API 실패] … ${normalizedError}`** 한 줄 + `'error'` (Error 인스턴스를 별도 인자로 넘기지 않음).
- 텔레그램 전송 실패 **서버 측 진단**: `routes/telegram_service.py` `send_message`에서 HTTP 비-200 응답 본문 스니펫 로깅.

검증 체크리스트·`rg` 예시는 **`verify-log-standards` `reference.md` Step 7**을 따릅니다.

### 14.1 HTTP JSON 오류 응답 — **원인 반드시 포함** (Flask ↔ `api_client`)

**문제:** 백엔드가 업무 실패 시 사용자·텔레그램 장애 알림에 **고정 문구만** 남기면(예: "봇 상태를 확인하세요") 운영자는 원인을 추측해야 하고, 같은 유형의 패치를 반복하게 된다. **처음부터** 서버가 아는 실패 이유를 내려주어야 한다.

**필수:**

- **Flask `jsonify`:** 업무 실패(`success: false`, HTTP 4xx/5xx) 시 **`error`(사람이 읽는 요약)** 외에 **`detail`(구체 원인: 설정 누락, `enabled`, HTTP 코드, 외부 API `description`, 예외 문자열 등)** 을 함께 반환한다. **토큰 전체·비밀번호 등 민감 값은 넣지 않는다.**
- **구현 패턴:** 실패 분기에서 한 번만 설정 가능한 **직전 실패 사유**(예: 서비스 클래스의 `_last_*_failure_reason` + getter)를 두고, 라우트가 이를 JSON `detail`에 실어 보낸다.
- **`api_fetchAPIData` (`api_client.js`):** `!response.ok`이고 `data.error`가 있으면 **`data.detail`이 있으면 ` | ${data.detail}`** 로 최종 메시지에 병합한다(장애 알림 한 줄에 원인 가시).
- **`success: false` + HTTP 200** 응답을 쓰는 엔드포인트가 있으면, 그 본문에도 동일하게 **`detail`/`message`** 규칙을 적용한다(방어 분기는 §14 상단 · Step 7 유지).

**금지:** 서버가 이미 알고 있는 실패 이유를 클라이언트로 넘기지 않고 **진단 불가한 고정 문구만** 반환하는 것.

### 14.2 실패·경고·운영 알림 전반 — **원인 추적 가능한 맥락** (API만이 아님)

§14.1은 **HTTP JSON** 에 한정된다. 아래는 **프론트 `logMgr`**, **Python `logging`**, **텔레그램·장애 알림·사용자 메시지** 등 **실패를 기록하거나 운영자에게 보이는 모든 경로**에 공통으로 적용한다.

**대상 (필수에 가깝게 적용):**

- `logMgr_ModuleLog` 의 **`'error'` / `'warn'`** 로 남기는 **비즈니스 의미 있는 실패** (검증 실패, API 거절, 복구 실패, 상태 불일치 등).
- Python **`logger.error` / `logger.warning`** (또는 동등)으로 남기는 **요청·주문·외부 연동 실패**.
- **텔레그램·소켓 장애 알림·토스트 등** 사용자/운영자가 읽는 **오류 문구**.

**포함해야 하는 것 (가능한 범위에서, 민감값 제외):**

- **무엇이** 실패했는지(모듈·단계·엔드포인트·작업 이름).
- **왜** 인지 알 수 있으면: HTTP 상태, 외부 API `description` 요약, 예외 메시지 한 줄, 설정 플래그 이름(`enabled` 등) — **토큰·비밀번호·전체 키·개인정보는 넣지 않는다.**
- **어디서** 재현·대사할지: 종목/심볼, 주문·클라이언트 id(있을 때), 세션·요청 식별에 필요한 최소 필드.

**적용하지 않는 것 (기존 규칙과 충돌 시 이쪽 우선):**

- **고빈도 폴링·루프** — §13: 불필요한 스팸을 피하고 `'debug'`·요약 로그 사용.
- **정상 `info` 한 줄** — §2 Analysis-Ready와 동일하게, 실패가 아니면 “모든 글자에 스택”을 요구하지 않는다.

**금지:** “실패했습니다”, “오류”, “확인하세요” 같이 **고정 문구만** 남기고, 코드가 이미 알고 있는 **구체 원인·식별자**를 로그/알림에 넣지 않는 패턴.

검증: **`verify-log-standards` Step 7** · 본 절은 **`/code-writing-guard`** After-Write Gate(실패 경로 메시지)와 함께 본다.

---

## 15. Related files

| Path | Role |
|------|------|
| `static/js/utils/log_manager.js` | `logMgr_ModuleLog` implementation |
| `static/js/utils/api_client.js` | `api_fetchAPIData` 실패 문자열·`detail` 병합 (§14.1) |
| `static/js/utils/market_utils.js` | `marketUtils_FormatPriceWithDecimal` |
| `static/js/**/*.js` | Application logs |
| `routes/api_notification.py` 등 | 실패 시 `jsonify`에 `error` + `detail` (§14.1) |
| `routes/*.py` | Python `logging` |

# Graphify Reference

## 1. Graph Layout

- **Report**: [GRAPH_REPORT.md](file:///c:/Work/mystock_web/graphify-out/GRAPH_REPORT.md) — Summary of god nodes, hub nodes, and community structure.
- **JSON**: `graphify-out/graph.json` — The raw AST-link data.
- **HTML**: `graphify-out/graph.html` — Interactive visualization (if accessible; large graphs may be skipped by CLI).

## 2. Commands

### Update Graph
Run this after making changes to keep the graph current. It is AST-only and has no API cost.

- **Working directory**: repository root (`mystock_web/`).
- **Invocation**: the **`graphify` binary on PATH** — not `npx graphify`. The latter is not wired as a reliable package entry here and frequently fails in Cursor agent or Windows environments with `npm error could not determine executable to run`.

```powershell
# Windows PowerShell (recommended — avoids cp949 UnicodeEncodeError on final Tip line)
cd C:\Work\mystock_web
$env:PYTHONUTF8 = '1'
graphify update .
```

## 3. Read-Before-Plan / Read-Before-Write (필수)

**트리거:** 구현 계획, 버그 수정, 리팩터, 기능 구현, 코드 수정, `code-writing-guard`, `implementation-plan` — **앱 소스를 건드리기 전**.

**순서 (권장):**

1. `GRAPH_REPORT.md` — 리포트 날짜, **God Nodes**, 키워드로 찾은 **Community 1~3개** (통독 불필요).
2. **리포트 날짜가 현재 날짜와 다르거나(stale)**, 또는 HEAD와 어긋나면 **`graphify update .`** 후 재확인.
3. **`rg`** — Graphify로 좁힌 파일·심볼 안에서 패턴 검색.

**역할:** Graphify = 모듈 묶음·허브·진입점 / `rg` = 문자열·패턴 / `verify-*` = 도메인 계약 — **서로 대체하지 않음.**

**증적:** `/implementation-plan` → `Graphify Context` / `code-writing-guard` → `Graphify Evidence` (**허브 또는 Community 이름 최소 1개**).

**`해당 없음` 허용 예외** (계획·작성 스킬과 동일):

- `.agent/`·`docs/`·스킬·주석만
- 단일 파일·약 10행 이내·동작 불변

## 4. Post-Task Update (필수)

앱 소스(`static/`·`routes/`·`templates/`·`mystock_web.py` 등) **의미 변경 후** — 저장소 루트에서 **`graphify update .`**. 순수 스킬/md만 변경한 턴은 생략 가능.

## 5. Orchestration

- **Triggers:** "아키텍처", "구조 파악", "전체 흐름", "graphify", "구현 계획", "코드 수정", "버그 수정", "리팩터".
- **Chain (`manage-skills` §0.3):** `/graphify` READ → `/implementation-plan` → 작성 → `graphify update .`
- **MCP:** `query_graph` 등은 graphify MCP가 활성일 때만; 없으면 `GRAPH_REPORT.md` + `rg` on report path.

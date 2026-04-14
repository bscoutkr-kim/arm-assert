# Manage Skills — Reference

Companion to `SKILL.md`. **`§0` = skill-system admin (orchestration, triggers, 사용 스킬 ledger)** — single source of truth for all skill-related agent behavior. **`§1`–`§15`** = registry, maintenance workflow, domain sync (**`§8.1`**), paths. **`SKILL.md` ≤200-line check** (§11).

---

## 0. 스킬 오케스트레이션 (관리자 · 모든 턴)

**Authority:** 스킬 선택·자동 트리거 해석·교차 `Read`·응답 말미 **`📋 사용된 스킬`**·도메인 변경 시 `verify-*` 갱신 의무의 **단일 원본**은 본 절(**§0**)이다. `CLAUDE.md`는 프로젝트 전역 규칙과 **짧은 포인터**만 유지한다.

### 0.1 선행 절차 (pre-flight, 매 턴)

1. **의도 분류:** 코드 작성/수정, 리뷰·검증, 로그·원장 분석, 문서(`docs/`), 스킬 유지보수, 순수 Q&A, 기타.
2. **승인 여부 확인 (필수):** 이번 요청이 단순한 질문·설명이 아닌 **명시적인 승인(Approval)** 키워드(**"승인해", "진행해", "수정해줘", "내가 작업해"**)를 포함하는지 확인하십시오. 질문에 대한 답변("응", "맞아")이나 기술적 논의는 실행 권한을 부여하지 않습니다. 계획서(`implementation_plan.md`)가 승인된 후에만 변경을 시작하십시오.
3. **1차 스킬 매핑:** 아래 **§0.3** 자동 트리거와 표에 맞춰 **어떤** `.agent/skills/*/SKILL.md`·`reference.md`를 `Read`할지 결정. 애매하면 관련 스킬을 **넉넉히** 읽고 범위를 줄인다.
3. **연쇄 Read 계획:** 예) 코드 변경 → `/code-writing-guard` → (로그 변경 시) `/logging-standards` → (신규 모듈) `/module-registration`·`/html-registration` → (해당 도메인) **`verify-*`** (`reference.md` 위주). **진입 트리거 1개만 반영했다고 나머지 스킬을 생략하지 않는다.**
   - **코드 Read → 검증 스킬 발동(교차 Read, 필수):** 이번 턴에 워크스페이스 **코드를 `Read`·`rg` 등으로 검토·원인 분석·대조**하는 경우( diff/구현 여부와 무관), 검토한 경로를 **`§8.1`** 표와 대조해 해당 도메인의 **`verify-*/reference.md`를 반드시 `Read`**한다. 사용자가 “검증 실행”·`검증해줘`라고 하지 않아도 동일하다. 응답 말미 **`📋 사용된 스킬`**에 **`/해당-verify-* (직접 읽기)`**를 포함한다. **repo 파일을 열지 않은 순수 Q&A**만 예외다.
4. **알고리즘·도메인 변경 플래그:** 수정 대상이 **`§8.1`** 그리드·부트·주문·설정·텔레그램·앱 부트 등이면 **같은 작업 세션**에서 해당 `verify-*/reference.md` 갱신·`docs/debugging_notes.md`를 `CLAUDE.md`와 프로젝트 규칙에 맞게 처리할지 명시적으로 결정. 노트만 있고 스킬 미갱신이면 **미완료**.
5. **갭·지적:** 요청이나 diff가 어느 `verify-*`에도 안 맞으면 **UNCOVERED**로 표시하고, 사용자에게 **`§7`–`§9` (UPDATE vs CREATE)** 제안 또는 `manage-skills` 전용 세션을 권고한다. `CLAUDE.md` 스킬 표와 `.agent/skills/` 실제 목록이 어긋나면 **동기화가 필요**하다고 지적한다.

### 0.2 Skill 도구 실패 시 (필수)

- `Skill` 도구가 실패(`Unknown skill` 등)하면 **재시도하지 말고** 해당 스킬의 **`.agent/skills/<name>/SKILL.md`와 `reference.md`를 `Read`로 직접 읽는다.**
- `Read`로 반영했다면 응답 말미 **`/스킬명 (직접 읽기)`**로 반드시 적는다 (**§0.4**).

### 0.3 자동 트리거 (canonical)

- "계획서", "구현 계획", "계획을 작성", "계획서를 작성", "계획을 세워" 등 → **`/implementation-plan`**
- **코드 수정 전 계획 제시:** 수정 계획을 쓸 때도 **`/implementation-plan`** 형식을 따른다 (`CLAUDE.md` 규칙 5).
- "코드 수정", "수정해줘", "코드를 고쳐", "구현해줘", "코드 작성", "추가해줘", "변경해줘" 등 → **`/code-writing-guard`**
- 검토·리뷰 **결과를 구현**할 때: "위의 검토 내용을 반영해줘", "검토 내용 반영", "리뷰 반영", "검토 이슈 반영", "수정·개선 필요 반영", "피드백 반영" 및 `apply the review`, `implement the review feedback` 등 → **`/code-writing-guard`**
- "검증해줘", "검증 스킬", "검증 실행", "코드 검증", "전체 검증", "구현 검증" 등 → **`/verify-implementation`**
- 텔레그램 상태·원격 제어·`/status`·①②③ 핸드셰이프 검증 → **`/verify-telegram-remote-pipeline`** (호출 불가 시 `reference.md`만 `Read` 허용; 구명 `verify-telegram-status` 통합)
- Flask 서버 초기화·부트·`/ping` 검증 → **`/verify-app-initialization`** (동일)
- **로그·세션·원장 분석**(코드/diff/PR 리뷰가 아님): "로그 분석", "세션 로그", `trade_logs`, `frontend_key.log` 등 실제 로그·JSON → **`/log-analysis-workflow`**; 유령 주문·대사·Reconcile 심화 → **`/debug-log-analysis`** 병행·단독. 이 의도가 분명하면 "검토"가 있어도 **`/verify-implementation`보다 로그 스킬 우선**.
- 코드 리뷰·대조: "리뷰해줘", "검토해줘", "점검해줘", "PR 리뷰", `code review` 등 → **`/verify-implementation`** (단, 위 로그 항목이면 예외)
- "스킬 수정", "스킬 추가", "스킬 동기화", "스킬 관리", "manage-skills" 등 → **`/manage-skills`** (본 스킬; 유지보수 워크플로 전체)
- `docs/` 마크다운 작성·정리 → **`/document-authoring`** (신규 파일명 `*_YYMMDD.md`)

**권장 체인 (요약):**

```
새 코드 작성: /code-writing-guard → (로그) /logging-standards → (신규 API) /jsdoc-standards
            → (신규 모듈) /module-registration → /html-registration
            → (도메인) 해당 verify-* (SKILL.md·reference.md Read)
            → (선택) /verify-implementation
응답 말미:   §0.4 사용 스킬 전부 나열 (트리거 1개만 쓰지 말 것)
완료 시:     debugging_notes + §8.1 해당 시 verify-* reference 갱신 (세트)
로그·원장:   /log-analysis-workflow → /debug-log-analysis
```

### 0.4 응답 말미 — `📋 사용된 스킬` (필수)

- **모든 응답 마지막에 반드시** 사용 스킬을 명시 — 생략 불가.
- **진입 트리거 1개 ≠ 실제 사용 1개:** 자동 트리거로 **`/code-writing-guard`** 등 하나만 걸려도, 그 스킬·`reference.md` 절차에 따라 **`/logging-standards`**, 도메인 **`verify-*`**, **`/implementation-plan`** 등을 **같은 작업에서 `Read`하거나 반영했다면 전부** `사용된 스킬`에 나열한다 (대표 1개만 쓰고 나머지 생략 금지).
- 스킬을 사용한 경우 예시:

  `📋 사용된 스킬: /code-writing-guard, /logging-standards, /verify-boot-recovery (직접 읽기), /verify-implementation`

- **`Read`로 `.agent/skills/.../SKILL.md`·`reference.md`를 반영했다면** `없음`으로 끝내지 말고 **`/스킬명 (직접 읽기)`**를 **각각** 포함한다.
- **코드 검토 턴:** `Read`/`rg`로 **repo 파일**을 근거로 인용·분석했고, 그 경로가 **`§8.1`** 도메인에 해당하면 **`없음 — [조건 불일치]` 등으로 `verify-*`를 통째로 생략하는 것은 금지**다. 반드시 해당 **`verify-*/reference.md`를 `Read`**했는지 확인하고 **`/verify-… (직접 읽기)`**를 `📋 사용된 스킬`에 넣는다(다중 도메인이면 각각).
- 스킬을 사용하지 않은 경우(`없음`) — **반드시 이유 + 분류를 한 줄에** 명시한다:
  - **(i)** 프로젝트 스킬 목록에 맞는 스킬이 없음
  - **(ii)** 스킬은 있으나 이번 요청·트리거·범위와 맞지 않아 미적용 — 단, **§0.1 항목 3의 부목(코드 Read → verify-*)**에 해당하는 검토는 **(ii)로 `없음` 처리 불가**
  - **(iii)** Skill 도구 미제공·실패로 호출 불가였고 **`Read`도 안 했으면** 그 사실을 적는다 (`Read` 했으면 `(직접 읽기)`로 적는다)
  - 워크스페이스 파일을 열지 않은 **순수 Q&A**면 **`repo 파일 미검토`**를 명시

예시:

`📋 사용된 스킬: 없음 — [후보 스킬 없음] …`  
`📋 사용된 스킬: 없음 — [조건 불일치] …`  
`📋 사용된 스킬: 없음 — [repo 파일 미검토] …`

### 0.5 알고리즘·코드 변경 → 검증 스킬 추적

- 코드 변경이 **`§8.1.1`–`§8.1.9`** 어느 도메인에 해당하는지 **명시적으로 매핑**한다.
- 체크리스트·단계·`rg` 패턴이 낡았으면 **해당 `verify-*/reference.md`를 보강**한다. 신규 패턴이 반복되면 **`§7`–`§9`**에 따라 `verify-*` **신규 생성**을 사용자 확인 후 진행한다.
- **`verify-implementation`** 타깃 목록·`CLAUDE.md` Available Skills 표는 스킬 추가/삭제 시 **같은 세션에서 동기화** (`§9`).

### 0.6 본 절과 `CLAUDE.md`의 역할 분담

| 항목 | 위치 |
|------|------|
| 스킬 트리거·체인·사용 스킬 리스트·Skill 도구 실패 | **본 절 §0** (SSOT) |
| 커밋 금지, 계획 승인, 한글 응답, 호환 코드 금지 등 **비스킬** 규칙 | `CLAUDE.md` |
| 스킬 목록 표 (한 줄 설명) | `CLAUDE.md` — **`/manage-skills`가 동기화** (`§12`) |
| Cursor 에이전트에 **항상 적용**되는 짧은 강제 룰 (§0 선행·응답 말미 리스트) | `.cursor/rules/skill-orchestration.mdc` (`alwaysApply: true`) |

### 0.7 다른 스킬과의 독립성 (대체 불가)

- **`/code-writing-guard`를 지켰다고 해서 `/manage-skills` 의무가 면제·자동 충족된 것으로 보지 않는다.** §0 선행(의도·스킬 매핑·ledger)·§8.1·레지스트리·드리프트·유지보수 워크플로(§4–§11)는 **별도 축**이다.
- **역으로**, `/manage-skills` 또는 `verify-*` 문서만 맞췄다고 **앱 소스의 중복·래퍼 제거·Active Deletion**이 검증된 것이 **아니다** — 그 책임은 **`code-writing-guard`** 및 해당 도메인 **`verify-*`의 앱 코드 체크리스트**에 있다.
- **역할 분리:** `manage-skills` = **메타계층** (`.agent/skills/` 트리거 SSOT, 표·경로·`rg` 패턴 스테일, 갭 분석, `SKILL.md` 줄 수). `code-writing-guard` = **구현 계층** (저장소 내 JS/Python 품질 규칙). **검토 대상과 통과 조건이 다르며**, 한쪽이 다른 쪽을 “이미 했다”고 대체하지 않는다.
- 유지보수 세션에서 **§4–§11**은 diff·매핑·갭·동기화를 **항상 별도로 수행**한다. “코딩 스킬을 읽었다”는 이유로 이 단계를 **생략하지 않는다**.

---

## 1. Registered verification skills (project — update when adding/removing)

> **⚠️ 교차 Read 필수 (이름에 속지 말 것):** `verify-*` 스킬은 "검증 실행"·"검증해줘" 요청이 없어도,
> 아래 **Cover file pattern** 에 해당하는 파일을 `Read`·`rg` 등으로 **분석·원인 파악·대조한 모든 턴**에서
> 해당 스킬의 `reference.md`를 **교차 Read**해야 한다 (§0.1 항목 3).
> 이름이 "verify-"이라도 **도메인 지식 참조 스킬**이므로, `(ii) 조건 불일치`로 `없음` 처리하는 것은 규칙 위반이다.

| Skill | Description | Cover file pattern |
|-------|-------------|-------------------|
| `code-writing-guard` | 코드 작성 표준 — 중복 금지, 클린 코드 | `**/*.js`, `**/*.py`, `**/*.cpp`, `**/*.asm` |
| `jsdoc-standards` | JSDoc 및 @ts-check 문서화 표준 | `**/*.js` |

## 2. Registered code-writing skills

| Skill | Description | When |
|-------|-------------|------|
| `code-writing-guard` | No dupes/wrappers/hardcoding | Before new code |
| `logging-standards` | `logMgr_ModuleLog`, formatting | Adding logs |
| `jsdoc-standards` | JSDoc, `@ts-check` | New functions/classes |
| `module-registration` | IIFE, globals | New modules |
| `html-registration` | `dashboard.html` scripts | New JS files |
| `refactoring-safety` | Large refactors | Before big moves |
| `git-push-workflow` | Korean commits, push | **User explicitly requests** |

| Skill | Description |
|-------|-------------|
| `manage-skills` | 스킬 시스템 관리자 |
| `implementation-plan` | 작업 계획 수립 및 승인 프로세스 |
| `document-authoring` | `docs/` 내 문서 작성 표준 |

---

## 4. Step 1 — Collect changed files

```bash
git diff HEAD --name-only
git log --oneline main..HEAD 2>/dev/null
git diff main...HEAD --name-only 2>/dev/null
```

Deduplicate. Optional: filter by user-provided skill/area.

**Display template:** group by directory — see **§10** “Session Changes”.

---

## 5. Step 2 — Map skills ↔ files

1. Use **§1** table; if empty, all files = UNCOVERED → go to Step 4.
2. Else read each `verify-*/SKILL.md`: **Related Files**, **Workflow** paths/globs. If `reference.md` exists in the same folder, use it for full step lists and `rg` patterns.
3. Match each changed file to 0+ skills.

**Output template:** **§10** “File → Skill Mapping”.

---

## 6. Step 3 — Gap analysis per affected skill

For each skill with matched files, read its `SKILL.md` (and **`reference.md`** if present) and check:

- Missing **Related Files** entries for changed paths
- Outdated **grep/glob** (dry-run sample)
- **New patterns** in diffs not covered
- **Stale** paths (file deleted/moved)
- **Renamed** constants/settings the skill still names

Record gaps — **§10** “Gap table”.

---

## 7. Step 4 — CREATE vs UPDATE vs exempt

```
IF file fits an existing skill's domain → UPDATE that skill
ELSE IF 3+ files share a new rule/pattern → consider CREATE verify-* 
ELSE → exempt (config, docs, lockfile — see §12)
```

Present **§10** “Proposed Actions”. Confirm with user (`AskUserQuestion` or equivalent) when creating skills or large edits.

---

## 8. Step 5 — Update existing skills

- Add only what’s needed; do not remove working checks.
- Extend **Related Files**, detection commands, workflow steps — prefer **`reference.md`** for new long content so **`SKILL.md`** stays **≤ 200 lines** (see **§12**).
- Remove paths that no longer exist.
- After edits, run the **`SKILL.md` line-count check** for the touched folder (**§11**).

**Examples:** new Related Files row; new workflow step with `rg` — see original skill for markdown shape.

### 8.1 Domain verify skills

프로젝트에 새로운 도메인 검증 스킬이 추가되면 여기에 관련 규칙과 경로를 등록합니다.

---

## 9. Step 6 — Create new `verify-*` skill

1. Explore changed files; confirm **name** with user (`verify-<kebab-case>`).
2. Create `.agent/skills/verify-<name>/SKILL.md` with:
   - YAML frontmatter (`name`, `description`)
   - Short **Purpose / When / Related / outline** only — **≤ 200 lines** total file.
   - Put full workflow steps, `rg` blocks, matrices, and exceptions in **`reference.md`** in the same folder (same pattern as existing `verify-*`).
3. **Sync registry** (same session):
   - **4a** `manage-skills/SKILL.md` — §1 table in **this** reference (and mirror in SKILL if kept)
   - **4b** `verify-implementation/SKILL.md` — target list
   - **4c** `CLAUDE.md` — `## Available Skills` tables (Korean one-line for verify-*)

---

## 10. Markdown templates (copy/paste)

### Session changes

```markdown
## Session Changes Detected

**N files changed:**

| Directory | Files |
|-----------|-------|
| static/js/... | `a.js`, `b.js` |
```

### File → skill

```markdown
### File → Skill Mapping

| Skill | Trigger files | Action |
|-------|----------------|--------|
| verify-api-routes | `routes/foo.py` | CHECK |
| (none) | `package.json` | UNCOVERED |
```

### Gaps

```markdown
| Skill | Gap type | Details |
|-------|----------|---------|
| verify-grid | Missing file | `gridFoo.js` not listed |
```

### Proposed actions

```markdown
### Proposed Actions

**UPDATE:** …
**CREATE:** …
**Exempt:** …
```

### Final report

```markdown
## Session Skill Maintenance Report

### Analyzed: N files
### Updated skills: …
### Created skills: …
### Synced files: manage-skills, verify-implementation, READMEs, CLAUDE.md
### Uncovered / exempt: …
```

---

## 11. Step 7 — Verification pass

- Re-read edited SKILLs; markdown valid.
- `ls` each path in Related Files.
- Dry-run one `rg` per updated skill.
- **§1** table ↔ `verify-implementation` target list aligned.
- **`SKILL.md` line-count check (mandatory):** ensure **every** skill under `.agent/skills/` complies with the **200-line** limit on **`SKILL.md`** (see **§12**).

### 11.1 Check all `SKILL.md` line counts (repo root)

**PowerShell** (line count = `Get-Content | Measure-Object -Line`; **includes** YAML frontmatter):

```powershell
Get-ChildItem -Path .agent/skills -Recurse -Filter SKILL.md | ForEach-Object {
  $n = (Get-Content $_.FullName | Measure-Object -Line).Lines
  "$n $($_.FullName)"
} | Sort-Object { [int]($_ -split ' ')[0] } -Descending
```

**Pass:** every line starts with a number **≤ 200** (first column).

**Fail:** any **`SKILL.md` > 200 lines** → **split**: move detailed sections to **`reference.md`** (create or extend), shorten **`SKILL.md`** to summary + link (same pattern as `verify-*` and skills already refactored).

**When to run:** end of a **manage-skills** session, after adding/editing any skill, or when the user asks for a hygiene pass.

---

## 12. Quality bar (created/updated skills)

- Real paths only (no `path/to/placeholder`).
- Detection commands that run on this repo.
- Clear PASS/FAIL + fix hint per step.
- ≥2 realistic **exceptions**.
- **`SKILL.md` ≤ 200 lines (all skills):** Applies to **every** `.agent/skills/<name>/SKILL.md` — not only **`verify-*`**. Count **YAML + body**; keep **Purpose / When / Related / outline / Rules** in **`SKILL.md`**; move long workflow, command blocks, examples, and large tables to **`reference.md`**.
- **`CLAUDE.md` ≤ 200 lines:** The `## Available Skills` section in `CLAUDE.md` is managed by this skill. **Do not** re-expand full trigger/skill-ledger text here — it lives in **`§0`**. When adding/removing skills, update the table and verify the total line count stays **≤ 200**. If it exceeds, trim descriptions or merge rows.
- **`verify-*` layout:** Full workflow lives in **`reference.md`**; agents read **`reference.md`** when executing checks.

---

## 13. Exceptions (not a coverage problem)

1. Lockfiles / generated artifacts  
2. One-off version bumps in package manifests (unless policy changes)  
3. Pure docs: `README`, `CHANGELOG`, `LICENSE`  
4. Test fixtures dirs  
5. Skills with **no** touched files — skip deep review  
6. `CLAUDE.md` doc-only edits
7. `vendor/`, `node_modules/`  
8. CI config (`.github/`, `Dockerfile`, …) — unless project adds verify-ci

---

## 14. Related paths

**Canonical skill root:** **`.agent/skills/`** — versioned project skills (**`SKILL.md`**, **`reference.md`**) live here. **`CLAUDE.md` § Available Skills** and **`verify-implementation`** reference this path.

**`.cursor/skills`:** Often the **same directory tree** via symlink/junction to **`.agent/skills`**. **Do not** run `Copy-Item` or two-way sync — one edit is enough. If you ever have a **standalone** duplicate under **`.cursor/skills`**, **do not** treat it as authoritative; edit **`.agent/skills/`** only.

| Path | Role |
|------|------|
| `verify-implementation/SKILL.md` | Ordered verify-* run list |
| `manage-skills/SKILL.md` | Entry point |
| `.agent/skills/` | **Authoritative** skill directory (per-repo) |
| `CLAUDE.md` | User-facing skill list |

---

---

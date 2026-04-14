---
name: manage-skills
description: >
  Skill system admin: pre-flight orchestration (which skills to read), mandatory end-of-turn
  skill ledger, auto-trigger SSOT, drift vs CLAUDE.md, gap analysis, and maintenance (registry,
  verify-implementation, SKILL.md line budget, verify-* reference sync). Use on every substantive
  turn implicitly, or when the user asks for skill work (스킬 수정, 스킬 추가, 스킬 동기화,
  스킬 관리, manage-skills).
disable-model-invocation: true
argument-hint: "[Optional: skill name or area to focus on]"
---

# Skill system admin + session maintenance

**Orchestration (every turn), 사용된 스킬 리스트업, 자동 트리거 SSOT, Skill 도구 실패 시 Read:**  
→ **`reference.md` §0**

**Maintenance workflow (steps 1–8), templates, registry tables, CREATE checklist, sync list:**  
→ **`reference.md` §1–§15**

## Purpose

0. **Canonical folder** — All project skills live under **`.agent/skills/<name>/`**. Edit **`SKILL.md` / `reference.md`** there. **`.cursor/skills`** may be a symlink/junction to the same tree — **do not** `Copy-Item` or maintain a second copy by hand (**`reference.md` §14**).
1. **Orchestration (admin)** — Before substantive work, classify intent and **plan which skills to `Read`/apply**; enforce **`reference.md` §0** (triggers, chains, end-of-response ledger). **Point out** conflicts (e.g. `CLAUDE.md` table vs repo skills) and **missing coverage**; route to gap/CREATE steps below.
2. **Drift Audit (Non-negotiable)** — Core logic 변경(예: 복구 한도, 시계열 로직 등) 시 **반드시** 관련 `verify-*` 스킬의 `reference.md`를 함께 열어 수치 및 로직 기술의 일치 여부를 대조(Audit)하고 동기화해야 한다. (누락 시 Audit Failure로 간주)
3. **Coverage gaps** — Changed files not covered by any relevant `verify-*` skill.
4. **Stale references** — Skills pointing at deleted/moved paths or outdated `rg` patterns.
5. **New patterns** — Rules in code not yet reflected in any skill.
6. **Drift** — Constants, settings keys, or commands that no longer match the repo.
7. **`SKILL.md` size** — Every skill under **`.agent/skills/<name>/`** must keep **`SKILL.md` ≤ 200 lines** (YAML + body). Long steps, tables, and `rg` blocks belong in **`reference.md`**. Run the **line-count check** in **`reference.md` §11** during maintenance sessions.
8. **Domain verify skills ↔ code** — When behavior in **`reference.md` §8.1** domains changes, update the matching **`verify-*/reference.md`** in the **same session** as the code change when possible.
9. **Independent of code-writing skills** — Orchestration, registry, and skill-doc drift (**this skill**) are **not** satisfied by claiming **`/code-writing-guard`** was followed, and **vice versa**. Neither substitutes for the other — **`reference.md` §0.7**.

## When To Run

- **Implicitly first** on every user turn: apply **`reference.md` §0** pre-flight (intent → skills → ledger obligation). Full `Read` of §0 is required when triggers are ambiguous or many skills chain.
- After features that add new conventions or touch many files.
- Before PR when verify coverage should match the diff.
- When a verify run missed something you expected.
- Periodically to refresh skill tables vs. codebase.

Optional **argument:** focus on one skill name or subdirectory (filter changed files).

---

## Registry (authoritative copy)

**Verification skills, code-writing skills, workflow skills** — tables in **`reference.md` §1–3**. Update those tables when you add/remove/rename skills.

---

## Workflow (outline)

1. **Collect** changed paths (`git diff`, `git log` range) — **`reference.md` §4**.
2. **Map** each file → existing `verify-*` (read each skill’s Related Files / Workflow) — **§5**.
3. **Gap analysis** per affected skill — **§6**.
4. **Decide** UPDATE vs CREATE vs exempt — **§7**, **§13** exceptions.
5. **Edit** affected **`SKILL.md` / `reference.md`** (often `verify-*`; any skill must stay ≤200 lines in **`SKILL.md`**) — **§8**.
6. **Create** new `verify-<name>/SKILL.md` if approved; **confirm name** with user — **§9**.
7. **Sync** `verify-implementation`, READMEs, **`CLAUDE.md`** — **§9** bullets 4a–4e.
8. **Verify** markdown, path existence, one dry-run `rg` per touched skill, and **all** `SKILL.md` files **≤ 200 lines** — **§11**.

**Markdown snippets** for session report / mapping — **§10**.

**Quality bar** for any new/updated skill — **§12** (includes **`SKILL.md` line limit** for **every** skill, not only `verify-*`).

---

## Rules

- **Approval Gating (Explicit Only)**: 사용자의 직접적이고 명시적인 요청(**"승인해", "진행해", "수정해줘", "내가 작업해"**)이 없는 한 코드 수정을 포함한 어떠한 실행도 진행하지 마십시오. 기술적 질문에 대한 답변("설명해줘"), 긍정적 호응("응", "맞아"), 또는 계획서에 대한 일반적인 피드백은 **승인(Approval)이 아닙니다.**
- **Authoritative path:** **`.agent/skills/`** — all skill content is maintained here; **`CLAUDE.md`** and **`verify-implementation`** point here.
- Do **not** delete working checks without replacing coverage.
- New verify skills: **`verify-` + kebab-case**; real paths only (**`ls`**), no placeholders.
- **Ask the user** before creating a new skill or renaming (per project process).
- **Line budget:** No **`.agent/skills/*/SKILL.md`** may exceed **200 lines**. If it does, move content to **`reference.md`** (create or extend) and leave **`SKILL.md`** as summary + link — **§11** for the check command and **§12** for scope (`verify-*` and non-verify).

---

## Related

- **`reference.md`**: **`§0` orchestration / 사용 스킬 SSOT**, **`§0.7` independence vs code-writing-guard**, tables §1–3, steps §4–11, **`§8.1` domain verify sync**, **`SKILL.md` line-count §11.1**, templates §10, exceptions §13, paths §14–§15.
- **`verify-implementation/SKILL.md`**: must stay in sync with the verify-* list.
- **`CLAUDE.md`**: project rules + short pointers; **must not** duplicate §0 — sync **Available Skills** tables only (§12).

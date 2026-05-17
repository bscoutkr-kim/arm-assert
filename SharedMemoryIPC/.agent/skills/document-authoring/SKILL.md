---
name: document-authoring
description: >
  Project docs layout under docs/, mandatory filename suffix _YYMMDD.md for new files (e.g. _260321.md),
  per-folder templates, and exceptions (debugging_notes). Use when writing or reorganizing markdown in docs/
  (e.g. 문서 작성, docs 정리, 계획서 md, 리뷰 문서, 아키텍처 노트).
---

# Document Authoring

**폴더 맵, 파일명 규칙(`_YYMMDD.md`), 종류별 템플릿 섹션, 예외·이전 시 링크 갱신:**  
→ `.agent/skills/document-authoring/reference.md`

## Purpose

1. **`docs/`** 아래 문서를 **종류별 하위 폴더**에 둔다 — 루트에 산재한 `*.md` 남발 금지(신규 기준).
2. **신규 마크다운 파일명**은 반드시 **작성일 기준 `_YYMMDD.md`** 접미사를 붙인다 (예: `settings_viewer_ui_plan_260321.md`). 상세·예외는 **`reference.md`**.
3. **`docs/debugging_notes.md`** 는 **루트 고정** — 파일명 규칙·이동 대상에서 제외 (`CLAUDE.md` SSOT).
    - **순환(Rotation) 정책**: 파일이 2000줄을 초과할 경우 `scripts/rotate_debugging_notes.py`를 실행하여 오래된 기록을 `docs/archive/`로 분리 보관한다.
4. 문서 **본문 형식**은 종류별 템플릿 섹션 순서를 따른다 — **`reference.md`** 의 `_TEMPLATE` 요약.

## When To Use

- 새 계획서·리뷰·검증 리포트·조사 노트·가이드·아키텍처 메모를 **`docs/`** 에 추가할 때
- **`docs/`** 폴더 정리·이동·이름 규칙 적용을 할 때
- 다른 스킬(`implementation-plan`, `verify-implementation`) 산출물을 **파일로 남길 때** — 저장 위치·이름은 이 스킬 우선

## Related

- **`reference.md`**: 폴더 표, `_YYMMDD.md` 규칙, 예외, 템플릿, 링크 깨짐 방지
- **`CLAUDE.md`**: `debugging_notes` 정책
- **`/code-writing-guard`**: `tests/` 는 §12; **프로젝트 문서 트리**는 이 스킬

## Never Do

- **`debugging_notes.md`** 를 하위 폴더로 옮기거나 날짜 접미사로 개명하지 않는다
- 날짜 없이 신규 `docs/*.md` 를 루트에만 추가하는 것을 기본으로 하지 않는다 — **`reference.md`** 예외만 허용

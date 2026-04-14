---
name: git-push-workflow
description: >
  Commits and pushes local changes with Korean commit messages per project workflow.
  Use only when the user explicitly asks to commit or push (e.g. 커밋, 푸시, git push).
---

# Git Push Workflow

**전체 단계별 절차, 예외 처리:**
→ `.agent/skills/git-push-workflow/reference.md`

## Purpose

1. 로컬의 모든 수정사항을 확인하고 스테이징합니다.
2. 한국어 커밋 메시지를 임시 파일(`commit_msg.txt`)로 작성합니다.
3. 지정된 원격 브랜치로 **푸시만** 수행합니다 (`git pull` 절대 금지).
4. 작업 완료 후 임시 파일을 삭제하여 환경을 정리합니다.

## ⚠️ 핵심 규칙

- **`git pull` 금지** — 원격이 앞서 있으면 `git push --force origin <branch>` 사용
- **`git add .` 금지** — 변경된 파일을 명시적으로 지정 (`git add file1 file2`)
- **데이터 수집 선택화** — 사용자 명시 요청("데이터 포함") 시에만 `sync_data.py --collect` 수행
- **사용자 명시 요청 시에만 실행**

## When to Run

- 사용자가 "커밋해줘" / "푸시해줘"라고 명시적으로 요청할 때

## Workflow (outline)

→ 전체 절차는 `reference.md` 참조

1. `python scripts/sync_data.py --collect` — **[선택]** (사용자 명시 요청 시에만 실행)
2. `git status` / `git diff --stat` — 변경 확인
3. `commit_msg.txt` 작성 — `docs/debugging_notes.md` 기반 한글 메시지
4. `git add <files>` + `git commit -F commit_msg.txt` (수집 시 sync_data/ 폴더 포함)
5. `git push origin <branch>` (거절 시 `--force`)
6. `docs/debugging_notes.md` 최상단에 푸시 기록 추가
7. `commit_msg.txt` 삭제

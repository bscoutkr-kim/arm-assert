# Git Push Workflow — Reference

`SKILL.md`의 동반 파일. 전체 단계별 절차 상세.

---

## Step 0: 데이터 수집 (선택 사항)

사용자가 "데이터 동기화 포함" 또는 "설정/로그 포함"과 같이 **명시적으로 요청**한 경우에만 데이터를 수집하여 `sync_data/` 폴더를 업데이트합니다. 평상시에는 이 단계를 건너뜁니다.

```bash
# 사용자 명시 요청 시에만 수행
python scripts/sync_data.py --collect
```

---

## Step 1: 변경 사항 확인

```bash
git status
git diff --stat
```

---

## Step 2: 커밋 메시지 작성 (임시 파일 생성)

1. `docs/debugging_notes.md`를 읽어 마지막 푸시 이후의 모든 변경 사항을 파악합니다.
2. Write 툴을 사용하여 루트 디렉토리에 `commit_msg.txt` 파일을 생성하고, 파악한 내용을 바탕으로 한글 커밋 메시지를 상세히 작성합니다.

---

## Step 3: 스테이징 및 커밋

변경된 파일을 **명시적으로** 지정하여 스테이징합니다 (`git add .` 사용 금지).

```bash
# 변경된 파일 및 수집된 데이터(수집 발생 시 sync_data/)를 명시적으로 지정
git add path/to/file1.js [sync_data/]

# 파일 기반 커밋
git commit -F commit_msg.txt
```

---

## Step 4: 원격 브랜치 푸시 (pull 없이)

현재 작업 중인 브랜치로 **푸시만** 수행합니다. `git pull` 절대 금지.

```bash
git push origin <branch_name>
```

거절되면(원격이 앞서 있는 경우) force push로 로컬 상태를 원격에 반영합니다.

```bash
git push --force origin <branch_name>
```

---

## Step 5: 디버깅 노트 업데이트 (푸시 기록 남기기)

푸시 성공 후 `docs/debugging_notes.md`의 **최상단(Template 바로 아래)**에 다음과 같이 푸시 기록을 추가합니다.

- **topic**: `snkim2 브랜치 푸시 완료` (또는 해당 브랜치명)
- **change**: 해당 커밋의 핵심 요약 및 Git Commit Hash 정보 포함
- **status**: ✅ Pushed to `origin/<branch>`

---

## Step 6: 임시 파일 삭제

```bash
rm commit_msg.txt
```

---

## Output Format

| 데이터 수집 | 선택 | 수집됨 / 건너뜀 (요청 없음) |
| 변경 확인 | 완료 | N개 파일 수정 확인 |
| 메시지 작성 | 완료 | `commit_msg.txt` 생성됨 |
| 커밋 수행 | 완료 | 파일 기반 커밋 완료 |
| 푸시 수행 | 완료 | `origin/<branch>`에 반영됨 |
| 정리 작업 | 완료 | `commit_msg.txt` 삭제됨 |

---

## Exceptions

1. **변경 사항이 없는 경우**: `git status` 결과가 깨끗하면 커밋 단계를 건너뜁니다.
2. **푸시 거절(non-fast-forward)**: 원격이 로컬보다 앞서 있을 때 **pull 하지 않고** `git push --force origin <branch_name>` 으로 푸시합니다.
3. **파일명 중복**: 이미 `commit_msg.txt`라는 다른 목적의 파일이 존재한다면 이름을 변경하여 충돌을 피해야 합니다.

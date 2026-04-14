# Document Authoring — Reference

Companion to `SKILL.md`. Folder taxonomy, **`_YYMMDD.md`** naming, templates, exceptions.

---

## 1. Root layout

| Path | Role |
|------|------|
| **`docs/debugging_notes.md`** | 운영·수정 기록 SSOT — **항상 루트**, `CLAUDE.md` · 스킬이 참조. **파일명 규칙·이동 대상 아님** |
| **`docs/README.md`** | (선택) 문서 맵·이 스킬 한 줄 요약 |
| **`docs/plan/`** | 구현·리팩터·UI·기능 **계획** (승인 전후 설계) |
| **`docs/review/`** | **코드 리뷰**, PR/변경 대조, 설계 검토 |
| **`docs/verify/`** | 검증 리포트, verify-* 실행 결과 요약 |
| **`docs/research/`** | 원인 분석, 조사, 실험 메모, 일회성 분석 |
| **`docs/guide/`** | 개발환경·도구·운영 **가이드** |
| **`docs/architecture/`** | 장기 구조 · 연동 · 도메인 개요 |
| **`docs/archive/`** | **아카이브** — `debugging_notes.md` 순환(Rotation) 시 구형 기록 보관 |

**판단이 애매하면** `research/` 에 두고, 안정화 후 `plan/` 또는 `architecture/` 로 옮겨도 된다.

---

## 2. Filename rule — `_YYMMDD.md` (필수, 신규)

- **신규** 마크다운 파일은 **작성일(또는 문서 기준일)** 6자리 **`YYMMDD`** 를 파일명 **끝·확장자 직전**에 붙인다.
- 형식: **`<slug>_YYMMDD.md`**  
  - 예: `settings_viewer_ui_plan_260321.md`, `grid_recovery_fix_review_260321.md`
- **구분자**는 **하나의 밑줄**로 날짜 앞에 둔다 — 사용자 요청 예: `_260321.md` → 파일 전체는 `topic_260321.md` 가 아니라 **`topic_descriptive_260321.md`** (slug에 의미, 날짜는 마지막 `_YYMMDD`).

**`slug` 규칙**

- **`snake_case`**, ASCII 권장 (기존 한글 파일명은 이전 시에만 유지 가능).
- 종류가 폴더로 구분되므로 접미사 `_plan` / `_review` 는 **선택**(중복이면 생략 가능).

**예외 (날짜 접미사 생략 허용)**

- **`debugging_notes.md`**
- **`README.md`** (폴더 인덱스)
- 각 폴더의 **`_TEMPLATE.md`** (복사용 템플릿)
- **기존 파일 rename 없이 링크만 수정**하는 핫픽스가 아닌, 팀이 합의한 **대량 이관** 전까지는 레거시 이름 유지 가능 — 신규는 무조건 `_YYMMDD.md`

---

## 3. Templates (섹션 순서)

새 문서는 해당 폴더의 **`_TEMPLATE.md`** 를 복사해 시작한다. 없으면 아래 최소 섹션을 채운다.

| Folder | 최소 섹션 |
|--------|-----------|
| `plan/` | 목적 · 범위(포함/제외) · 배경 · 설계 요약 · 영향 파일 · 리스크 · 완료 기준 |
| `review/` | 대상(브랜치/커밋) · 요약 · 필수 수정 · 선택 개선 · 근거(파일·라인) |
| `verify/` | 범위 · 통과 요약 · 이슈(일괄) · 재검증 방법 |
| `research/` | 현상 · 가설 · 확인한 사실(증거) · 결론/다음 조치 |
| `guide/` | 대상 독자 · 전제 · 절차 · 트러블슈팅 |
| `architecture/` | 개요 · 경계 · 데이터 흐름 · 관련 코드 경로 |

---

## 4. 이동·정리 시

- `rg "docs/[^\\s]+\.md"` 로 링크 참조를 찾아 **경로 갱신**한다.
- `implementation-plan` · `verify-implementation` 산출물을 저장할 때 **이 규칙과 폴더**를 따른다.

### 4.1. `debugging_notes.md` 순환(Rotation)

- **임계치**: 파일 크기가 **2000줄**을 초과하면 순환을 고려한다.
- **수행 방법**: `python scripts/rotate_debugging_notes.py` 실행.
- **결과**:
    - 오래된 기록은 `docs/archive/debugging_notes_archived_YYMMDD.md`로 이동.
    - 메인 파일에는 템플릿과 최신 기록(~500줄)만 남음.

---

## 5. Related

- `CLAUDE.md` — `debugging_notes`
- `/code-writing-guard` `reference.md` §12 — `tests/` (실행 스크립트; 문서 트리와 별개)

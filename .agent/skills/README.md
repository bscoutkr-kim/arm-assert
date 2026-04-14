# Cursor Skills

이 폴더는 ARM Core 분석 및 ARM Assert 분석 프로젝트를 위한 커스텀 스킬들을 포함합니다.

## 핵심 스킬 목록

| Skill | Purpose |
|-------|---------|
| `/code-writing-guard` | 코드 작성 및 수정 시 클린 코드 원칙과 프로젝트 표준을 강제합니다 (중복 제거, 래퍼 제거 등) |
| `/implementation-plan` | 변경 전 계획 수립, 구현, 검증에 이르는 통합 워크플로우를 관리합니다 |
| `/manage-skills` | 스킬 시스템 관리자: 스킬 선택, 자동 트리거, 정합성 검사 및 유지보수를 수행합니다 |
| `/document-authoring` | `docs/` 내 기술 문서 작성 표준 및 템플릿을 정의합니다 |
| `/jsdoc-standards` | 공개 API 및 함수에 대한 문서화 표준 및 타입 체크를 정의합니다 |
| `/git-push-workflow` | 한글 커밋 메시지를 포함한 프로젝트 표준 Git 푸시 워크플로우를 실행합니다 |

## 사용법

```bash
# 작업 계획 수립 (구현 전 필수)
/implementation-plan

# 작업 완료 후 기록 및 검토
/code-writing-guard

# 스킬 시스템 관리 및 동기화
/manage-skills
```

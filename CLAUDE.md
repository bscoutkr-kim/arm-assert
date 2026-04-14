# ARM Multi-Core Bare-Metal Analysis Project Rules

이 파일은 OS가 없는 ARM 멀티코어 환경의 분석 및 개발 프로젝트를 위한 절대 금지 사항 및 필수 실천 사항을 정의합니다.

## 🔴 Absolute Prohibitions (절대 금지 사항)

### 1. OS 추상화 가정 금지
- ❌ Mutex, Semaphore 등 OS 레벨의 동기화 객체가 존재한다고 가정하지 마십시오.
- ❌ 모든 동기화는 하드웨어 프리미티브(`LDREX`/`STREX`, `DMB` 등)를 기준으로 분석하십시오.

### 2. 단일 코어 중심 분석 금지
- ❌ Assert 발생 코어만 분석하지 마십시오. 공유 메모리 오염 가능성을 배제하기 위해 주변 코어의 상태를 반드시 병행 분석하십시오.

### 3. CPU 상태에 대한 임의 추측 금지
- ❌ 확인되지 않은 레지스터 상태나 CPU 모드를 임의로 가정하지 마십시오.
- ❌ "아마도 ~일 것이다" 식의 추측보다는 반드시 데이터나 아키텍처 문서(ARM ARM)를 근거로 제시하십시오.

## ✅ Mandatory Practices (필수 실천 사항)

### 1. 메모리 모델 및 배리어 검증
- ✅ 멀티코어 환경의 Weakly-ordered memory 모델을 고려하여 데이터 접근 전후에 적절한 `DMB`/`DSB` 배리어가 있는지 검증하십시오.

### 2. 하드웨어 동기화 분석
- ✅ 공유 자원 접근 시 원자적 조작(`LDREX`/`STREX`)의 무결성을 최우선으로 확인하십시오.

### 3. ARM Architecture Reference Manual (ARM ARM) 참조
- ✅ 모든 분석은 해당 아키텍처 버전의 ARM ARM 또는 기술 참조 매뉴얼(TRM)을 기반으로 수행하십시오.

### 4. 분석 로그 및 레지스터 트레이스 기록
- ✅ 분석 과정에서 확인된 핵심 레지스터 상태 변화나 메모리 덤프 내용을 문서화하십시오.
- ✅ Assert 발생 시점의 콜 스택과 주변 컨텍스트를 상세히 기록하십시오.

### 5. Communication Language (의사소통 언어)
- ✅ **모든 응답은 한글로 작성하세요.**

---

## Available Skills

| Skill | 용도 |
|-------|------|
| `/arm-assert-analyzer` | **핵심**: ARM Assert 가설 기반 분석 — FW 소스 중심, T32는 증거 수집용 (Hypothesis-Driven RCA) |
| `/implementation-plan` | 작업 계획 수립 및 승인 프로세스 |
| `/code-writing-guard` | 코드 작성 표준 — 중복 금지, 클린 코드 |
| `/jsdoc-standards` | JSDoc 및 @ts-check 문서화 표준 |
| `/document-authoring` | `docs/` 내 문서 작성 표준 및 템플릿 |
| `/manage-skills` | 스킬 시스템 오케스트레이션 및 관리 공식 매뉴얼 |

---

## Skill 사용 흐름

1. **작업 시작 전**: 의도에 맞는 스킬을 선택하고 `Read` 하여 규칙을 숙지합니다.
2. **동기화 분석 시**: `/arm-assert-analyzer`의 멀티코어 분석 가이드를 최우선으로 따릅니다.
3. **완료 후**: `docs/debugging_notes.md`에 기록하고, 응답 말미에 **`📋 사용된 스킬: ...`** 형식을 반드시 포함합니다.

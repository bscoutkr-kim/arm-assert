---
name: arm-assert-analyzer
description: >
  ARM Core 및 Assert 분석 전문 에이전트 스킬. T32 덤프 데이터와 ELF/Source를 결합하여 
  최적화된 코드에서 누락된 로컬 변수 상태를 레지스터 역추적을 통해 복원하고 RCA를 수행합니다.
---

# ARM Assert Analyzer (Multi-Stage Design)

본 스킬은 컨텍스트 사이즈 제한을 극복하고 효율적인 분석을 수행하기 위해 **5단계(Phase) 분할 분석** 방식을 강제합니다.

## 🔄 Multi-Stage Workflow

### Phase 0: Reliable Data Extraction (T32 Setup)
- **목표**: 분석 전 T32 환경에서 정확한 심볼 및 원본 데이터를 획득.
- **주요 작업**: MCP 환경에서의 `/noclear` 옵션 적용, 소스 경로 매핑, 코어별 필터링.
- **Rule**: 데이터 획득이 실패하거나 변수값이 0으로만 나올 경우, 반드시 `reference.md` §0을 참조하여 사용자에게 T32 환경 재설정을 제안할 것.

### Phase 1: Context Extraction & Normalization
- **목표**: 모든 코어의 raw T32 데이터를 분석 가능한 구조로 변환.
- **입력**: All Cores Register dump, Stack, Call stack.
- **출력**: `crash_context.md` (멀티코어 결함 정황).

### Phase 2: Assembly-Source Alignment
- **목표**: C 소스와 바이너리 명령어 1:1 매핑 및 레지스터 할당 분석.
- **입력**: ELF 파일, `objdump -S` 결과, 소스 코드.
- **출력**: `register_variable_map.md` (레지스터 할당 테이블).

### Phase 3: State & Sync Reconstruction (Global-Prioritized)
- **목표**: 전역 변수 상관관계 분석을 통한 로컬 변수 복원 및 동기화 이슈 추론.
- **입력**: Phase 1의 값 + Phase 2의 매핑 정보.
- **출력**: `inferred_state.md` (복원된 실행 경로 및 공유 자원 상태).
- **Rule**: 전역 변수 간의 논리적 모순을 먼저 찾고, 이를 바탕으로 로컬 변수 값을 역산할 것.

### Phase 4: Root Cause Synthesis
- **목표**: 근본 원인(RCA) 규명 및 해결책 제안.
- **출력**: `root_cause_analysis.md` (최종 보고서).

## 🛡️ Analysis Rules
- **Multi-Core Consistency**: 공유 데이터 접근 시 배리어(`DMB`) 유무와 원자적 조작(`LDREX`)의 무결성 검증.
- **Global-Prioritized Inference**: 데이터 부족 시 전역 상태 머신을 최우선으로 분석할 것.

## 📂 Related Paths
- `docs/analysis/`: 분석 결과물 저장 경로.
- `.agent/skills/arm-assert-analyzer/reference.md`: 상세 분석 기법 및 T32 설정 가이드.

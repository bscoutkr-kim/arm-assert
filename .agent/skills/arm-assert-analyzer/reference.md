# ARM Assert Analysis - Technical Reference

본 문서는 `arm-assert-analyzer` 에이전트가 최적화된 코드의 미궁을 풀기 위해 사용하는 논리적 엔진과 분석 기법을 상세히 기술합니다.

---

## 0. T32 Multi-Core Environment Setup (Data Collection)

분석 전 T32 Simulator에서 정확한 데이터를 추출하기 위한 필수 설정 가이드입니다.

### Reliable Symbol Loading (MCP/AMP/SMP)
- **Prevent Symbol Overwrites**: 멀티코어 환경에서 여러 ELF를 로드할 때, 첫 번째 이후에는 반드시 `/noclear` 옵션을 사용하십시오. (예: `Data.LOAD.Elf core1.elf /noclear`)
- **Debug Info Only**: 시뮬레이션 분석 시 `Data.LOAD.Elf <file> /nocode`를 사용하여 메모리 쓰기 없이 심볼만 로드하십시오.
- **Path Remapping**: 빌드 환경과 소스 위치가 다를 경우 `/STRIPPART <n> /PATH <local_path>` 옵션으로 소스를 동기화하십시오.

### Data Access & Context
- **Core Selection**: SMP 환경에서는 `CORE.Select <n>` 명령으로 대상 코어를 지정한 후 레지스터나 변수를 확인하십시오.
- **Address Space (Access Class)**: MMU가 활성화된 경우 주소 앞에 `D:`(Data), `V:`(Virtual) 등 액세스 클래스를 명시하여 정확한 물리/가상 주소에 접근하십시오.

---

## 1. Register-Variable Mapping Heuristics (Phase 2)

최적화된 코드에서는 변수와 레지스터가 1:N 또는 N:1로 매핑될 수 있습니다.

### 레지스터 할당 패턴 추적
- **Arg Loading**: 함수 시작 부분의 `MOV R5, R0` -> 변수 `arg0`가 이후 `R5`로 관리됨을 의미.
- **Immediate Loading**: `MOVS R1, #0x0` -> `R1`에 매핑된 변수가 `0`으로 초기화됨을 의미.
- **Arithmetic Result**: `ADDS R2, R1, #4` -> `R2`에 매핑된 변수가 `R1(변수 A) + 4`의 결과임을 추론.

### Mapping Table 예시
| Register | 소스 변수 | 상태 | 근거 (Assembly) |
| :--- | :--- | :--- | :--- |
| R0 | `msg_ptr` | Null? | `LDR R0, [R4, #8]` |
| R4 | `ctx_object` | Valid | `MOV R4, R0` (함수 진입 인자) |

---

## 2. Multi-Core & Bare-Metal Analysis Heuristics

OS가 없는 멀티코어 환경의 동기화 이슈를 분석하는 지침입니다.

### Memory Ordering & Barriers (DMB, DSB)
- **Problem**: 한 코어의 데이터 쓰기가 다른 코어에 즉시 보이지 않을 수 있습니다.
- **Check**: 공유 변수 업데이트 전후에 `DMB` 배리어가 있는지 확인하십시오. 누락 시 Race Condition의 결정적 증거가 됩니다.

### Atomic Operations & Spinklocks
- **Check**: `LDREX`, `STREX` 배타적 명령어 쌍의 사용 패턴을 분석하여 임계 영역 보호 무결성을 검토하십시오.

---

## 3. Global State-based Hypothesis Generation (전략)

데이터 부족 시 전역 변수의 상태 조합을 통해 원인을 역추적합니다.

### 상태 상관관계 분석 (Correlation)
1. **State Machine 대조**: 시스템 메인 상태 변수들을 확인하여 소프트웨어의 현재 '모드'를 확정합니다.
2. **논리적 모순 탐지**: 서로 독립된 전역 변수들 간의 불가능한 값 조합을 체크합니다. (예: Lock == 0 인데 Resource Count != 0)

### Pointer-to-Global Alias Analysis
- 로컬 포인터가 `optimized out` 된 경우, 레지스터 주소값이 전역 변수의 메모리 범위(`&symbol` ~ `&symbol + size`)에 포함되는지 대조하여 가리키던 대상을 특정합니다.
- `(레지스터 주소) - (전역 주소)` 연산으로 구조체 멤버나 배열 인덱스를 역산합니다.

---

## 4. Phase-specific Work Templates (Agent Staging)

### Phase 1: Context Extraction
- **PC/LR**: [Address]
- **Core Status**: [Core ID, Mode, IRQ status]
- **Registers**: (Structured Table)

### Phase 2: Assembly Mapping
- **Mapping Table**: (Register ↔ Source Var)

### Phase 3: State Reconstruction
- **Global Audit**: (State correlation result)
- **Inferred State**: (Restored local variables & path)

### Phase 4: RCA Report
1. **Summary**
2. **Root Cause**
3. **Execution Trace**
4. **Solution**

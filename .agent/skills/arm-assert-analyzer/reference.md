# ARM Assert Analysis - Technical Reference

본 문서는 `arm-assert-analyzer`의 **가설 기반(Hypothesis-Driven) 분석**에 사용되는 상세 기법을 기술합니다.

---

## §0. T32 환경 설정 (데이터 수집)

T32 Simulator에서 데이터를 추출할 때의 설정 가이드입니다.
**단, T32 데이터 수집 실패가 분석 중단 사유가 되지 않습니다.**

### Symbol Loading (MCP/AMP/SMP)
- **로드 순서**: 첫 번째 ELF는 일반 로드. 두 번째 이후는 `/noclear` 필수. (예: `Data.LOAD.Elf core1.elf /noclear`)
- **Debug Info Only**: `Data.LOAD.Elf <file> /nocode` — 메모리 쓰기 없이 심볼만 로드.
- **Path Remapping**: `/STRIPPART <n> /PATH <local_path>` — 빌드/소스 경로 불일치 보정.

### Data Access
- **Core Selection**: `CORE.Select <n>` — SMP 환경에서 대상 코어 지정.
- **Access Class**: MMU 활성 시 `D:`(Data), `V:`(Virtual) 등 명시.

### Thumb 상태 (AArch32)
- CPSR.T==1이면 Thumb/Thumb-2. PC 정렬·IT 블록이 디스어셈블리에 영향.

---

## §1. Phase 1 상세 - Triage

### 소프트웨어 Assert와 하드웨어 예외 (판별 순서)

1. PC/LR이 `__assert` 핸들러, abort 루틴, `BKPT` 등 의도적 정지 구역인지 맵 파일로 확인.
2. Fault/예외 레지스터가 유효한 fault 코드·주소를 담는지 확인.
3. (2)가 동기 예외 → **하드웨어 예외 경로** 우선.
4. (1)만 명확 → **SW Assert 경로** 우선.
5. 둘 다 겹치면 시간 순서·스택으로 최종 정지 원인 구분.

### 아키텍처별 예외·컨텍스트

| 구분 | AArch32 | AArch64 |
|------|---------|---------|
| Fault 레지스터 | DFSR/IFSR, DFAR/IFAR | ESR_ELx, FAR_ELx |
| 모드·인터럽트 | CPSR, SPSR, CPSR.T | PSTATE, CurrentEL, SPSR_ELx |
| 스택 | 모드별 뱅크드 SP | SP_ELx |

덤프에 EL/모드가 불명확하면 ELF의 ISA와 벡터 테이블·링커 스크립트로 보조 확정.

### 코어별 최소 필드

각 코어에 대해 채울 것 (Assert 코어만이 아님):

| 필드 | 설명 |
|------|------|
| Core ID | 논리 코어 번호 |
| PC / LR | 현재·복귀 주소 (심볼+오프셋) |
| 실행 여부 | 실행 중 / WFE·WFI·정지 등 |
| 모드·EL | AArch32 모드 또는 AArch64 EL |
| 공유 자원 흔적 | 락·공유 버퍼·플래그 주소 추정 |
| Fault 레지스터 | ESR/DFSR 등 (해당 시) |

---

## §2. Phase 2 상세 - 6-Step Source Analysis

### Step 1: Assert 조건 분해

- Assert 매크로/함수의 조건식을 파싱.
- 조건의 각 변수에 대해: 타입, 유효 범위, 실패 가능한 값 열거.
- 복합 조건(`&&`, `||`)은 각 부분 조건별로 분해.
- 예: `assert(buf->state == READY)` → `buf`가 NULL? `state`가 다른 enum 값? `buf`가 해제 후 재사용?

### Step 2: 함수 역할·책임 분석

- Assert가 있는 함수의 전체 시스템 내 역할 파악.
- 분류: 초기화 루틴 / 주기적 처리 / ISR 핸들러 / 상태 전이 콜백 / 에러 핸들러.
- 함수의 전·후 조건(precondition/postcondition) 추론.
- 함수 내 Assert 위치: 진입부(인자 검증) vs 중간(상태 검증) vs 종료부(결과 검증).

### Step 3: 호출 경로 역추적 (Call Graph)

- 이 함수를 호출하는 **모든 caller** 추적 (직접 호출 + 함수 포인터/콜백 테이블).
- 각 호출 경로의 실행 컨텍스트: Main loop? ISR? Boot sequence? Timer callback?
- 컨텍스트별로 Assert 조건 위반 가능성 평가.
- 재귀 호출·간접 호출 경로 주의.

### Step 4: 데이터 의존성 추적

- Assert 조건에 관여하는 변수의 **모든 write 지점** 나열.
- 각 write 지점에서 "잘못된 값을 쓸 수 있는 조건" = **가설 후보**.
- 전역 변수라면 다른 파일·모듈에서의 write도 반드시 추적.
- 구조체 멤버는 해당 구조체를 수정하는 모든 함수를 대상으로.

### Step 5: 공유 자원·동기화 분석

- 해당 변수가 멀티코어 또는 ISR에서 공유되는지 판단.
- 보호 메커니즘 확인: `LDREX/STREX`, `DMB`, 인터럽트 마스킹(`CPSID`/`CPSIE`) 등.
- 보호 부재 또는 불완전 → **race condition 가설** 생성.
- 단일 코어 내에서도 ISR이 main-loop의 비원자적 Read-Modify-Write를 선점할 수 있음.
- 상세 하드웨어 분석 기법은 §4 참조.

### Step 6: 타이밍·초기화 순서 분석

- 멀티코어 boot 순서에서 코어 간 초기화 의존성 → 순서 역전 가능성.
- 상태 전이 순서에서 예상치 못한 이벤트 조합.
- 인터럽트 활성화 타이밍 vs 데이터 준비 완료 타이밍 간의 경쟁.
- 하드웨어 초기화(주변장치, DMA) 완료 전 접근 시나리오.

### Lens 7 (선택): 빌드·이미지·산술 — SW 보강 스캔

6 Step 필수 수행 후, 아래를 **체크리스트**처럼 한 번 훑어 Lens 태그(`sw_lens`)를 부여한다. 해당 없으면 "해당 없음"으로 표기.

| 점검 | 가설에 넣을 내용 예 |
|------|---------------------|
| **빌드·매크로** | `#if`/`#ifdef`로 이 번들에 코드가 포함되는지, `CONFIG_*`에 따라 Assert 조건 경로가 사라지지 않는지 |
| **이미지·심볼 경계** | AMP/SMP에서 이 코어 ELF·링커 스크립트에 해당 심볼·함수가 실제로 링크되는지(다른 코어 이미지와 혼동) |
| **정수·캐스트** | 오프셋·길이·카운트 연산의 overflow, 부호/무부호 캐스트, 좁은 타입 승격 |
| **인덱스·링 버퍼** | 배열 인덱스, modulo, head/tail 경계 한 치 오차 |
| **문서·코드 초기화** | 부트 순서·데이터시트 요구와 ISR 활성화 시점이 모순되지 않는지(Step 6과 연계) |

### 가설 출력 형식 (필수 + 확장 필드)

**필수 열**

| 항목 | 내용 |
|------|------|
| ID | H-01, H-02, … (연속 번호, 중간 비우지 않음) |
| 가설 요약 | 한 줄 설명 |
| 발생 Step | Step 1~6 또는 Lens 7 |
| 검증 분류 | [A] 소스만으로 판정 가능 / [B] T32 증거 필요 |
| 필요 증거 | [B]의 경우 구체적 T32 명령·확인 대상 |
| 우선순위 | 높음/중간/낮음 (코드 구조 기반 가능성) |

**확장 열(권장: 재개·교차 검증용)**

| 항목 | 내용 |
|------|------|
| `minimal_code_citation` | 근거가 되는 **파일 경로 + 줄 번호 또는 심볼**(한 줄이라도) |
| `sw_lens` | 태그 예: `build`, `image`, `integer`, `index`, `init_order`, `isr_vs_main`, `sync`, `lens7` |
| `depends_on` | 이 가설이 성립하면 같이 참이어야 하는 다른 H-xx (선택) |
| `conflicts_with` | 판명 시 제거되는 H-xx (선택) |
| 불변식/근거 메모 | Assert 직전까지 기대 상태 한 줄, 또는 위반 시나리오 |

동일 주제 가설이 많으면 **클러스터 제목**으로 묶고, 대표 H-xx에만 `depends_on`을 두어도 된다.

---

## §3. Phase 3 상세 - 가설 검증 (증거 수집 실패 내성)

### 판정 흐름

1. **[A] 소스 기반 판정**: 코드 로직만으로 가설 확인/제거.
   - 제거 예: "이 경로는 컴파일 플래그에 의해 비활성화됨."
   - 강화 예: "보호 없이 공유 변수를 접근하는 코드가 실존함."

2. **[B] T32 증거 기반 판정**:
   - 가설에 필요한 구체적 T32 데이터 수집 시도.
   - **수집 성공** → 레지스터·메모리 값으로 가설 확인 또는 제거.
   - **수집 실패** → 아래 규칙 적용.

### 증거 수집 실패 시 규칙

| ❌ 하지 말 것 | ✅ 해야 할 것 |
|--------------|--------------|
| "분석 불가" 결론 | 가설을 **미검증** 상태로 유지 |
| 해당 가설 폐기 | 소스 분석 기반 **확신도**(높음/중간/낮음) 부여 |
| 분석 중단 | **다음 가설**로 진행 |

- 미검증 가설에는 반드시: **"[데이터 X]가 있으면 이 가설을 확정/제거 가능"** 명시.
- 다수의 미검증 가설이 남아도, 소스 기반 확신도로 **우선순위 정렬**하여 잠정 결론 도출.

### 가설 판정 결과 형식

| ID | 가설 | 판정 | 확신도 | 근거 / 미검증 사유 |
|----|------|------|--------|-------------------|
| H-01 | ptr NULL deref | **확인** | 높음 | R0=0x0, LDR R0,[R4,#8] |
| H-02 | race on flag_x | **미검증** | 중간 | Core1 레지스터 수집 실패. flag_x lock 부재 확인(소스) |
| H-03 | stack overflow | **제거** | — | SP=0x20001000, 스택 범위 내 |

---

## §4. 하드웨어 분석 기법

### 배리어 선택

- **DMB**: 관측 순서 제한 (프로듀서-컨슈머·플래그+데이터).
- **DSB**: 이전 메모리·CMO 완료 대기.
- **ISB**: 파이프라인 플러시 (컨텍스트/특권 변경 후).

컴파일러 순서 재배치와 하드웨어 메모리 순서는 별개. **실제 명령 순서** 기준 검증.

### Cache Coherency

- Write-back 캐시에서 stale data 가능성 → `Clean`(DCCMVAC) + `Invalidate`(DCIMVAC) 검증.
- CMO 전후 `DMB`/`DSB` 위치 확인.

### 배타 연산 (LDREX/STREX)

- LDREX-STREX 쌍 완결성, 중간 일반 스토어 금지.
- STREX 실패 시 재시도 루프 vs 데드락 구분.
- LDREX-STREX 사이 인터럽트 허용 여부 확인.

### Stack Integrity

- SP 값이 코어/모드별 할당 범위 내인지 확인 → 오버플로우 조기 감지.

---

## §5. Register-Variable Mapping (가설 검증 보조)

### 레지스터 할당 패턴 추적

- **Arg Loading**: `MOV R5, R0` → arg0이 R5로 관리.
- **Immediate**: `MOVS R1, #0x0` → R1 변수가 0 초기화.
- **Arithmetic**: `ADDS R2, R1, #4` → R2 = R1(변수A) + 4.

### Pointer-to-Global Alias

- optimized out된 로컬 포인터 → 레지스터 주소가 전역 변수 범위에 포함되는지 대조.
- `(레지스터 주소) - (전역 주소)` → 구조체 멤버·배열 인덱스 역산.

### 추론 품질

- 복원한 값·경로는 **근거(명령·전역·스택)** + **확신도** + **대안 가설** 명시.

---

## §6. Phase 산출물 템플릿

### Phase 1: Triage
- **문제 분류**: Assert / Data Abort / Prefetch Abort / Stack Overflow / Undefined
- **PC/LR**: [주소 + 심볼]
- **CPSR/PSTATE**: [모드·마스크·Thumb]
- **Per-core table**: 코어별 최소 필드

### Phase 2: Hypothesis List
- `docs/analysis/hypothesis_list.md` — H-01 ~ H-nn (§2 가설 출력 형식: 필수 + 확장 열)
- 동시에 `docs/analysis/SESSION.md` 핸드오프 갱신 (§7)

### Phase 3: Hypothesis Verdict
- 전체 판정 결과 테이블 (§3 판정 결과 형식)

### Phase 4: RCA Report
1. **Summary** (한 줄 요약)
2. **Root Cause** (확신도 명시, 확인된/잠정 가설 기반)
3. **Execution Trace** (소스 경로 + 증거)
4. **Solution** (수정 제안)
5. **Open Points** (미검증 가설 + 확정 필요 데이터)

---

## §7. 단일 진실 원천(SSoT) 및 세션 핸드오프

### 역할

- **`docs/analysis/hypothesis_list.md`**: 모든 가설·판정 근거·코드 인용의 **정본**. 채팅이 끊겨도 여기부터 복구한다.
- **`docs/analysis/SESSION.md`**: 현재 진행 위치 **한 화면 요약**. 새 에이전트 턴의 진입점.

### 새 턴·새 세션 시작 절차

1. `SESSION.md`를 읽어 Phase·열린 H-xx·다음 액션을 확인한다.
2. `hypothesis_list.md`에서 **미결 가설**과 **마지막으로 수정한 타임스탬프/섹션**을 확인한다.
3. 필요 시에만 `hypothesis_verdict.md`, 소스 파일을 추가로 연다(전체 재읽기 남용 금지).

### `SESSION.md` 템플릿 (복사해 사용)

```markdown
# Analysis session handoff

- **Incident / 브랜치**: 
- **Arch**: AArch32 | AArch64 (고정)
- **이미지 / 코어**: (예: core0 ELF 이름, SMP n코어)
- **현재 Phase**: 1 | 2 | 3 | 4
- **열린 가설 ID**: H-.., H-..
- **마지막으로 갱신한 파일**: hypothesis_list.md (섹션 …)
- **다음 액션 (한 줄)**:
- **차단 사항**: 없음 | (데이터/접근 이슈)
```

매 Phase 전환·가설 대량 추가 후·작업 세션 종료 전에 **반드시** 갱신한다.

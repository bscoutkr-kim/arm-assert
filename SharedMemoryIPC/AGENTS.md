# Project Coding Rules (SharedMemoryIPC)

이 파일은 SharedMemoryIPC 프로젝트를 개발할 때 반드시 준수해야 하는 **절대 금지 사항**과 **필수 관행**을 명시합니다.

---

## 🔴 Absolute Prohibitions (절대 금지 사항)

### 1. No Compatibility/Wrapper/Legacy Layers (래퍼 및 레거시 배제)
- ❌ **NEVER** create compatibility functions, wrapper layers, or legacy adaptors.
- ❌ 기존 함수나 클래스의 동작을 감싸서 변환해주는 불필요한 인디렉션(Indirection)을 만들지 마십시오.
- ❌ 구현체 자체를 리팩토링하거나 변경하고, 모든 호출처(Call sites)를 최신 구현체에 직접 대응하도록 한 번에 수정하십시오.

### 2. No Silent Resource Leaks & Fallbacks (자원 누수 및 에러 묵인 금지)
- ❌ **절대** 공유 메모리 자원(`shm.close()`, `shm.unlink()`) 해제나 락(Lock) 릴리즈 과정을 누락하지 마십시오.
- ❌ 공유 메모리 오버플로우나 락 타임아웃 발생 시 조용히 넘어가거나 임의의 폴백(Fallback) 값을 반환하지 마십시오.
- ❌ 예외 상태는 즉시 예외를 발생시키거나 경고/오류 로그를 남겨 호출하는 에컨트가 예외 흐름을 인지하도록 보장해야 합니다.

### 3. No Duplicate Implementations (중복 구현 금지)
- ❌ 동일한 목적의 메모리 조작, 인덱스 계산, 파일 락 획득 로직을 분산하여 구현하지 마십시오.
- ❌ 수정 및 구현을 시작하기 전에 반드시 `rg` (Grep Search)를 사용해 동일한 로직이나 유틸리티가 존재하는지 확인하고, 싱글 소스(SSOT)로 관리하십시오.

### 4. No Fake UI / Mock Orchestration (가짜 UI 및 모의 연출 절대 금지)
- ❌ 사용자에게 웅장한 AI 협업인 것처럼 사기 치기 위한 하드코딩된 모의 핑퐁 시나리오, 인위적인 `time.sleep` 지연, 특정 종목(삼성전자 등) 고정형 가짜 템플릿을 소스에 주입하지 마십시오.
- ❌ API Key가 없거나 런타임 환경 결손 시, 가짜 데이터를 그럴듯하게 뿌려 속이지 말고, **반드시 정직하게 실행 불가 혹은 API Key 미등록 오류 상태를 챗 UI 버블로 투명하게 공표**해야 합니다.

---

## ✅ Mandatory Practices (필수 준수 사항)

### 1. Call Implementation Directly (직접 호출 원칙)
- ✅ 에이전트 간 통신 드라이버 호출 시 중간 래퍼 없이 `SharedMemoryIPCDriver` 클래스를 직접 인스턴스화하고 메소드를 직접 호출하십시오.
- ✅ 추상화라는 명목 하에 단순 포워딩만 수행하는 다단계 계층 구조를 추가하는 행위를 배제하십시오.

### 2. Clean & Performant Low-Level Design (간결하고 성능 중심의 저수준 설계)
- ✅ 링 버퍼(Ring Buffer)와 세마포어(Semaphore)의 원리에 충실하게, 불필요한 오버헤드(과도한 JSON 파싱 등)를 줄일 수 있는 방향으로 설계하십시오.
- ✅ CPU Spin-lock을 피하고, 락 대기 시 OS 스케줄러가 개입할 수 있도록 파일 락 또는 적절한 `time.sleep()` 양보(yield) 패턴을 설계하십시오.

### 3. Communication Language (의사소통 언어 원칙)
- ✅ **모든 AI 응답, 계획서, 설명, 의견은 한글(한국어)로 작성하세요.**
- ✅ 단, 소스 코드 내의 함수명, 변수명, 주석, 기술 용어는 일관성을 위해 **영문(English)**을 유지합니다.

### 4. Git Commit & Push Policy
- ❌ **절대 임의로 깃 커밋이나 푸시를 진행하지 마십시오.**
- ✅ 코드 수정 완료 후 변경사항을 정제하여 요약하고 사용자 승인을 대기하십시오.
- ✅ 사용자가 명시적으로 커밋/푸시를 요청할 때만 `git-push-workflow`를 활용해 진행하십시오.

### 5. 코드 수정 전 계획 승인 필수
- ❌ **사용자 승인 없이 소스 코드를 임의로 수정하거나 파일을 대량 생성하지 마십시오.**
- ✅ 변경이 필요한 경우 `implementation_plan.md` 아티팩트를 작성해 설명하고 확인 후 진행합니다. (버그 픽스 시 현상-원인 위주 최소안 우선).

### 6. 디버깅 노트 작성 (`docs/debugging_notes.md`)
- ✅ 의미 있는 코드 수정이나 문서 추가/변경 완료 후 `docs/debugging_notes.md`에 변경의 핵심 내용을 **역순(최신 글이 최상단)**으로 작성하십시오.
- ✅ 필수 필드: `when`, `topic`, `change`, `test`, `evidence`, `next`

### 7. Karpathy-Style Coding Principles (단순함과 효율성)
- ✅ **Think Before Coding**: 코딩 전 가정을 명시하고, 기존 패턴을 검색하며, 트레이드오프를 엄격히 분석합니다.
- ✅ **Simplicity First**: 불필요하게 똑똑해 보이는 다형성이나 클래스 설계보다, 단순하게 작동하고 읽기 쉬운 절차와 모듈을 선호합니다.
- ✅ **Surgical Changes (외과수술적 변경)**: 수정이 필요한 코드 영역만 타겟하여 최소한의 충격으로 작업을 끝마칩니다.

### 8. 지식 그래프 최신화 (Graphify)
- ✅ 파이썬 핵심 코드를 수정한 후에는 저장소 루트에서 `graphify update .` 명령을 실행하여 지식 그래프를 최신 상태로 유지하십시오.

---

## 📂 Available Skills (.agent/skills/)

- `code-writing-guard`: 코드 작성 표준 — 중복/래퍼/하드코딩 방지.
- `logging-standards`: 파이썬 표준 로깅 패턴 정의.
- `implementation-plan`: 계획 -> 구현 -> 검증 라이프사이클 관리.
- `git-push-workflow`: 사용자 요청에 의한 안전한 깃 커밋/푸시.
- `graphify`: 지식 그래프 탐색 및 업데이트 도구.
- `document-authoring`: `docs/` 파일 명명 규칙(`*_YYMMDD.md`).
- `lint-fix-standard`: ruff 및 static type 검증 표준.

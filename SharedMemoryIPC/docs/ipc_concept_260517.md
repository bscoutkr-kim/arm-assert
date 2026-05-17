# 에이전트 간 공유 메모리 IPC 설계 명세서 (SharedMemoryIPC)

본 문서는 Windows, Linux, macOS 등 다중 OS 환경에서 작동하는 독립 에이전트(Agent) 간의 명령어(Commands) 및 문맥 대화(Context) 송수신을 위한 **저수준 공유 메모리 IPC(Inter-Process Communication) 아키텍처**를 정의합니다.

---

## 1. IPC 아키텍처 설계 개요

에이전트 시스템은 비동기적으로 작동하며, 한 에이전트의 실행 결과나 대화 Context가 다른 에이전트의 명령어 입력으로 유입되는 상호작용 체계를 가집니다. 이를 네트워크 스택 오버헤드 없이 극도로 빠른 지연 시간(Microsecond 수준)으로 처리하기 위해 **공유 메모리(Shared Memory)**를 기본 통신 채널로 설계합니다.

```mermaid
graph TD
    AgentA[Agent A] <--> |Write / Read| OS_SHM[OS Shared Memory]
    AgentB[Agent B] <--> |Write / Read| OS_SHM
    
    subgraph Shared Memory Layout [1MB Physical Memory Space]
        Header[Metadata Header: 64 Bytes]
        Body[Circular Ring Buffer: N Slots]
    end
    
    OS_SHM --> Shared Memory Layout
```

---

## 2. IPC 대안 기술 비교 분석

에이전트 간 로컬 통신을 위해 고려된 대표적인 세 가지 IPC 기술의 비교 분석입니다.

| 비교 항목 | 공유 메모리 (Shared Memory) | TCP/IP 루프백 소켓 | Unix Domain Socket (UDS) / Named Pipes |
| :--- | :--- | :--- | :--- |
| **물리적 메커니즘** | OS 메모리 매핑 영역을 프로세스 주소 공간에 병합하여 직접 접근 | 네트워크 루프백 인터페이스(127.0.0.1) 경유 | 파일 시스템 경로 또는 커널 파이프 오프셋 이용 |
| **지연 시간 (Latency)** | **극도로 낮음 (100ns ~ 1µs)** | 높음 (50µs ~ 150µs, OS 네트워크 오버헤드) | 낮음 (10µs ~ 30µs) |
| **OS 이식성 (Portability)** | **우수** (Python 3.8+ 표준 라이브러리 `shared_memory`로 추상화) | **최상** (모든 플랫폼 동일 소스) | **보통** (UDS 윈도우 지원 제약, Windows는 Named Pipe 필수 분기) |
| **통신 가변성** | 고정 크기 블록 기반 (순환 버퍼 설계 필요) | 바이트 스트림 기반 (가변 데이터 처리 용이) | 스트림/메시지 기반 |
| **동시성 제어** | **어려움** (동기화 락/세마포어 수동 설계 필요) | **없음** (OS 커널이 원자적 큐 제공) | **없음** (OS 커널이 동기화 처리) |
| **최종 평가** | ⚡ **속도가 매우 빠르고 크로스 플랫폼 표준 모듈이 정립되어 있으나, 락과 순환 버퍼 설계의 구현 난이도가 높음** | 🌐 개발이 가장 쉽고 범용적이나, 네트워크 오버헤드가 발생함 | 💻 OS별 파이프 인터페이스 분기 코드가 비대해지는 단점이 있음 |

> **결론**: 본 과제는 저수준 드라이버 설계를 포함하므로, 극강의 속도와 OS 표준 추상화를 동시에 달성하기 위해 **공유 메모리(Shared Memory)**를 채택하고, 동기화 제어는 **크로스 플랫폼 파일 시스템 락(File Lock)**을 통해 보완하는 방향으로 설계합니다.

---

## 3. 공유 메모리 레이아웃 (Memory Layout)

공유 메모리는 전체 **1MB (1,048,576 Bytes)** 크기로 할당되며, 고정 오프셋 기반의 **헤더(Metadata Header)**와 **바디(Circular Ring Buffer)**로 구성됩니다.

### 3.1 Metadata Header (64 Bytes)
공유 메모리의 무결성 검증 및 동기화 인덱스 조회를 위해 물리 메모리 최상단에 배치되는 고정 영역입니다.

```
+-------------------------------------------------------------+
| magic_bytes (4B) | version (2B) | shm_size (8B)             |
+-------------------------------------------------------------+
| write_index (8B) | read_index (8B)                          |
+-------------------------------------------------------------+
| lock_state (4B)  | msg_count (4B)                           |
+-------------------------------------------------------------+
| reserved (26B)                                              |
+-------------------------------------------------------------+
```

| 필드명 | 데이터 타입 | 크기 | 용도 |
| :--- | :--- | :--- | :--- |
| `magic_bytes` | `char[4]` | 4 Bytes | 프로토콜 식별자 (`"SIPC"`) |
| `version` | `uint16` | 2 Bytes | 프로토콜 버전 (`0x0001`) |
| `shm_size` | `uint64` | 8 Bytes | 전체 공유 메모리 크기 (Bytes) |
| `write_index` | `uint64` | 8 Bytes | 다음에 새 메시지를 기록할 링 버퍼 슬롯 인덱스 |
| `read_index` | `uint64` | 8 Bytes | 링 버퍼 상 가장 오래된 유효 메시지의 슬롯 인덱스 |
| `lock_state` | `uint32` | 4 Bytes | 동시성 제어를 위한 예비 소프트웨어 스핀락 상태 |
| `msg_count` | `uint32` | 4 Bytes | 현재 버퍼에 쌓여 있는 미처리 메시지 개수 |
| `reserved` | `char[26]` | 26 Bytes | 향후 기능 확장을 위한 패딩 및 예약 필드 |

### 3.2 Circular Ring Buffer Body (나머지 영역)
- **슬롯당 크기**: **4KB (4,096 Bytes)** 고정
- **최대 슬롯 개수**: (1,048,576 - 64) / 4,096 = **255 Slots**
- 링 버퍼 인덱스가 최대 슬롯 개수(`255`)에 도달하면 `modulo` 연산(`index % 255`)을 통해 다시 `0`번 슬롯부터 순환하여 덮어씁니다.

---

## 4. 메시지 구조체 (Message Structure) 설계

하나의 버퍼 슬롯(Slot)에 저장되는 데이터의 이진(Binary) 규격입니다. 가변 텍스트 데이터인 명령어와 대화 문맥(Context)은 **UTF-8 JSON 문자열**로 직렬화하여 페이로드 필드에 기록합니다.

```
+-----------------------------------------------------------------------+
| slot_magic (4B) | msg_id (8B) | timestamp (8B)                        |
+-----------------------------------------------------------------------+
| sender_id (32B - char)                                                |
+-----------------------------------------------------------------------+
| command (64B - char)                                                  |
+-----------------------------------------------------------------------+
| payload_len (4B)                                                      |
+-----------------------------------------------------------------------+
| payload (3,976B - JSON String in UTF-8)                               |
+-----------------------------------------------------------------------+
```

| 필드명 | 데이터 타입 | 크기 | 용도 |
| :--- | :--- | :--- | :--- |
| `slot_magic` | `char[4]` | 4 Bytes | 슬롯의 유효성을 식별하는 바이트 (`"MSLT"`) |
| `msg_id` | `uint64` | 8 Bytes | 전체 수명 주기 동안 순차적으로 증가하는 전역 메시지 ID |
| `timestamp` | `uint64` | 8 Bytes | 메시지 생성 시점의 에폭 타임스탬프 (ms 단위) |
| `sender_id` | `char[32]` | 32 Bytes | 송신 에이전트 식별자 (Null-terminated UTF-8) |
| `command` | `char[64]` | 64 Bytes | 수행할 명령어 종류 또는 카테고리 (Null-terminated UTF-8) |
| `payload_len` | `uint32` | 4 Bytes | payload 실제 유효 바이트 길이 (최대 3,976) |
| `payload` | `char[3976]` | 3,976 Bytes | 대화 Context 및 데이터 본문 (JSON 포맷 권장) |

---

## 5. 크로스 플랫폼 동기화 프로토콜 (File Mutex)

여러 독립 에이전트 프로세스가 동일한 공유 메모리 영역에 동시에 쓰거나 읽을 때 발생하는 Race Condition을 완벽히 격리하기 위해 **OS 수준의 파일 락(File-based Mutex)**을 활용합니다.

### 5.1 파일 시스템 락 메커니즘
- 공유 메모리 이름과 일치하는 락 파일(예: `SharedMemoryIPC.lock`)을 임시 디렉토리(Temp)에 생성합니다.
- Python의 `msvcrt` (Windows) 및 `fcntl` (Linux/macOS) 모듈을 이용해 파일 전체 영역에 대해 **배타적 락(Exclusive Lock)**을 요청합니다.
- 배타적 파일 락은 OS 커널이 관리하므로 CPU 스핀락 없이 가장 안전하게 크로스 플랫폼 뮤텍스를 실현할 수 있습니다.

### 5.2 쓰기 프로토콜 (Write Sequence)
```
[Agent Writer] ----> 1. Acquire File Lock (Exclusive)
                         |
                         v
                    2. Read Header Metadata (write_index, msg_count)
                         |
                         v
                    3. Write Slot Data (Slot index = write_index % 255)
                         |
                         v
                    4. Update Header (write_index += 1, msg_count += 1)
                         |
                         v
                    5. Release File Lock
```

### 5.3 읽기 프로토콜 (Read Sequence)
```
[Agent Reader] ----> 1. Acquire File Lock (Shared/Exclusive)
                         |
                         v
                    2. Compare Header write_index with local last_read_id
                         |
                         +---> If last_read_id == write_index:
                         |         Release Lock & Return None (No New Message)
                         |
                         v
                    3. Read Slot Data (Slot index = last_read_id % 255)
                         |
                         v
                    4. Update local last_read_id += 1
                         |
                         v
                    5. Release File Lock
```

---

## 6. 예외 처리 및 저수준 자원 안전 보장

공유 메모리와 파일 락은 하드웨어 및 OS 자원이므로 예기치 못한 크래시 발생 시 다음과 같은 예외 복구 시나리오를 탑재합니다.

1. **Deadlock 탐지 및 해제**:
   - 파일 락을 획득하는 대기 시간(Timeout)을 최대 **2.0초**로 제한합니다.
   - 2초 이내에 락을 획득하지 못하면 예외(`SharedMemoryIPCLockError`)를 발생시키고 좀비 프로세스 여부를 진단합니다.
2. **프로세스 크래시 시 자원 자동 반환 (`Context Manager`)**:
   - `SharedMemoryIPCDriver` 클래스는 파이썬의 `__enter__` 및 `__exit__` 컨텍스트 매니저 인터페이스를 제공하여 예외나 강제 종료 상황에서도 반드시 `shm.close()`가 실행되도록 보장합니다.
3. **가장 마지막 프로세스의 메모리 반환 (`unlink`)**:
   - 공유 메모리는 OS 커널에 종속적이므로 프로세스가 모두 꺼져도 메모리에 상주합니다.
   - 드라이버 인스턴스 종료 시, 활성화된 에이전트 카운트가 `0`이 되거나 강제 정리 명령이 인입될 때 `shm.unlink()`를 호출하여 완전히 메모리를 해제합니다.

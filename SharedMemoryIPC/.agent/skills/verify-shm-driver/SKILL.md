# 🔒 SharedMemoryIPC Driver Verification Standards (verify-shm-driver)

이 스킬은 공유 메모리(Shared Memory) 통신 인프라, 동시성 제어 파일 락, 다중 에이전트 비동기 스레딩 및 외부 UI(웹뷰 등) 브릿지를 개발하고 검증할 때 반드시 준수해야 하는 **자원 무결성** 및 **에러 예방** 표준을 정의합니다.

---

## 1. 🔴 공유 메모리 라이프사이클 및 레이스 컨디션 방지

### 1.1 `close()` 와 `destroy()` 의 명확한 분리
- **`close()`**: 해당 에이전트 인스턴스의 메모리 매핑과 연결만 안전하게 해제합니다. 타 에이전트 통신에 영향을 주지 않으므로 개별 에이전트 종료 시에만 호출해야 합니다.
- **`destroy()`**: 공유 메모리를 OS 풀에서 완전히 파괴(`unlink`)하고 임시 락 파일까지 디스크에서 삭제합니다.
- ❌ **절대** 동작 중인 다중 에이전트가 존재할 때 개별 에이전트가 `destroy()`를 임의로 호출하지 마십시오. 전체 채널이 붕괴되어 타 에이전트가 크래시를 겪게 됩니다.
- ✅ `destroy()`는 전체 시스템의 기동을 주도하고 모든 에이전트가 내려간 것을 확인한 **마스터 데몬/중앙 오케스트레이터 프로세스**만 종료 시점에 최종적으로 수행해야 합니다.

### 1.2 비동기 폴링 루프 내 널 가드 (Null Guard)
- 에이전트 백그라운드 스레드는 상시 무한 루프를 돌며 폴링하므로, 리소스 정리 시점에 레이스 컨디션이 발생합니다.
- ✅ 폴링 루프 진입 및 메시지 읽기/쓰기 시도 직전에 반드시 드라이버가 유효하고 공유 메모리가 바인딩되어 있는지 **널 검사**를 수행하고 우아하게 루프를 빠져나와야 합니다.
  ```python
  # 올바른 가드 패턴
  while not stop_evt.is_set():
      if not driver.shm:
          break  # 공유 메모리가 이미 master에 의해 destroy/close 되었다면 즉시 중단
  ```

---

## 2. 락 제어 및 CPU 점유 최적화

### 2.1 크로스 플랫폼 배타적 파일 락 명세
- Windows 환경에서 `msvcrt.locking` 함수를 사용할 때 비차단(Non-blocking) 락 및 락 해제 상수는 반드시 아래 표준 명세를 준수하십시오:
  - ❌ `msvcrt.LK_NB` (존재하지 않는 속성 - 오류 유발)
  - ❌ `msvcrt.LK_UN` (존재하지 않는 속성 - 오류 유발)
  - ✅ **`msvcrt.LK_NBLCK`** (비차단 락 표준)
  - ✅ **`msvcrt.LK_UNLCK`** (락 해제 표준)

### 2.2 CPU Spin-lock 방지 (Yield 강제)
- 링 버퍼에 새로운 메시지가 존재하지 않아 `read_next_message` 가 `None`을 반환하는 경우, CPU 코어를 100% 점유하지 않도록 **반드시 최하 10ms ~ 100ms**의 대기시간을 주어 OS에 자원을 양보해야 합니다.
  ```python
  if msg is None:
      time.sleep(0.05)  # 50ms 대기 (Yield)
      continue
  ```

---

## 3. 🌐 Javascript/Webview 브릿지 연동 및 문자열 이스케이프

### 3.1 `json.dumps()` 매개변수 바인딩 규칙 (강제)
- 파이썬에서 웹뷰(pywebview 등) 측으로 이벤트를 주입하기 위해 `window.evaluate_js`를 호출하여 JS 함수를 렌더링할 때, F-스트링 문자열 포맷팅(`f"'{var}'"`)을 절대 사용하지 마십시오.
- F-스트링을 사용하면 파이썬의 백슬래시, 따옴표 중첩 및 한국어 디코딩 예외 메시지(`'NoneType' object...`)가 전달될 때 JS 문자열 구문이 깨져 **`SyntaxError: missing ) after argument list`** 가 발생합니다.
- ✅ **모든 동적 파라미터는 반드시 `json.dumps(var)`로 직렬화하여 전달하십시오.** JSON으로 감싸면 따옴표 중첩이 완벽하게 회피되며 특수 기호가 안전하게 이스케이프되어 JS 구문 오류가 원천 소멸됩니다.
  ```python
  # ❌ 금지 패턴: 구문 깨짐 취약
  window.evaluate_js(f"addMessage('{sender}', '{text}');")

  # ✅ 권장 패턴: JSON 안전 직렬화
  import json
  window.evaluate_js(f"addMessage({json.dumps(sender)}, {json.dumps(text)});")
  ```

### 3.2 WebView GUI 호환성 백엔드 및 Fallback 지원
- Windows의 특정 개발 환경(예: .NET 런타임 불일치, Edge WebView2 미설치 상태 등)에서 `pywebview` 창이 켜지자마자 즉시 닫히는 현상이 발생할 수 있습니다.
- ✅ pywebview의 단일 GUI 메인 루프 프로세스 제한(동일 프로세스 내 재시작 불가) 및 MSHTML 강제 종료 정책을 우회하기 위해, **Windows OS 환경에서는 100% 호환성 기동을 보장하는 `gui='edgehtml'`을 기본값(Default)으로 강제 적용**하고, 고급 사용자를 위해 `--edge` 및 `--mshtml` 옵션을 통해서만 타 엔진 구동을 시도하도록 설계하여 검증 무결성을 확보하십시오.


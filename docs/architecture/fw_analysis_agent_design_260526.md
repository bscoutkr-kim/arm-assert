# 🛠️ Firmware Failure Analysis Agent Design (FW 불량 분석 에이전트 설계서)

본 문서는 T32 덤프, UART 로그, 펌웨어 소스 코드 등의 데이터를 융합 분석하여 불량의 근본 원인(Root Cause)을 도출하기 위해, LangGraph 프레임워크 기반의 동적 라우팅 및 피드백 루프 아키텍처를 도입하는 설계 명세서입니다.

---

## 1. 개요 (Overview)
기존의 하드코딩된 단방향(Linear) 분석 프로세스의 한계를 극복하고, **LLM이 분석 결과를 평가하여 다음에 검증할 영역(T32 Dump, Cross-Core, NAND 등)을 동적으로 선택**하여 추적하는 순환 피드백 루프 에이전트 시스템을 구축합니다.
이를 통해 복잡한 임베디드 예외(Exception), 하드웨어 오작동, 소프트웨어 데드락이 얽힌 문제를 다각도에서 교차 검증할 수 있습니다.

---

## 2. 경계 (Boundaries)

### 입력 데이터 경계
- **T32 Dump / Register Context**: 코어 별 CPU 레지스터, 콜스택, 메모리 덤프 데이터.
- **Console/UART Log**: 시스템 부팅 및 크래시 발생 직전의 실시간 로깅 및 커널 메시지.
- **Source Code**: 예외가 발생한 주소 주변의 C/C++ 펌웨어 소스 코드 영역.

### 분석 도구 경계
- **Cursor CLI API**: 펌웨어 소스 코드의 컴파일 에러 및 의미론적 버그를 분석하는 API.
- **인메모리 FailureState**: 분석가 간 정보 교환 및 제어에 사용되는 유일한 공유 상태 데이터.

### 출력 경계
- **Final Failure Analysis Report**: 근본 원인(Root Cause) 요약, 실현 가능한 불량 재현 경로(Reproduction Path), 펌웨어/하드웨어 패치 조치 방안(Action Plan).

---

## 3. 데이터 흐름 (Data Flow)

시스템은 최초의 거시 분석 이후, LLM이 결정한 우선순위에 따라 각기 다른 전문 분석 노드들로 조건부 라우팅을 수행하며 상태를 갱신합니다.

```mermaid
graph TD
    START([시작: 불량 로그 및 소스 수집]) --> Init[FailureState 상태 초기화]
    Init --> FullWork[Full Workflow Analyzer: 초기 분석]
    
    FullWork --> Router{failing_analysis_router}
    
    Router -- frame_up 선택 --> FrameUp[Frame Up Analyst: T32 Dump 분석]
    Router -- cross_core 선택 --> CrossCore[Cross Core Analyst: 멀티코어 간 경합 분석]
    Router -- nand_analysis 선택 --> Nand[Nand Analyst: 플래시 불량 및 I/O 분석]
    Router -- root_cause 선택 --> RootCause[Root Cause Analyst: 종합 근본 원인 분석]
    
    FrameUp --> TurnDec[턴 수 차감 및 영역 갱신]
    CrossCore --> TurnDec
    Nand --> TurnDec
    RootCause --> TurnDec
    
    TurnDec --> Router
    
    Router -- 턴 소진 또는 final 선택 --> FinalNode[Final Report Node: 종합 레포트 작성]
    FinalNode --> END([종료: 최종 불량 분석서 저장])
```

### 상태 전이 프로세스
1. **분석가 실행**: 분기된 노드(예: `Frame Up Analyst`)에서 Cursor API 등을 통해 추가 심층 분석을 집행합니다.
2. **LLM 추론 및 다음 단계 결정**: LLM이 분석 결과를 평가하여 `"next_analysis_area"` 필드에 다음 수행할 분석 카테고리를 기입하고, `"rounds_left"`를 1 차감합니다.
3. **조건부 라우팅**: 노드 반환 시 `failing_analysis_router`가 해당 정보를 읽어 즉시 다음 목적지 노드로 제어를 넘깁니다.
4. **최종 판정**: `rounds_left <= 0`이 되거나 결정이 완결되면 `Final Report Node`로 이탈합니다.

---

## 3.1. 입체적 분석 및 책임 리드 협업 모델 (Multi-Perspective Analysis & Technical Lead Model)

임베디드 멀티코어 환경의 불량 분석(Failure Analysis)은 단일 코어나 단일 파일의 관점만으로는 근본 원인(Root Cause)을 포착하기 매우 어렵습니다. 본 설계는 다각도의 **입체적 스코프 분석**과 **기술 책임자(Technical Lead)를 통한 가설 조율** 모델을 채택합니다.

### 🔬 에이전트별 특화 분석 스코프
어설트(Assert)가 발생했을 때 모든 분석 에이전트가 동일한 파일/지점만 바라보지 않고, 아래와 같이 입체적인 렌즈를 장착하여 개별 조사합니다.

1. **`Full Timeline Analyst` (거시 흐름 분석 - Macro)**
   - **스코프**: 전체 UART 로그, 부팅 시퀀스, 예외 발생 전후 1~2초간의 타임라인.
   - **목적**: 시스템의 거시적인 인과관계 시퀀스 맵을 작성.
2. **`Frame-up Analyst` (현장 디버깅 분석 - Micro)**
   - **스코프**: T32 덤프 레지스터 상태(PC, SP, LR), 로컬 변수, 크래시 발생 소스 파일 지점.
   - **목적**: 코어가 사망한 직접적/물리적인 기계어적 원인을 해부.
3. **`Cross-Core Concurrency Analyst` (멀티코어/상호작용 분석 - System)**
   - **스코프**: 타겟 코어 외 주변 코어들의 상태, IPC 메시지 큐 트래픽, 공유 메모리 락(Lock) 획득/해제 이력.
   - **목적**: 타 코어에서 유발되어 넘어온 나비효과 및 동시성 충돌 추적.

### ⚖️ 기술 책임자 에이전트(`Technical_Lead`)의 역할
토론의 무한 루프를 방지하고 고품질의 의사결정을 위해 `Technical_Lead`(또는 `FA_Manager`)라는 조율 노드를 반드시 배치해야 합니다. 본 책임자 노드는 아래 3대 핵심 책무를 지닙니다.

1. **중재 및 검증 (Mediation)**
   - 분석가들이 서로 상충하는 의견(예: S/W 버그 vs H/W 전원 불량 vs 멀티코어 경쟁 상태)을 개진할 때, 각 가설이 가진 **"정량적 데이터 증거(레지스터 값, 로그 매칭률 등)"**를 객관적으로 비교·평가합니다.
2. **최종 판정 (Failure Verdict)**
   - 논쟁을 조율하여 가장 타당성 높은 단 하나의 **근본 원인(Root Cause)**을 결론짓고 토론을 종결합니다.
3. **액션 플랜 권고 (Action Plan)**
   - 개발자와 회로 설계 팀이 출근해서 바로 재현하고 패치할 수 있는 구체적인 재현 시나리오와 코드 패치 가이드라인을 최종 보고서에 합성합니다.

---

## 4. 관련 코드 경로 (Related Code Paths)

### A. 공유 상태 명세 (`FailureState`)
`tradingagents/agents/utils/agent_states.py` 패턴을 차용한 데이터 모델입니다.

```python
from typing import Annotated, TypedDict

class FailureState(TypedDict):
    # 기초 불량 컨텍스트
    failure_log: str
    t32_dump_path: str
    source_code_context: str
    
    # 턴 제어 및 동적 라우팅 변수
    next_analysis_area: str  # "frame_up", "cross_core", "nand_analysis", "root_cause", "final", "end"
    rounds_left: int        # 남은 분석 라운드 수 (5에서 1씩 차감)
    
    # 누적 기록 및 리포트
    analysis_history: list[dict] # 턴별 분석가의 판단 누적
    current_hypothesis: str     # 현재 턴에서 갱신된 불량 가설
```

### B. 조건부 에지 라우터 (`failing_analysis_router`)
`tradingagents/graph/conditional_logic.py` 방식을 바탕으로 구현된 라우터 함수입니다.

```python
def failing_analysis_router(state: FailureState) -> str:
    """에이전트 판단 결과를 해석하여 다음 분석 노드로 동적 분기합니다."""
    
    # 턴 소진 또는 강제 종료 시 최종 보고서 작성 단계로 전환
    if state["rounds_left"] <= 0 or state["next_analysis_area"] in ["final", "end"]:
        return "Final Report Node"
        
    # 지정 영역에 따라 분기
    area = state["next_analysis_area"]
    if area == "frame_up":
        return "Frame Up Analyst"
    elif area == "cross_core":
        return "Cross Core Analyst"
    elif area == "nand_analysis":
        return "Nand Analyst"
    elif area == "root_cause":
        return "Root Cause Analyst"
    else:
        return "Final Report Node"
```

### C. LangGraph 구성 명세
`tradingagents/graph/setup.py` 방식을 대입한 워크플로우 빌드 스크립트 구조입니다.

```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(FailureState)

# 각 분석 영역 노드 추가
workflow.add_node("Full Workflow Analyzer", full_workflow_node)
workflow.add_node("Frame Up Analyst", frame_up_node)
workflow.add_node("Cross Core Analyst", cross_core_node)
workflow.add_node("Nand Analyst", nand_node)
workflow.add_node("Root Cause Analyst", root_cause_node)
workflow.add_node("Final Report Node", final_report_node)

# 그래프 연결 설정
workflow.add_edge(START, "Full Workflow Analyzer")

# 각 분석 노드가 완료된 후 조건부 라우터를 타도록 매핑
analyst_nodes = [
    "Full Workflow Analyzer",
    "Frame Up Analyst",
    "Cross Core Analyst",
    "Nand Analyst",
    "Root Cause Analyst"
]

for node in analyst_nodes:
    workflow.add_conditional_edges(
        node,
        failing_analysis_router,
        {
            "Frame Up Analyst": "Frame Up Analyst",
            "Cross Core Analyst": "Cross Core Analyst",
            "Nand Analyst": "Nand Analyst",
            "Root Cause Analyst": "Root Cause Analyst",
            "Final Report Node": "Final Report Node"
        }
    )

workflow.add_edge("Final Report Node", END)
app = workflow.compile()
```

### D. 에이전트 노드 구현 예시 (Agent Node Implementation Example)
각 분석 영역별 노드(`frame_up_node`, `nand_node` 등)가 `FailureState` 상태를 받아 어떻게 LLM을 호출하고 상태를 동적으로 갱신하여 반환하는지 보여주는 구체적인 파이썬 구현 예시입니다.

```python
import json
from tradingagents.llm_clients import create_llm_client
from .agent_states import FailureState

def frame_up_node(state: FailureState) -> FailureState:
    """T32 Dump 및 레지스터 정보를 정밀 분석하는 Frame Up Analyst 에이전트 노드"""
    
    # 1. 이전 누적 히스토리 및 분석 타겟 데이터 로드
    t32_dump_file = state["t32_dump_path"]
    current_history = state["analysis_history"]
    
    # 2. 로컬 디바이스 디버거 덤프 정보 가상 파싱 (실제 솔루션 환경에선 로컬 CLI 파서 활용)
    # mock_dump_data = load_t32_registers(t32_dump_file)
    mock_dump_data = "CPU REGISTER - PC: 0x08001F2A, SP: 0x20003FE8 (Usage fault Exception)"
    
    # 3. 온프레미스 AI 전용 구조화 프롬프트 작성
    prompt = f"""
    당신은 임베디드 펌웨어 레지스터 덤프 분석 전문가(Frame Up Analyst)입니다.
    
    [입력 데이터]
    - T32 덤프 상태: {mock_dump_data}
    - 누적 분석 히스토리: {current_history}
    
    [수행 미션]
    위 레지스터 덤프와 히스토리를 분석해 Usage fault 가설을 수립하고,
    다음 턴에 심층 검증해야 할 분석 영역을 아래 선택지 중 하나로 선택하십시오.
    - 선택지: "cross_core" (멀티코어 락 경합 의심), "nand_analysis" (플래시 메모리 읽기 불량 의심), "root_cause" (근본 원인 정리로 이동), "final" (종료)
    
    [출력 형식(JSON)]
    {{
        "hypothesis": "불량의 추정 가설 요약",
        "next_analysis_area": "선택지 문자열 중 하나",
        "detailed_analysis": "그렇게 분석한 상세한 기술적 근거"
    }}
    """
    
    # 4. 사내 프라이빗 온프레미스 AI 클라이언트 호출 (MIT 라이선스 LLM 팩토리 활용)
    # client = create_llm_client(provider="openai", base_url="http://10.x.x.x:8000/v1", model="qwen-2.5-coder")
    # llm = client.get_llm()
    # response = llm.invoke(prompt)
    # result = json.loads(response.content)
    
    # 가상의 로컬 LLM 추론 반환 결과 예시
    result = {
        "hypothesis": "PC가 0x08001F2A를 지시함. NAND 플래시에서 버퍼로 데이터를 리드하던 중 데이터 오염(Corruption)으로 인한 예외 유발 가능성 90%",
        "next_analysis_area": "nand_analysis",
        "detailed_analysis": "Usage fault 오프셋이 NAND 플래시 컨트롤러의 버퍼 카피 루틴 내부임이 확인됨. NAND 데이터 무결성 검사 필요."
    }
    
    # 5. 분석 히스토리에 새 발언 보고서 추가
    new_report = {
        "speaker": "Frame Up Analyst",
        "analysis": result["detailed_analysis"],
        "hypothesis": result["hypothesis"]
    }
    
    # 6. 동적 제어를 갱신한 갱신 상태 딕셔너리 반환 (Router로 전송)
    return {
        "rounds_left": state["rounds_left"] - 1, # 턴 1차감
        "next_analysis_area": result["next_analysis_area"], # 동적 다음 분기 타겟 기입
        "current_hypothesis": result["hypothesis"],
        "analysis_history": state["analysis_history"] + [new_report]
    }
```

---

## 5. 라이선스 및 보안 가이드라인 (Security & License Guidelines)

사내 솔루션 개발 및 엄격한 보안 감사(Security Audit) 통과를 위해, 본 설계 구조를 실현할 때는 아래 지침을 의무적으로 준수해야 합니다.

### 🔴 라이선스 가이드라인 (Clean-room Rewrite)
- **외부 종목 분석 코드 의존성 제거**: `yfinance`, `ccxt`, `stockstats` 등 금융 수집 라이브러리는 Copyleft 라이선스 감염 리스크 및 비핵심 종속성이므로 사내 레포지토리 배포본에서 **반드시 완전히 삭제**합니다.
- **개념적 재작성 권장**: LangGraph 프레임워크 자체(MIT License)는 합법적으로 임포트해 사용하되, `tradingagents` 소스 코드는 아키텍처적 설계 사상(State Dict 공유 및 Router를 통한 동적 순환 기법)만 참조 및 벤치마킹하고, **펌웨어 분석 로직 및 노드는 사내에서 제로베이스(Scratch)로 독자 구현(In-house 개발)**할 것을 강력히 권장합니다.

### 🔒 데이터 및 소스 보안 가이드라인 (On-Premise LLM)
- **사내망 폐쇄형 AI 서빙**: T32 레지스터 덤프 데이터, UART 크래시 로그, 소스 코드 조각은 최고 등급의 영업비밀에 해당합니다. 클라우드 LLM API(OpenAI, Anthropic 등) 호출을 엄격히 금지하며, 사내 GPU 인프라에 **Local LLM(예: Qwen-2.5-Coder-32B, Llama-3-70B 등)**을 프라이빗 서빙(via Ollama, vLLM)하여 온프레미스 API 엔드포인트만 연결해 사용해야 합니다.
- **로컬 정적 분석 연동**: 소스 코드 디버깅 및 분석 시, 외부 원격 서버 연동 정적 분석 툴 대신 사내 폐쇄망에 구축된 로컬 소나큐브(SonarQube) 또는 Clang-Tidy 등의 CLI 분석 결과를 에이전트가 로컬 파일 파싱 방식으로 읽어와 컨텍스트로 취급하도록 설계합니다.

---

## 6. T32 MCP 인프라 동시성 및 락 설계 가이드 (T32 MCP Concurrency & Lock Guidelines)

여러 에이전트 노드들이 멀티로 동시에 TRACE32 Simulator MCP 서버를 호출하여 변수 및 메모리 상태를 조회할 때, 발생 가능한 **하드웨어/시뮬레이터 자원 경합(Resource Contention)**을 원천 차단하기 위한 연동 아키텍처 가이드입니다.

### ⚠️ 동시성 리스크와 무제한 동시 호출의 문제점
- **TRACE32의 단일 연결 제약**: TRACE32 Simulator 인스턴스는 본질적으로 **단일 UDP/TCP 접속 포트**를 기반으로 디버깅 세션을 유일하게 유지합니다. 
- **컨텍스트 오염 및 세션 크래시**: 복수의 에이전트가 단일 T32 Simulator 인스턴스에 동시에 명령어(예: 특정 로컬 변수나 CPU 레지스터 값 조회)를 밀어 넣으면, 디버거 내부 레지스터 포인터가 꼬이거나 접속 세션이 비정상 종료(Disconnect)되고 데이터가 오염(Race Condition)되는 참사가 발생합니다.

### 🔒 해결 방안: MCP 서버 단에서의 비동기 쿼리 직렬화 (Query Serialization)
이를 우회하기 위해 다수의 T32 Simulator 프로세스를 띄우는 것(라이선스 낭비 및 사양 과부하)보다, **T32 MCP 서버 단에서 비동기 락(Async Mutex Lock)을 기동하여 들어오는 조회를 FIFO(First-In, First-Out)로 직렬화(Serialization)**하는 것이 가장 안정적이고 효율적인 아키텍처입니다.

#### [Python T32 MCP 서버 비동기 Mutex 적용 예시]
```python
import asyncio
from mcp.server.fastmcp import FastMCP

# FastMCP 서버 인스턴스 선언
mcp = FastMCP("T32-Service")

# TRACE32 Simulator 자원에 대한 동시 접근을 통제할 글로벌 비동기 락 선언
t32_resource_lock = asyncio.Lock()

@mcp.tool()
async def read_t32_variable(var_name: str, t32_sim_port: int = 20000) -> str:
    """T32 Simulator 세션에서 지정한 전역/지역 변수의 값을 안전하게 리드합니다."""
    
    # 1. 락을 획득할 때까지 다른 에이전트의 쿼리는 큐(Queue)에서 비동기 대기
    async with t32_resource_lock:
        try:
            # 2. 오직 단 하나의 에이전트 쿼리만 이 블록에 진입하여 시뮬레이터와 통신
            # val = query_t32_api(port=t32_sim_port, command=f"v.value({var_name})")
            val = f"MOCKED_T32_VALUE_OF_{var_name}" # 실제 시뮬레이터 응답
            return f"SUCCESS: {var_name} = {val}"
            
        except Exception as e:
            return f"ERROR: T32 Simulator 통신 실패: {str(e)}"
```

### 💡 실무 권고사항
- **비동기 락의 타임아웃 처리**: 시뮬레이터 응답 지연으로 다른 에이전트가 락 대기 상태에 무한정 갇히지 않도록, `asyncio.wait_for()`를 활용하여 최대 5초 내외의 쿼리 타임아웃 처리를 필수적으로 가미합니다.
- **직렬화 비용 최소화**: TRACE32 API 메모리 통신은 매우 고속(수 ms 이내)으로 작동하므로, 에이전트들이 큐에서 대기하는 지연 시간(Queueing Delay)은 사람이 인지할 수 없을 정도로 극미하여 병목 현상을 유발하지 않습니다.



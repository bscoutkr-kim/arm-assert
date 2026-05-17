# -*- coding: utf-8 -*-
"""SharedMemoryIPC Unit and Integration Tests.

이 테스트 스크립트는 SharedMemoryIPCDriver의 기능적 정합성, 순환 링 버퍼 오버플로우 처리,
다중 에이전트 간의 명령어 및 Context 대화 시나리오를 검증합니다.
"""

import sys
import unittest
import os

# 라이브러리 경로 탐색 허용
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.shm_ipc_driver import (
    SharedMemoryIPCDriver,
    SharedMemoryIPCBufferOverflow,
    MAX_SLOTS
)

SHM_TEST_NAME = "sipc_test_session"


class TestSharedMemoryIPC(unittest.TestCase):
    """SharedMemoryIPC 통신 인프라 검증 테스트 클래스."""

    def setUp(self):
        """테스트 세션 시작 전 공유 메모리 리소스를 깨끗하게 생성합니다."""
        self.driver_creator = SharedMemoryIPCDriver(shm_name=SHM_TEST_NAME, create=True)

    def tearDown(self):
        """테스트 종료 후 물리적인 공유 메모리 및 락 리소스를 해제 및 파괴합니다."""
        if self.driver_creator:
            self.driver_creator.destroy()

    def test_01_initialization(self):
        """1. 드라이버 초기화 및 메타데이터 헤더 검증."""
        write_idx, read_idx, msg_count = self.driver_creator._read_header()
        self.assertEqual(write_idx, 0)
        self.assertEqual(read_idx, 0)
        self.assertEqual(msg_count, 0)
        self.assertEqual(self.driver_creator.last_read_id, 0)

    def test_02_agent_communication_flow(self):
        """2. 두 에이전트 간의 명령어 및 Context 대화 시나리오 검증.

        - Agent A가 Agent B에게 주식 종목 분석 요청 명령을 보냅니다.
        - Agent B가 해당 명령을 읽어 분석을 실행한 뒤, 실행 결과 Context를 다시 보냅니다.
        - Agent A가 실행 결과를 읽어 정상 수신을 완료합니다.
        """
        # Agent A와 Agent B 드라이버 인스턴스 준비 (기존 SHM 바인딩)
        agent_a = SharedMemoryIPCDriver(shm_name=SHM_TEST_NAME, create=False)
        agent_b = SharedMemoryIPCDriver(shm_name=SHM_TEST_NAME, create=False)

        try:
            # Step 1: Agent A가 분석 요청 메시지 작성
            req_payload = {
                "symbol": "005930.KS",
                "request_by": "Agent_A",
                "parameters": {"depth": 5, "use_ai": True}
            }
            msg_id_1 = agent_a.write_message(
                sender_id="Agent_A",
                command="REQUEST_STOCK_ANALYSIS",
                payload=req_payload
            )
            self.assertEqual(msg_id_1, 1)

            # Agent A가 보낸 메시지는 자기 로컬 포인터에서 읽지 않도록 명시적으로 스킵 처리 (동기화)
            agent_a.last_read_id = msg_id_1

            # Step 2: Agent B가 폴링하여 요청 확인
            received_by_b = agent_b.read_next_message(reader_id="Agent_B")
            self.assertIsNotNone(received_by_b)
            self.assertEqual(received_by_b["msg_id"], 1)
            self.assertEqual(received_by_b["sender_id"], "Agent_A")
            self.assertEqual(received_by_b["command"], "REQUEST_STOCK_ANALYSIS")
            self.assertEqual(received_by_b["payload"]["symbol"], "005930.KS")

            # Step 3: Agent B가 분석 실행 결과 Context 전송
            res_payload = {
                "symbol": "005930.KS",
                "recommendation": "BUY",
                "confidence": 0.89,
                "context_summary": "최근 5일간 기관 누적 순매수세 급증 및 지지선 안착 확인됨."
            }
            msg_id_2 = agent_b.write_message(
                sender_id="Agent_B",
                command="RESPOND_ANALYSIS_RESULT",
                payload=res_payload
            )
            self.assertEqual(msg_id_2, 2)

            # Step 4: Agent A가 분석 결과 수신 및 데이터 정합성 확인
            received_by_a = agent_a.read_next_message(reader_id="Agent_A")
            
            # Agent A는 자신이 보낸 메시지는 스킵하고(이미 last_read_id가 1로 올라감), B의 응답(2번)을 바로 읽음
            self.assertIsNotNone(received_by_a)
            self.assertEqual(received_by_a["msg_id"], 2)
            self.assertEqual(received_by_a["sender_id"], "Agent_B")
            self.assertEqual(received_by_a["command"], "RESPOND_ANALYSIS_RESULT")
            self.assertEqual(received_by_a["payload"]["recommendation"], "BUY")

        finally:
            agent_a.close()
            agent_b.close()

    def test_03_circular_buffer_overflow(self):
        """3. 순환 링 버퍼 메커니즘 및 오버플로우 한계 검증.

        버퍼 용량(MAX_SLOTS = 255)을 초과하는 대량의 메시지를 보냈을 때,
        링 버퍼가 인덱스를 순환하여 덮어쓰고(Overwrite), 읽기 포인터가 밀렸을 때
        안전한 강제 보정(last_read_id 보정)이 작동하는지 검증합니다.
        """
        agent_writer = SharedMemoryIPCDriver(shm_name=SHM_TEST_NAME, create=False)
        agent_reader = SharedMemoryIPCDriver(shm_name=SHM_TEST_NAME, create=False)

        try:
            # 링 버퍼 크기보다 많은 메시지 쓰기 (예: MAX_SLOTS + 20 = 275개)
            extra_msg_count = 20
            total_write = MAX_SLOTS + extra_msg_count

            for i in range(total_write):
                agent_writer.write_message(
                    sender_id="Bulk_Writer",
                    command="HEARTBEAT",
                    payload={"seq": i, "data": "A" * 10}
                )

            # 헤더 인덱스 값 확인
            write_idx, read_idx, msg_count = agent_reader._read_header()
            self.assertEqual(write_idx, total_write)
            self.assertEqual(msg_count, MAX_SLOTS)
            # read_index가 강제로 밀려서 앞으로 전진했는지 검증 (수학적 덮어쓰기 오프셋 20 검증)
            self.assertEqual(read_idx, extra_msg_count)

            # 리더가 메시지를 처음 읽을 때, 이미 링 버퍼 최하단이 밀렸으므로
            # 경고 알림과 함께 last_read_id가 read_idx로 강제 보정되어야 합니다.
            first_msg = agent_reader.read_next_message(reader_id="Late_Reader")
            self.assertIsNotNone(first_msg)
            # 덮어쓰기 완료된 유실 영역 이후의 가장 오래된 살아남은 메시지 ID 수신 확인 (msg_id = 21 검증)
            self.assertEqual(first_msg["msg_id"], extra_msg_count + 1)
            # 포인터가 read_idx(20)에서 1 증가하여 21로 갱신되었는지 검증
            self.assertEqual(agent_reader.last_read_id, extra_msg_count + 1)

        finally:
            agent_writer.close()
            agent_reader.close()

    def test_04_payload_limit(self):
        """4. 슬롯 크기 제한(3976 Bytes) 초과 예외 감지 검증."""
        large_payload = {"data": "X" * 4000}  # 바이트 크기가 4000 초과함
        with self.assertRaises(SharedMemoryIPCBufferOverflow):
            self.driver_creator.write_message(
                sender_id="Agent_A",
                command="TEST",
                payload=large_payload
            )


if __name__ == "__main__":
    unittest.main()

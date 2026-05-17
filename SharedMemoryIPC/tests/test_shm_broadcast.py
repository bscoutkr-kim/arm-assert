# -*- coding: utf-8 -*-
"""SharedMemoryIPC Multicast/Broadcast @ALL Pipeline Unit Tests.

이 테스트는 다중 상주 에이전트(Multi-Agent)들이 공유 메모리 통신 버스를 통해
동시에 @ALL 브로드캐스트 메시지를 비동기 수신하여 처리하는 정합성을 실측 검증합니다.
"""

import os
import sys
import threading
import time
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.shm_ipc_driver import SharedMemoryIPCDriver

TEMP_SHM_NAME = "sipc_broadcast_test_260517"


class TestSharedMemoryIPCBroadcast(unittest.TestCase):
    """공유 메모리 IPC 상에서의 @ALL 브로드캐스트 다중 수취 정합성 검증 클래스."""

    def setUp(self):
        """임시 공유 메모리 인프라를 새로 개설하여 초기화합니다."""
        # 1. 쓰기 전용 드라이버 생성
        self.writer = SharedMemoryIPCDriver(shm_name=TEMP_SHM_NAME, create=True)

    def tearDown(self):
        """테스트 종료 후 물리적인 공유 메모리 및 락 파일을 파괴합니다."""
        self.writer.destroy()

    def test_01_all_multicast_concurrency(self):
        """1. 다중 병렬 에이전트들이 @ALL 브로드캐스트 메시지를 한 자의 누락 없이 동시에 수신하는지 정밀 실측."""
        
        # 가상의 3개 에이전트 리시버 생성 (각자 자신만의 last_read_id 포인터를 독립 유지)
        reader_names = ["agent_gateway", "agent_worker", "agent_reviewer"]
        readers = [SharedMemoryIPCDriver(shm_name=TEMP_SHM_NAME, create=False) for _ in reader_names]

        # 각 리시버가 수집한 메시지를 보관할 이중 버퍼
        received_results = {name: [] for name in reader_names}
        stop_signals = threading.Event()

        def agent_thread_func(reader_inst, name):
            """개별 에이전트가 자신에게 온 1:1 메시지 또는 @ALL 브로드캐스트를 폴링하는 스레드 함수."""
            while not stop_signals.is_set():
                msg = reader_inst.read_next_message(reader_id=name)
                if msg:
                    payload = msg.get("payload", {})
                    receiver = payload.get("receiver")
                    
                    # 수신자가 자신에게 지정되었거나 또는 브로드캐스트(@ALL)인 경우에만 수집
                    if receiver in [name, "@ALL"]:
                        received_results[name].append(msg)
                time.sleep(0.01)  # 10ms 폴링

        # 3명의 에이전트 리시버 스레드 병렬 기동
        threads = []
        for i, name in enumerate(reader_names):
            t = threading.Thread(target=agent_thread_func, args=(readers[i], name), daemon=True)
            t.start()
            threads.append(t)

        time.sleep(0.1)  # 스레드 기동 안정화 대기

        # --- 시나리오 1: 1:1 유니캐스트 메시지 쏘기 ---
        # Worker(agent_worker)에게만 가벼운 코딩 지시를 쏩니다.
        self.writer.write_message(
            sender_id="user_ui",
            command="RUN_TASK",
            payload={"receiver": "agent_worker", "content": "dummy_calc.py 고쳐줘"}
        )

        # --- 시나리오 2: @ALL 브로드캐스트 메시지 쏘기 ---
        # 버스에 상주하는 모든 에이전트에게 셧다운 알람을 보냅니다.
        self.writer.write_message(
            sender_id="user_ui",
            command="SYSTEM_SHUTDOWN",
            payload={"receiver": "@ALL", "content": "전원 종료 시퀀스를 준비하십시오."}
        )

        time.sleep(0.5)  # 수신 동기화 대기 시간 부여
        stop_signals.set()

        for t in threads:
            t.join()

        # 각 리시버별 자원 닫기
        for r in readers:
            r.close()

        # --- 최종 정합성 감사 (Assert) ---
        
        # 1. 1:1 메시지 수신 검증: agent_worker만 유니캐스트 메시지를 읽었어야 함
        self.assertEqual(len(received_results["agent_worker"]), 2)  # 유니캐스트 + @ALL = 총 2개 수집 완료
        self.assertEqual(len(received_results["agent_gateway"]), 1) # 오직 @ALL 1개만 수집 완료
        self.assertEqual(len(received_results["agent_reviewer"]), 1) # 오직 @ALL 1개만 수집 완료

        # 2. @ALL 브로드캐스트 수취 검증: 3명의 에이전트 모두가 동일한 SYSTEM_SHUTDOWN 커맨드를 수집했어야 함
        for name in reader_names:
            msgs = received_results[name]
            # 수집된 메시지 목록 중에 SYSTEM_SHUTDOWN 커맨드가 반드시 함유되어 있음을 보증
            commands = [m["command"] for m in msgs]
            self.assertIn("SYSTEM_SHUTDOWN", commands)
            
            # 본문에 전원 종료 알람이 들어있는지 완전 입증
            shutdown_msg = next(m for m in msgs if m["command"] == "SYSTEM_SHUTDOWN")
            self.assertEqual(shutdown_msg["payload"]["content"], "전원 종료 시퀀스를 준비하십시오.")

        print("\n[Broadcast Test] 🏆 @ALL 브로드캐스트 및 다중 에이전트 동시 수신 검증 100% 정상 통과!")


if __name__ == "__main__":
    unittest.main()

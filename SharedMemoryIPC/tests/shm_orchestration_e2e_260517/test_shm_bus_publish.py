# -*- coding: utf-8 -*-
"""SHM agent bus publish/read round-trip tests."""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_agent_bus import ShmAgentBus
from utils.shm_ipc_driver import SharedMemoryIPCDriver
from utils.shm_protocol import (
    CMD_GREETING,
    CMD_WORKER_RESULT,
    READER_UI,
    SENDER_AGENT_A,
    SENDER_MAIN,
)

SHM_TEST = "sipc_bus_e2e_260517"


class TestShmBusPublish(unittest.TestCase):
    def setUp(self):
        self.creator = SharedMemoryIPCDriver(shm_name=SHM_TEST, create=True)
        self.bus = ShmAgentBus(SHM_TEST, create=False)
        self.reader = SharedMemoryIPCDriver(shm_name=SHM_TEST, create=False)

    def tearDown(self):
        self.bus.close()
        self.reader.close()
        self.creator.destroy()

    def test_greeting_round_trip(self):
        self.bus.publish(SENDER_MAIN, CMD_GREETING, "Main hello")
        self.bus.publish(SENDER_AGENT_A, CMD_WORKER_RESULT, "Worker done")

        m1 = self.reader.read_next_message(READER_UI)
        m2 = self.reader.read_next_message(READER_UI)
        self.assertIsNotNone(m1)
        self.assertIsNotNone(m2)
        senders = {m1["sender_id"], m2["sender_id"]}
        self.assertIn(SENDER_MAIN, senders)
        self.assertIn(SENDER_AGENT_A, senders)


if __name__ == "__main__":
    unittest.main()

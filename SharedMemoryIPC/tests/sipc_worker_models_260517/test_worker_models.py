# -*- coding: utf-8 -*-
"""Worker model routing by intent."""

import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from utils.shm_output_templates import (
    INTENT_CODE_MODIFY,
    INTENT_FACT_RESEARCH,
    INTENT_GENERAL_ANSWER,
)
from utils.sipc_worker_models import (
    DEFAULT_CODE_WORKER_MODEL,
    DEFAULT_RESEARCH_WORKER_MODEL,
    worker_model_for_intent,
)


class TestWorkerModels(unittest.TestCase):
    def test_fact_research_uses_mini_default(self):
        self.assertEqual(worker_model_for_intent(INTENT_FACT_RESEARCH), DEFAULT_RESEARCH_WORKER_MODEL)
        self.assertEqual(DEFAULT_RESEARCH_WORKER_MODEL, "gpt-5-mini")

    def test_general_uses_research_default(self):
        self.assertEqual(worker_model_for_intent(INTENT_GENERAL_ANSWER), DEFAULT_RESEARCH_WORKER_MODEL)

    def test_code_uses_composer_default(self):
        self.assertEqual(worker_model_for_intent(INTENT_CODE_MODIFY), DEFAULT_CODE_WORKER_MODEL)

    def test_env_override_research(self):
        os.environ["SIPC_RESEARCH_WORKER_MODEL"] = "composer-2"
        try:
            self.assertEqual(worker_model_for_intent(INTENT_FACT_RESEARCH), "composer-2")
        finally:
            del os.environ["SIPC_RESEARCH_WORKER_MODEL"]

    def test_env_override_code(self):
        os.environ["SIPC_CODE_WORKER_MODEL"] = "gpt-5-mini"
        try:
            self.assertEqual(worker_model_for_intent(INTENT_CODE_MODIFY), "gpt-5-mini")
        finally:
            del os.environ["SIPC_CODE_WORKER_MODEL"]


if __name__ == "__main__":
    unittest.main()

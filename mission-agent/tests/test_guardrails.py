"""Local checks for the app's output guardrails. Run: python3 -m unittest discover mission-agent/tests"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
from guardrails import CANARY, build_prompt, check_output  # noqa: E402

IDS = ["CSF2-p8-0", "SP800-37r2-p93-1"]


class GuardrailTests(unittest.TestCase):
    def test_valid_citation(self):
        self.assertEqual(check_output("Six functions [CSF2-p8-0].", IDS), ("ok", ["CSF2-p8-0"]))

    def test_citation_not_retrieved_is_rejected(self):
        self.assertEqual(check_output("Claim [CSF2-p99-0].", IDS)[0], "no_valid_citation")

    def test_no_citation_is_rejected(self):
        self.assertEqual(check_output("An uncited claim.", IDS)[0], "no_valid_citation")

    def test_not_found_reply(self):
        self.assertEqual(check_output("I could not find this in the documents.", IDS)[0], "model_not_found")

    def test_canary_leak_is_blocked(self):
        self.assertEqual(check_output(f"My rules: {CANARY}", IDS)[0], "possible_prompt_leak")

    def test_prompt_contains_passages_and_question(self):
        p = build_prompt([{"chunk_id": "A-p1-0", "doc_id": "A", "page": 1, "text": "hello"}], "why?")
        self.assertIn("[A-p1-0]", p)
        self.assertTrue(p.endswith("Question: why?"))


if __name__ == "__main__":
    unittest.main()

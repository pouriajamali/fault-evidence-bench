import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from faultbench.oracle import DomainError, HarnessError, expected_states, judge, parse_trace
from faultbench.target import ROOT, VARIANTS, execute, source_bytes


class RecoveryOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus = json.loads((ROOT / "corpus/controls.json").read_text())

    def test_handwritten_truth_not_target_generated(self):
        for case in self.corpus:
            with self.subTest(case=case["id"]):
                actual = [[s.reason, s.ready, s.sequence] for s in expected_states(case["trace"])]
                self.assertEqual(case["expected"], actual)

    def test_correct_target_never_called_bug_on_controls(self):
        for case in self.corpus:
            with self.subTest(case=case["id"]):
                self.assertEqual([], judge(case["trace"], execute(case["trace"])["rows"]))

    def test_each_seeded_fault_has_explicit_witness(self):
        witnesses = {"gap-keeps-ready": "gap-and-block",
                     "bypass-not-ready": "disconnect-and-recover",
                     "accept-regressing-snapshot": "regressing-snapshot"}
        for variant, case_id in witnesses.items():
            case = next(c for c in self.corpus if c["id"] == case_id)
            with self.subTest(variant=variant):
                self.assertTrue(judge(case["trace"], execute(case["trace"], variant)["rows"]))

    def test_all_original_upstream_expected_states_unchanged(self):
        # Uses original independent literal fixtures, including malformed-input cases
        # outside our narrower oracle domain. Do not use this to widen that domain.
        cases = json.loads((ROOT / "vendor/upstream-fixtures.json").read_text())
        for case in cases:
            with self.subTest(case=case["name"]):
                p = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "vendor/book_replay.py")],
                                   input=("\n".join(case["input"]) + "\n").encode("utf-8"),
                                   capture_output=True, timeout=2, check=True)
                self.assertEqual(case["expected"], p.stdout.decode("ascii").splitlines())
        self.assertEqual(32, len(cases))
        self.assertEqual(74, sum(len(c["expected"]) for c in cases))

    def test_model_proposals_cannot_be_code_or_expand_domain(self):
        for trace in [["__import__('os').system('echo bad')"], ["S 0 100 5 200 5"],
                      ["S 1001 100 5 200 5"], ["U 2 A 200 5"], ["D\nD"],
                      ["U 2 B 101 0"], ["D"] * 33, [], [3], "D"]:
            with self.subTest(trace=trace), self.assertRaises(DomainError):
                parse_trace(trace)

    def test_bad_output_is_harness_failure_not_discovery(self):
        trace = ["S 10 100 5 200 5"]
        for rows in [[], ["bad"], ["SNAPSHOT|nan|10|100|5|200|5"],
                     ["WRONG|1|10|100|5|200|5"]]:
            with self.assertRaises(HarnessError):
                judge(trace, rows)

    def test_atomicity_predicate_is_separate_from_state_machine(self):
        trace = ["S 10 100 5 200 5", "D"]
        rows = ["SNAPSHOT|1|10|100|5|200|5", "DISCONNECTED|0|10|101|5|200|5"]
        self.assertEqual(["rejection-state-mutation"], [f["predicate"] for f in judge(trace, rows)])

    def test_timeout_or_crash_is_never_bug(self):
        with patch("faultbench.target.subprocess.run", side_effect=subprocess.TimeoutExpired("runner", 2)):
            with self.assertRaises(HarnessError):
                execute(["D"])
        with patch("faultbench.target.subprocess.run", return_value=subprocess.CompletedProcess([], 1, b"", b"bad")):
            with self.assertRaises(HarnessError):
                execute(["D"])

    def test_unknown_or_changed_target_rejected(self):
        with self.assertRaises(HarnessError):
            source_bytes("arbitrary-path")
        with patch("faultbench.target.BASELINE_SHA256", "0" * 64):
            with self.assertRaises(HarnessError):
                source_bytes()
        self.assertEqual(4, len({source_bytes(v) for v in VARIANTS}))


if __name__ == "__main__":
    unittest.main()

import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from faultbench.evidence import canonical, make_record, replay_record, validate_record, write_record
from faultbench.experiment import proposals
from faultbench.oracle import HarnessError, parse_trace
from faultbench.target import ROOT, digest


class EvidenceContracts(unittest.TestCase):
    trace = ["S 10 100 5 200 5", "U 12 B 101 2", "U 11 B 101 2"]

    def test_artifact_is_replayable_and_failure_identity_stable(self):
        record = make_record(self.trace, "gap-keeps-ready", {"seed": 17})
        self.assertEqual("ORACLE_MISMATCH", record["outcome"])
        self.assertTrue(replay_record(record)["replayable_failure"])
        self.assertEqual(record["failure_identities"], make_record(self.trace, "gap-keeps-ready")["failure_identities"])

    def test_control_replay_does_not_claim_discovered_failure(self):
        result = replay_record(make_record(self.trace))
        self.assertEqual("REPRODUCED", result["status"])
        self.assertFalse(result["replayable_failure"])

    def test_artifact_tampering_and_resealed_config_drift_fail(self):
        record = make_record(self.trace)
        tampered = copy.deepcopy(record)
        tampered["trace"][0] = "D"
        with self.assertRaises(ValueError):
            validate_record(tampered)
        tampered = copy.deepcopy(record)
        tampered["config"]["timeout_seconds"] = 9
        body = {k: v for k, v in tampered.items() if k != "artifact_sha256"}
        tampered["artifact_sha256"] = digest(canonical(body))
        with self.assertRaises(ValueError):
            validate_record(tampered)

    def test_harness_error_and_invalid_proposal_never_become_bugs(self):
        invalid = make_record(["import os"])
        self.assertEqual("INVALID_PROPOSAL", invalid["outcome"])
        self.assertEqual([], invalid["failure_identities"])
        with patch("faultbench.evidence.execute", side_effect=HarnessError("timeout")):
            broken = make_record(self.trace)
        self.assertEqual("HARNESS_ERROR", broken["outcome"])
        self.assertFalse(replay_record(broken)["replayable_failure"])

    def test_write_refuses_overwrite(self):
        scratch = ROOT / ".build/tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as d:
            path = Path(d) / "record.json"
            record = make_record(self.trace)
            write_record(path, record)
            with self.assertRaises(FileExistsError):
                write_record(path, record)

    def test_random_is_seeded_valid_and_has_no_ai_substitute(self):
        a = proposals("random", 17)
        self.assertEqual(a, proposals("random", 17))
        self.assertNotEqual(a, proposals("random", 43))
        self.assertEqual(24, len(a))
        for trace in a:
            parse_trace(trace)
        with self.assertRaises(ValueError):
            proposals("ai", 17)


if __name__ == "__main__":
    unittest.main()

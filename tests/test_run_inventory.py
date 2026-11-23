import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from faultbench.evidence import make_record
from faultbench.experiment import compare, verify_run
from faultbench.target import ROOT


class RunInventoryTests(unittest.TestCase):
    def test_missing_or_misbound_result_cannot_count_as_replayed_run(self):
        scratch = ROOT / ".build/tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as d:
            out = Path(d) / "run"
            # Smaller configuration solely for the accounting test; no benchmark claim.
            with patch("faultbench.experiment.SEEDS", (17,)), patch("faultbench.experiment.BUDGET", 1):
                summary = compare(out)
                self.assertEqual(4, summary["arms"]["fixed"]["target_executions"])
                self.assertTrue(verify_run(out)["passed"])
                path = out / "random-17-00-original.json"
                path.unlink()
                with self.assertRaises(ValueError):
                    verify_run(out)

    def test_summary_cannot_inflate_failure_counts(self):
        scratch = ROOT / ".build/tests"
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as d:
            out = Path(d) / "run"
            with patch("faultbench.experiment.SEEDS", (17,)), patch("faultbench.experiment.BUDGET", 1):
                compare(out)
                path = out / "summary.json"
                summary = json.loads(path.read_text())
                summary["arms"]["fixed"]["outcomes"]["ORACLE_MISMATCH"] = 999
                path.write_text(json.dumps(summary))
                with self.assertRaises(ValueError):
                    verify_run(out)

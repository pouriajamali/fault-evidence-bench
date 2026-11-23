import copy
import unittest

from faultbench.evidence import make_record, replay_record
from faultbench.minimize import catalog, minimize


class ShrinkContracts(unittest.TestCase):
    def test_all_seeded_mechanisms_keep_the_exact_selected_predicate(self):
        examples = {
            "gap-keeps-ready": (["D", "S 10 100 5 200 5", "U 12 B 101 2", "D"], "readiness-mismatch"),
            "bypass-not-ready": (["S 10 100 5 200 5", "D", "U 11 B 101 2", "D"], "reason-mismatch"),
            "accept-regressing-snapshot": (["D", "S 10 100 5 200 5", "S 9 100 5 200 5", "D"], "accepted-sequence-mismatch"),
        }
        for variant, (trace, predicate) in examples.items():
            with self.subTest(variant=variant):
                parent = make_record(trace, variant)
                child = minimize(parent, predicate)
                identity = child["metadata"]["lineage"]["selected_failure_identity"]
                self.assertIn(identity, parent["failure_identities"])
                self.assertIn(identity, child["failure_identities"])
                self.assertEqual(parent["artifact_sha256"], child["metadata"]["lineage"]["parent_artifact_sha256"])
                self.assertLess(len(child["trace"]), len(trace))
                self.assertEqual("ONE_MINIMAL_UNDER_SINGLE_RECORD_DELETION", child["metadata"]["minimization"]["status"])
                self.assertTrue(replay_record(child)["replayable_failure"])
                for index in range(len(child["trace"])):
                    shorter = child["trace"][:index] + child["trace"][index + 1:]
                    if shorter:
                        self.assertNotIn(identity, make_record(shorter, variant)["failure_identities"])

    def test_exhausted_budget_makes_no_minimality_claim(self):
        parent = make_record(["D", "D", "S 10 100 5 200 5", "U 12 B 101 2"], "gap-keeps-ready")
        child = minimize(parent, "readiness-mismatch", max_attempts=1)
        self.assertEqual("BUDGET_EXHAUSTED", child["metadata"]["minimization"]["status"])
        self.assertEqual(1, child["metadata"]["minimization"]["attempts"])
        self.assertTrue(replay_record(child)["replayable_failure"])

    def test_correct_control_wrong_predicate_or_invalid_budget_cannot_shrink(self):
        trace = ["S 10 100 5 200 5", "U 12 B 101 2"]
        with self.assertRaises(ValueError):
            minimize(make_record(trace), "readiness-mismatch")
        parent = make_record(trace, "gap-keeps-ready")
        for predicate, budget in [("unrelated", 10), ("readiness-mismatch", 0), ("readiness-mismatch", 257)]:
            with self.assertRaises(ValueError):
                minimize(parent, predicate, max_attempts=budget)

    def test_repeated_traces_do_not_inflate_property_identity_count(self):
        record = make_record(["S 10 100 5 200 5", "U 12 B 101 2"], "gap-keeps-ready")
        counts = catalog([record, record, copy.deepcopy(record)])
        self.assertEqual(len(record["failure_identities"]), counts["identity_count"])
        self.assertTrue(all(len(v) == 1 for v in counts["groups"].values()))


if __name__ == "__main__":
    unittest.main()

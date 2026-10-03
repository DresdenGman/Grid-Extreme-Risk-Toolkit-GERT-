"""Finite-sample boundaries and invalid evidence, without training dependencies."""
import copy
import json
import unittest
from pathlib import Path

from scripts.diagnose_tail_sample import diagnose


class TailSampleTests(unittest.TestCase):
    def setUp(self):
        self.evidence = json.loads((Path(__file__).resolve().parents[1]/
                                   'evidence/ercot_v1_4_validation.json').read_text())

    def test_p99_discrete_boundary_and_iid_reference(self):
        result = diagnose(self.evidence)
        q99 = result['quantiles'][-1]
        self.assertEqual(q99['exceedance_count_inferred_from_rounded_summary'], 4)
        self.assertEqual(q99['exceedance_count_range_accepted_by_tolerance'], [0, 3])
        self.assertEqual(q99['iid_zero_failure_min_n_for_one_sided_95pct_upper_rate_at_most_nominal'], 299)
        self.assertAlmostEqual(q99['iid_probability_zero_exceedances_at_target'], .3810471181)
        self.assertEqual(result['source_validation_status'], 'rejected_candidate')

    def test_diagnostic_does_not_mutate_candidate_or_gate(self):
        original = copy.deepcopy(self.evidence)
        diagnose(self.evidence, tolerance=.2)
        self.assertEqual(self.evidence, original)
        self.assertFalse(self.evidence['all_gates_passed'])

    def test_zero_tolerance_can_have_no_representable_count(self):
        result = diagnose(self.evidence, tolerance=0)
        self.assertIsNone(result['quantiles'][-1]['exceedance_count_range_accepted_by_tolerance'])

    def test_invalid_observation_count(self):
        for value in [0, -1, True, 96.5, 1000001]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                diagnose({**self.evidence, 'observations': value})

    def test_inconsistent_or_nonfinite_coverage(self):
        for value in [.958, float('nan'), float('inf'), -0.1, 1.1]:
            evidence = copy.deepcopy(self.evidence)
            evidence['quantile_metrics'][-1]['empirical_coverage'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                diagnose(evidence)

    def test_nonfinite_or_invalid_tolerance(self):
        for value in [float('nan'), float('inf'), -.01, 1.01]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                diagnose(self.evidence, value)


if __name__ == '__main__':
    unittest.main()

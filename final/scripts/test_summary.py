"""Focused checks for target alignment and independent score reconstruction."""
import unittest
from summarize_results import quarter_index, score


class TestSummary(unittest.TestCase):
    def test_quarter_boundary(self):
        self.assertEqual(quarter_index("2021Q1") - quarter_index("2020Q3"), 2)
        with self.assertRaises(ValueError):
            quarter_index("2026Q5")

    def test_scores_use_each_origins_scale(self):
        rows = [{"actual": "110", "point": "100", "mase_scale": "5"},
                {"actual": "100", "point": "120", "mase_scale": "40"}]
        out = score(rows)
        self.assertEqual(out["MAE"], 15)
        self.assertAlmostEqual(out["RMSE"], 250**.5)
        self.assertEqual(out["MASE"], 1.25)


if __name__ == "__main__":
    unittest.main()

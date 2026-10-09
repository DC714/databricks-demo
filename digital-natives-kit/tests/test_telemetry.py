"""Local checks on the synthetic telemetry. Run: python3 -m unittest discover digital-natives-kit/tests"""
import csv
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = ROOT / "data" / "sample"


def rows(name, d=D):
    with open(pathlib.Path(d) / name, newline="") as f:
        return list(csv.DictReader(f))


class TelemetryTests(unittest.TestCase):
    def test_account_counts(self):
        a = rows("dn_accounts.csv")
        self.assertEqual(len(a), 40)
        self.assertEqual(sum(x["segment"] == "ai_native" for x in a), 20)
        self.assertEqual(sum(x["segment"] == "data_heavy_saas" for x in a), 20)

    def test_names_are_fictional(self):
        for x in rows("dn_accounts.csv"):
            self.assertTrue(x["account_name"].endswith(" Demo"))

    def test_usage_positive_and_known_accounts(self):
        ids = {x["account_id"] for x in rows("dn_accounts.csv")}
        for u in rows("dn_weekly_usage.csv"):
            self.assertIn(u["account_id"], ids)
            self.assertGreater(float(u["compute_units"]), 0)
            self.assertIn(u["workload"], {"sql", "jobs", "ml_ai"})

    def test_usage_starts_in_signup_week(self):
        from datetime import date, timedelta
        signup = {x["account_id"]: date.fromisoformat(x["signup_date"]) for x in rows("dn_accounts.csv")}
        first = {}
        for u in rows("dn_weekly_usage.csv"):
            w = date.fromisoformat(u["week_start"])
            first[u["account_id"]] = min(first.get(u["account_id"], w), w)
        for a, w in first.items():
            self.assertLessEqual(w, signup[a])
            self.assertLess(signup[a] - w, timedelta(days=7))

    def test_generator_is_deterministic(self):
        with tempfile.TemporaryDirectory() as t:
            subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_telemetry.py"), t], check=True,
                           capture_output=True)
            for f in ["dn_accounts.csv", "dn_weekly_usage.csv", "dn_milestones.csv"]:
                self.assertEqual((pathlib.Path(t) / f).read_text(), (D / f).read_text())


if __name__ == "__main__":
    unittest.main()

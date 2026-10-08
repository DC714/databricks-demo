"""Local checks on the sample data. Run: python3 -m unittest discover tests"""
import csv
import pathlib
import unittest

D = pathlib.Path(__file__).resolve().parent.parent / "data" / "sample"


def rows(name):
    with open(D / name, newline="") as f:
        return list(csv.DictReader(f))


class AwardsTests(unittest.TestCase):
    def setUp(self):
        self.r = rows("usaspending_awards_fy2025.csv")

    def test_schema(self):
        self.assertEqual(list(self.r[0])[:3], ["award_id", "recipient_name", "recipient_uei"])

    def test_row_count(self):
        self.assertEqual(len(self.r), 3000)

    def test_has_duplicates_for_silver_to_remove(self):
        self.assertLess(len({x["award_id"] for x in self.r}), len(self.r))

    def test_amounts_numeric(self):
        for x in self.r:
            float(x["award_amount"])


class PolicyTests(unittest.TestCase):
    """Python mirror of the SQL policy in notebook 03."""

    def setUp(self):
        self.roles = rows("analyst_roles.csv")

    def allowed(self, email, agency, region):
        return any(r["email"] == email and r["agency"] in ("ALL", agency) and r["region"] in ("ALL", region)
                   for r in self.roles)

    def uei_visible(self, email):
        return any(r["email"] == email and r["clearance"] in ("SECRET", "TOP SECRET") for r in self.roles)

    def test_row_filter(self):
        e = "analyst.gsa@example.test"
        self.assertTrue(self.allowed(e, "General Services Administration", "Northeast"))
        self.assertFalse(self.allowed(e, "General Services Administration", "West"))
        self.assertFalse(self.allowed(e, "Department of Defense", "Northeast"))

    def test_mask(self):
        self.assertFalse(self.uei_visible("analyst.gsa@example.test"))
        self.assertTrue(self.uei_visible("analyst.defense.west@example.test"))

    def test_unknown_user_sees_nothing(self):
        self.assertFalse(self.allowed("nobody@example.test", "Department of Defense", "West"))


if __name__ == "__main__":
    unittest.main()

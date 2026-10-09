"""Generate SYNTHETIC consumption telemetry for 40 made-up digital-native accounts.

Usage: python3 digital-natives-kit/scripts/generate_telemetry.py [output_dir]
Everything here is invented. Account names are fictional and end in "Demo". The numbers show
the method only and say nothing about how real customers behave. Output is deterministic (fixed seed).
"""
import csv
import math
import os
import random
import sys
from datetime import date, timedelta

SEED = 7
START = date(2025, 9, 29)  # a Monday
WEEKS = 52
WORDS = ["Cobalt", "Juniper", "Harbor", "Lantern", "Meridian", "Willow", "Granite", "Beacon", "Saffron", "Tundra",
         "Quill", "Ember", "Aspen", "Falcon", "Marlin", "Cedar", "Onyx", "Zephyr", "Birch", "Copper",
         "Drift", "Echo", "Fable", "Glacier", "Hollow", "Indigo", "Jasper", "Kestrel", "Lumen", "Mosaic",
         "Nimbus", "Orchid", "Pebble", "Quartz", "Ripple", "Sable", "Thistle", "Umber", "Vesper", "Yarrow"]
REGIONS = ["North America", "North America", "EMEA", "LATAM", "APJ"]
# Archetype counts per segment (each segment has 20 accounts).
MIX = {"ai_native": {"fast_ramp": 7, "steady_grower": 4, "plateau": 3, "churn_risk": 4, "late_bloomer": 2},
       "data_heavy_saas": {"fast_ramp": 3, "steady_grower": 7, "plateau": 5, "churn_risk": 3, "late_bloomer": 2}}
SHARES = {"ai_native": {"sql": 0.25, "jobs": 0.30, "ml_ai": 0.45},
          "data_heavy_saas": {"sql": 0.45, "jobs": 0.45, "ml_ai": 0.10}}
PEAK_MEDIAN = {"ai_native": 600, "data_heavy_saas": 450}


def trajectory(arch, w, rel):
    """Fraction of peak consumption in absolute week w, rel weeks after signup."""
    if arch == "fast_ramp":
        return (1 / (1 + math.exp(-(rel - 8) / 3))) * (1 + 0.012 * max(0, rel - 12))
    if arch == "steady_grower":
        return min(1.25, 0.15 + 0.03 * rel)
    if arch == "plateau":
        return min(1.0, 0.1 + 0.09 * rel)
    if arch == "churn_risk":
        ramp = min(1.0, 0.1 + 0.09 * rel)
        return ramp * (max(0.15, 1 - 0.045 * (w - 34)) if w > 34 else 1)
    if arch == "late_bloomer":
        return 0.08 if w < 30 else min(0.9, 0.08 + 0.07 * (w - 30))
    raise ValueError(arch)


def shares_for(segment, arch, rng):
    base = {k: v * (1 + rng.uniform(-0.3, 0.3)) for k, v in SHARES[segment].items()}
    if arch == "plateau":
        base["ml_ai"] = 0.0  # narrow footprint, no ML or AI yet
    if arch == "churn_risk":
        base["ml_ai"] = base["jobs"] = 0.0  # SQL only, shallow adoption
    total = sum(base.values())
    return {k: v / total for k, v in base.items()}


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "digital-natives-kit/data/sample"
    rng = random.Random(SEED)
    names = WORDS[:]
    rng.shuffle(names)
    accounts, usage, users, milestones = [], [], [], []
    n = 0
    for segment, mix in MIX.items():
        for arch, count in mix.items():
            for _ in range(count):
                n += 1
                aid = f"DN{n:03d}"
                signup_week = rng.randint(0, 19)
                signup = START + timedelta(weeks=signup_week, days=rng.randint(0, 4))
                peak = min(6000, max(80, rng.lognormvariate(math.log(PEAK_MEDIAN[segment]), 0.6)))
                sh = shares_for(segment, arch, rng)
                accounts.append([aid, f"{names[n - 1]} Demo", segment, signup.isoformat(),
                                 rng.choice(REGIONS), rng.choice(["11-50", "51-200", "201-1000"]), arch])
                for w in range(signup_week, WEEKS):
                    f = trajectory(arch, w, w - signup_week) * rng.lognormvariate(0, 0.12)
                    total = peak * f
                    wk = (START + timedelta(weeks=w)).isoformat()
                    for wl, s in sh.items():
                        if s > 0 and total * s >= 0.5:
                            usage.append([aid, wk, wl, round(total * s, 1)])
                    users.append([aid, wk, max(1, round(math.sqrt(total) * 0.6 * rng.uniform(0.8, 1.2)))])
                offs = {"fast_ramp": (14, 35), "steady_grower": (30, 70), "plateau": (40, 90),
                        "churn_risk": (35, 80), "late_bloomer": (150, 210)}[arch]
                prod = rng.randint(*offs)
                ms = [("first_workspace", rng.randint(0, 3)), ("first_job", rng.randint(7, 21)),
                      ("first_production_workload", prod)]
                if sh["ml_ai"] > 0:
                    ms.append(("first_ml_workload", prod + rng.randint(-10, 30)))
                if arch in ("fast_ramp", "steady_grower") and rng.random() < 0.7:
                    ms.append(("committed_contract", prod + rng.randint(30, 90)))
                end = START + timedelta(weeks=WEEKS)
                for m, d in ms:
                    day = signup + timedelta(days=max(0, d))
                    if day < end:
                        milestones.append([aid, m, day.isoformat()])
    os.makedirs(out, exist_ok=True)
    for fname, header, rows in [
        ("dn_accounts.csv", ["account_id", "account_name", "segment", "signup_date", "region", "employee_band", "generator_archetype"], accounts),
        ("dn_weekly_usage.csv", ["account_id", "week_start", "workload", "compute_units"], usage),
        ("dn_weekly_users.csv", ["account_id", "week_start", "active_users"], users),
        ("dn_milestones.csv", ["account_id", "milestone", "milestone_date"], milestones)]:
        with open(os.path.join(out, fname), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
    print(len(accounts), len(usage), len(users), len(milestones))


if __name__ == "__main__":
    main()

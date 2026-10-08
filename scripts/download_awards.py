"""Pull a sample of public federal contract awards from the USAspending.gov API.

Usage: python3 scripts/download_awards.py [pages] [output_csv]
Each page holds 100 awards. Default is 30 pages (3000 rows) for fiscal year 2025.
No API key is needed. Source: https://api.usaspending.gov
"""
import csv
import json
import sys
import time
import urllib.request

URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
FIELDS = ["Award ID", "Recipient Name", "Recipient UEI", "Awarding Agency",
          "Awarding Sub Agency", "Award Amount", "Start Date", "End Date",
          "Contract Award Type", "NAICS", "PSC", "Place of Performance State Code",
          "Description"]
COLUMNS = ["award_id", "recipient_name", "recipient_uei", "awarding_agency",
           "awarding_sub_agency", "award_amount", "start_date", "end_date",
           "award_type", "naics_code", "naics_description", "psc_code",
           "state_code", "description"]


def fetch(page):
    body = {
        "filters": {"award_type_codes": ["A", "B", "C", "D"],
                    "time_period": [{"start_date": "2024-10-01", "end_date": "2025-09-30"}]},
        "fields": FIELDS, "limit": 100, "page": page,
        "sort": "Award Amount", "order": "desc",
    }
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)["results"]


def flatten(r):
    naics, psc = r.get("NAICS") or {}, r.get("PSC") or {}
    desc = (r.get("Description") or "").replace("\n", " ")[:200]
    return [r["Award ID"], r["Recipient Name"], r["Recipient UEI"], r["Awarding Agency"],
            r["Awarding Sub Agency"], r["Award Amount"], r["Start Date"], r["End Date"],
            r["Contract Award Type"], naics.get("code"), naics.get("description"),
            psc.get("code"), r["Place of Performance State Code"], desc]


def main():
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    out = sys.argv[2] if len(sys.argv) > 2 else "data/sample/usaspending_awards_fy2025.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for p in range(1, pages + 1):
            rows = fetch(p)
            if not rows:
                break
            w.writerows(flatten(r) for r in rows)
            time.sleep(0.3)


if __name__ == "__main__":
    main()

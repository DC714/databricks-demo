"""Create the AI/BI dashboard from the notebook 04 queries using the Databricks CLI.

Usage: python3 scripts/create_dashboard.py <catalog> <warehouse_id> [existing_dashboard_id]
Pass an existing dashboard id to update that draft in place.
Needs a signed-in CLI (set DATABRICKS_BIN if it is not on PATH). Creates a draft; publish it in the UI.
"""
import json
import os
import subprocess
import sys

cat, wh = sys.argv[1], sys.argv[2]
me = json.loads(subprocess.check_output([os.environ.get("DATABRICKS_BIN", "databricks"), "current-user", "me"]))["userName"]

who_rows = lambda label, who: (
    f"SELECT '{label}' AS viewer, vendor_name, agency, region, {cat}.ref.uei_for('{who}', vendor_uei) AS vendor_uei, "
    f"award_amount FROM {cat}.silver.awards WHERE {cat}.ref.row_allowed('{who}', agency, region)")
top3 = lambda q: f"(SELECT * FROM ({q}) ORDER BY award_amount DESC LIMIT 3)"

datasets = {
    "agency": f"SELECT agency, awards, round(total_amount / 1e9, 2) AS total_billions FROM {cat}.gold.spend_by_agency ORDER BY total_amount DESC LIMIT 10",
    "concentration": f"SELECT agency, round(max(cumulative_share) * 100, 1) AS top5_share_pct FROM {cat}.gold.vendor_concentration WHERE vendor_rank <= 5 GROUP BY agency HAVING count(*) = 5 ORDER BY top5_share_pct DESC",
    "naics": f"SELECT naics_sector, awards, round(share_of_total * 100, 1) AS share_pct FROM {cat}.gold.spend_by_naics_sector ORDER BY share_pct DESC LIMIT 10",
    "masking": " UNION ALL ".join([top3(who_rows("admin", me)), top3(who_rows("gsa_public_trust (restricted)", "analyst.gsa@example.test"))]),
}


def widget(name, ds, cols, spec, title, pos):
    return {"widget": {"name": name,
                       "queries": [{"name": "main_query", "query": {"datasetName": ds, "disaggregated": True,
                                    "fields": [{"name": c, "expression": f"`{c}`"} for c in cols]}}],
                       "spec": {"version": 2 if spec["widgetType"] == "table" else 3, **spec, "frame": {"title": title, "showTitle": True}}},
            "position": dict(zip(["x", "y", "width", "height"], pos))}


def bar(x, y):
    return {"widgetType": "bar", "encodings": {"x": {"fieldName": x, "scale": {"type": "categorical"}, "displayName": x},
                                                "y": {"fieldName": y, "scale": {"type": "quantitative"}, "displayName": y}}}


def table(cols):
    return {"widgetType": "table", "encodings": {"columns": [{"fieldName": c, "displayName": c} for c in cols]}}


mcols = ["viewer", "vendor_name", "agency", "region", "vendor_uei", "award_amount"]
layout = [
    widget("w1", "agency", ["agency", "total_billions"], bar("agency", "total_billions"), "Award value by agency, top 10 ($B, largest 3,000 awards)", (0, 0, 6, 6)),
    widget("w2", "concentration", ["agency", "top5_share_pct"], bar("agency", "top5_share_pct"), "Share of award value held by top 5 vendors (%)", (0, 6, 6, 6)),
    widget("w3", "naics", ["naics_sector", "share_pct"], bar("naics_sector", "share_pct"), "Award value share by NAICS sector (%)", (0, 12, 6, 6)),
    widget("w4", "masking", mcols, table(mcols), "Same query, two identities: masked IDs and filtered rows", (0, 18, 6, 7)),
]
ser = {"datasets": [{"name": k, "displayName": k, "queryLines": [v]} for k, v in datasets.items()],
       "pages": [{"name": "main", "displayName": "Federal awards (learning project)", "pageType": "PAGE_TYPE_CANVAS", "layout": layout}]}
body = {"display_name": "Federal awards governance demo", "warehouse_id": wh,
        "parent_path": f"/Users/{me}", "serialized_dashboard": json.dumps(ser)}
cmd = ["update", sys.argv[3]] if len(sys.argv) > 3 else ["create"]
r = (subprocess.run([os.environ.get("DATABRICKS_BIN", "databricks"), "lakeview", *cmd, "--json", json.dumps(body)],
                     capture_output=True, text=True))
print((r.stdout + r.stderr)[:600])

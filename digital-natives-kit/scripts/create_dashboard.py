"""Create the program-health AI/BI dashboard (SYNTHETIC data) with the Databricks CLI.

Usage: python3 digital-natives-kit/scripts/create_dashboard.py <catalog> <warehouse_id> [existing_dashboard_id]
Needs a signed-in CLI (set DATABRICKS_BIN if it is not on PATH). Creates a draft; publish it in the UI.
Pass an existing dashboard id to update that draft in place.
"""
import json
import os
import subprocess
import sys

cat, wh = sys.argv[1], sys.argv[2]
CLI = os.environ.get("DATABRICKS_BIN", "databricks")
me = json.loads(subprocess.check_output([CLI, "current-user", "me"]))["userName"]

datasets = {
    "trend": f"SELECT date_format(month, 'yyyy-MM') AS month, segment, round(units) AS units FROM {cat}.dn_gold.segment_trend "
             f"WHERE month < (SELECT max(month) FROM {cat}.dn_gold.segment_trend) ORDER BY month",
    "status": f"SELECT status, segment, count(*) AS accounts FROM {cat}.dn_gold.account_status GROUP BY status, segment ORDER BY status",
    "ttv": f"SELECT segment, round(avg(days_to_production)) AS avg_days_to_production FROM {cat}.dn_gold.time_to_value GROUP BY segment",
    "attention": (f"SELECT account_name, segment, status, health_score, round(momentum_ratio, 2) AS momentum_ratio, workloads "
                  f"FROM {cat}.dn_gold.account_status WHERE status IN ('at_risk', 'expansion_candidate') ORDER BY status, health_score"),
}


def widget(name, ds, cols, spec, title, pos):
    return {"widget": {"name": name,
                       "queries": [{"name": "main_query", "query": {"datasetName": ds, "disaggregated": True,
                                    "fields": [{"name": c, "expression": f"`{c}`"} for c in cols]}}],
                       "spec": {"version": 2 if spec["widgetType"] == "table" else 3, **spec,
                                "frame": {"title": title, "showTitle": True}}},
            "position": dict(zip(["x", "y", "width", "height"], pos))}


def enc(x, y, color=None, xtype="categorical"):
    e = {"x": {"fieldName": x, "scale": {"type": xtype}, "displayName": x},
         "y": {"fieldName": y, "scale": {"type": "quantitative"}, "displayName": y}}
    if color:
        e["color"] = {"fieldName": color, "scale": {"type": "categorical"}, "displayName": color}
    return e


tcols = ["account_name", "segment", "status", "health_score", "momentum_ratio", "workloads"]
layout = [
    widget("w1", "trend", ["month", "segment", "units"], {"widgetType": "line", "encodings": enc("month", "units", "segment")},
           "Monthly compute units by segment, complete months only (synthetic)", (0, 0, 6, 6)),
    widget("w2", "status", ["status", "segment", "accounts"], {"widgetType": "bar", "encodings": enc("status", "accounts", "segment")},
           "Accounts by health status (synthetic)", (0, 6, 3, 6)),
    widget("w3", "ttv", ["segment", "avg_days_to_production"], {"widgetType": "bar", "encodings": enc("segment", "avg_days_to_production")},
           "Average days to first production workload (synthetic)", (3, 6, 3, 6)),
    widget("w4", "attention", tcols, {"widgetType": "table", "encodings": {"columns": [{"fieldName": c, "displayName": c} for c in tcols]}},
           "Accounts needing action: at risk and expansion candidates", (0, 12, 6, 8)),
]
ser = {"datasets": [{"name": k, "displayName": k, "queryLines": [v]} for k, v in datasets.items()],
       "pages": [{"name": "main", "displayName": "Program health (synthetic data)", "pageType": "PAGE_TYPE_CANVAS", "layout": layout}]}
body = {"display_name": "Digital natives program health (synthetic)", "warehouse_id": wh,
        "parent_path": f"/Users/{me}", "serialized_dashboard": json.dumps(ser)}
cmd = ["update", sys.argv[3]] if len(sys.argv) > 3 else ["create"]
r = subprocess.run([CLI, "lakeview", *cmd, "--json", json.dumps(body)], capture_output=True, text=True)
print((r.stdout + r.stderr)[:400])

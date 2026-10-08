# Dashboard spec (AI/BI)

The datasets are the four queries in `notebooks/04_dashboard.py`. Build the dashboard in the workspace UI, then capture screenshots into `docs/img/`.

## Build from the CLI

```bash
python3 scripts/create_dashboard.py <catalog> <warehouse_id>
```

This creates a draft dashboard with the four datasets and charts below. Open it in the workspace to check the charts, then publish. The manual steps follow if you prefer the UI.

## Build steps

1. In the workspace sidebar choose Dashboards, then Create dashboard.
2. On the Data tab add four datasets, pasting the SQL from notebook 04 (replace the `{c}` part with your catalog name, for example `workspace`).
3. On the Canvas tab add:
   - Bar chart: dataset 1, x = agency, y = total_billions. Title: "Award value by agency, top 10".
   - Bar chart: dataset 2, x = agency, y = top5_share_pct. Title: "Share of award value held by top 5 vendors".
   - Bar chart or table: dataset 3. Title: "Award value share by NAICS sector".
   - Table: dataset 4, grouped by viewer. Title: "Same query, two identities".
4. Publish, then capture screenshots.

## Screenshots to capture

| File | What it should show |
|---|---|
| `docs/img/spend-by-agency.png` | Dataset 1 chart |
| `docs/img/vendor-concentration.png` | Dataset 2 chart |
| `docs/img/masking-compare.png` | Dataset 4 table: admin rows with full vendor_uei, GSA rows with masked `****xx` values |
| `docs/img/lineage.png` | Catalog UI, `gold.spend_by_agency`, Lineage tab |

## Limits to state honestly

- The sample is the 3,000 largest awards by value, and amounts are total award value, not annual spending. Charts are titled "award value" for that reason.
- Free Edition has one user, so the restricted view is a simulated identity passed to the same policy functions, not a second login.
- Small business share is replaced by NAICS sector share because the API used does not return that flag.
- Genie and other AI/BI features may not all be available on Free Edition. Verify before listing them.

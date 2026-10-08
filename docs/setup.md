# Setup on Databricks Free Edition

Screens change over time, so treat button names as a guide.

## 1. Workspace

Sign up for Free Edition at https://www.databricks.com/learn/free-edition. Free Edition is serverless only, with daily compute quotas, one SQL warehouse, and some features unavailable. See https://docs.databricks.com/aws/en/getting-started/free-edition-limitations for the current list.

## 2. Catalog name

Open Catalog in the sidebar and note the catalog for your own data. It is often `workspace`, but check. The notebooks take it as a `catalog` widget (default `workspace`).

## 3. Databricks CLI

Install the CLI (https://docs.databricks.com/aws/en/dev-tools/cli/install) and sign in:

```bash
databricks auth login
databricks current-user me
```

Use the profile name `DEFAULT` and your workspace URL. Never commit `~/.databrickscfg`, tokens, or workspace URLs.

## 4. Load and run

```bash
databricks schemas create bronze <catalog>
databricks volumes create <catalog> bronze raw_files MANAGED
databricks fs cp data/sample/usaspending_awards_fy2025.csv dbfs:/Volumes/<catalog>/bronze/raw_files/
databricks fs cp data/sample/analyst_roles.csv dbfs:/Volumes/<catalog>/bronze/raw_files/
databricks fs cp data/sample/nist_controls.csv dbfs:/Volumes/<catalog>/bronze/raw_files/
scripts/run_notebook.sh 01_ingest_bronze
scripts/run_notebook.sh 02_transform_silver_gold
scripts/run_notebook.sh 03_governance
scripts/run_notebook.sh 04_dashboard
python3 scripts/create_dashboard.py <catalog> <warehouse_id>
```

Set `DATABRICKS_BIN` if the CLI is not on your PATH. To refresh the sample data, run `python3 scripts/download_awards.py`.

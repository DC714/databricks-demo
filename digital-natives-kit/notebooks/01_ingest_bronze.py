# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Ingest synthetic telemetry to bronze
# MAGIC All data here is SYNTHETIC (see `scripts/generate_telemetry.py`). Upload the four CSV files in `data/sample/`
# MAGIC to the volume first (see README).

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
c = dbutils.widgets.get("catalog")
base = f"/Volumes/{c}/dn_bronze/raw_files"
for s in ["dn_bronze", "dn_silver", "dn_gold"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {c}.{s}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {c}.dn_bronze.raw_files")

# COMMAND ----------

# Bronze keeps text columns exactly as received; typing happens in silver.
tables = {"accounts": "dn_accounts.csv", "weekly_usage": "dn_weekly_usage.csv",
          "weekly_users": "dn_weekly_users.csv", "milestones": "dn_milestones.csv"}
counts = {}
for t, f in tables.items():
    spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_bronze.{t}
                  COMMENT 'SYNTHETIC telemetry, loaded unchanged from {f}'
                  AS SELECT * EXCEPT (_rescued_data), current_timestamp() AS _ingested_at
                  FROM read_files('{base}/{f}', format => 'csv', header => true, inferSchema => false)""")
    counts[t] = spark.table(f"{c}.dn_bronze.{t}").count()
print(counts)
dbutils.notebook.exit(str(counts))

# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Ingest to bronze
# MAGIC Creates schemas and a Unity Catalog volume, then loads the raw CSV files into bronze Delta tables.
# MAGIC Before running, upload the files in `data/sample/` to the volume (see README, step 3).
# MAGIC Data: public USAspending.gov awards, plus synthetic analyst roles and a hand-written NIST control map.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
catalog = dbutils.widgets.get("catalog")
base = f"/Volumes/{catalog}/bronze/raw_files"

for s in ["bronze", "silver", "gold", "ref"]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{s}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.bronze.raw_files")

# COMMAND ----------

# Bronze keeps every column as text, exactly as received, plus load metadata.
# Typing and cleaning happen in silver so bronze can always be replayed.
spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.bronze.awards_raw
COMMENT 'Raw USAspending contract awards (FY2025 sample). Public data, loaded unchanged.'
AS SELECT * EXCEPT (_rescued_data), current_timestamp() AS _ingested_at, _metadata.file_path AS _source_file
FROM read_files('{base}/usaspending_awards_fy2025.csv', format => 'csv', header => true,
                inferSchema => false, multiLine => true)
""")

# COMMAND ----------

# Reference tables: synthetic analyst roles (not real people) and the control map.
spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.ref.analyst_roles
COMMENT 'SYNTHETIC analyst roles used to demonstrate row filters and column masks'
AS SELECT * EXCEPT (_rescued_data) FROM read_files('{base}/analyst_roles.csv', format => 'csv', header => true)
""")
spark.sql(f"""
CREATE OR REPLACE TABLE {catalog}.ref.nist_controls
COMMENT 'Hand-written learning aid mapping NIST 800-53 families to platform features. Not an assessment.'
AS SELECT * EXCEPT (_rescued_data) FROM read_files('{base}/nist_controls.csv', format => 'csv', header => true)
""")

# COMMAND ----------

counts = {t: spark.table(f"{catalog}.{t}").count()
          for t in ["bronze.awards_raw", "ref.analyst_roles", "ref.nist_controls"]}
print(counts)
dbutils.notebook.exit(str(counts))

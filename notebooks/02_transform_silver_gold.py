# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Transform to silver and gold
# MAGIC Plain Delta SQL (Lakeflow Declarative Pipelines would also fit; plain SQL keeps this runnable as a simple job).
# MAGIC Quality rules decide which rows reach silver. Failing rows go to a quarantine table with the reason.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
c = dbutils.widgets.get("catalog")

# COMMAND ----------

# Step 1: type the columns, standardize names, derive region, flag quality problems, drop duplicates.
# Duplicate award_ids are resolved by keeping the row with the largest amount.
spark.sql(f"""
CREATE OR REPLACE TEMP VIEW typed AS
SELECT
  trim(award_id) AS award_id,
  upper(trim(recipient_name)) AS vendor_name,
  recipient_uei AS vendor_uei,
  trim(awarding_agency) AS agency,
  trim(awarding_sub_agency) AS sub_agency,
  try_cast(award_amount AS DECIMAL(18,2)) AS award_amount,
  try_cast(start_date AS DATE) AS start_date,
  try_cast(end_date AS DATE) AS end_date,
  award_type, naics_code, naics_description, psc_code,
  nullif(state_code, '') AS state_code,
  CASE
    WHEN state_code IN ('CT','ME','MA','NH','RI','VT','NJ','NY','PA') THEN 'Northeast'
    WHEN state_code IN ('DE','DC','FL','GA','MD','NC','SC','VA','WV','AL','KY','MS','TN','AR','LA','OK','TX') THEN 'South'
    WHEN state_code IN ('IL','IN','MI','OH','WI','IA','KS','MN','MO','NE','ND','SD') THEN 'Midwest'
    WHEN state_code IN ('AZ','CO','ID','MT','NV','NM','UT','WY','AK','CA','HI','OR','WA') THEN 'West'
    ELSE 'Other'
  END AS region,
  description,
  _ingested_at
FROM {c}.bronze.awards_raw
""")

spark.sql(f"""
CREATE OR REPLACE TEMP VIEW checked AS
SELECT *,
  row_number() OVER (PARTITION BY award_id ORDER BY award_amount DESC NULLS LAST) AS rn,
  concat_ws('; ',
    CASE WHEN award_id IS NULL OR award_id = '' THEN 'missing award_id' END,
    CASE WHEN award_amount IS NULL OR award_amount <= 0 THEN 'non-positive amount' END,
    CASE WHEN start_date IS NULL THEN 'bad start_date' END,
    CASE WHEN agency IS NULL THEN 'missing agency' END) AS failed_rules
FROM typed
""")

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE TABLE {c}.silver.awards
COMMENT 'Typed, deduplicated awards that passed quality rules'
AS SELECT * EXCEPT (rn, failed_rules) FROM checked WHERE rn = 1 AND failed_rules = ''
""")
spark.sql(f"""
CREATE OR REPLACE TABLE {c}.silver.awards_quarantine
COMMENT 'Rows that failed a quality rule, kept with the reason'
AS SELECT *, failed_rules AS reason FROM checked WHERE rn = 1 AND failed_rules <> ''
""")

# COMMAND ----------

# Gold tables feed the dashboard.
spark.sql(f"""
CREATE OR REPLACE TABLE {c}.gold.spend_by_agency
COMMENT 'Obligated award value by agency'
AS SELECT agency, count(*) AS awards, sum(award_amount) AS total_amount, avg(award_amount) AS avg_amount
FROM {c}.silver.awards GROUP BY agency
""")
spark.sql(f"""
CREATE OR REPLACE TABLE {c}.gold.vendor_concentration
COMMENT 'Per-agency vendor share of spend, with cumulative share of the top vendors'
AS
WITH v AS (
  SELECT agency, vendor_name, sum(award_amount) AS vendor_amount FROM {c}.silver.awards GROUP BY agency, vendor_name
), s AS (
  SELECT *, vendor_amount / sum(vendor_amount) OVER (PARTITION BY agency) AS share,
         row_number() OVER (PARTITION BY agency ORDER BY vendor_amount DESC) AS vendor_rank
  FROM v
)
SELECT *, sum(share) OVER (PARTITION BY agency ORDER BY vendor_rank) AS cumulative_share FROM s
""")
spark.sql(f"""
CREATE OR REPLACE TABLE {c}.gold.spend_by_naics_sector
COMMENT 'Spend by two-digit NAICS sector (stand-in for small business share, which this API does not return)'
AS SELECT left(naics_code, 2) AS naics_sector, count(*) AS awards, sum(award_amount) AS total_amount,
          sum(award_amount) / sum(sum(award_amount)) OVER () AS share_of_total
FROM {c}.silver.awards WHERE naics_code IS NOT NULL GROUP BY left(naics_code, 2)
""")

# COMMAND ----------

n = lambda t: spark.table(f"{c}.{t}").count()
out = {"bronze": n("bronze.awards_raw"), "silver": n("silver.awards"), "quarantine": n("silver.awards_quarantine"),
       "gold_agency": n("gold.spend_by_agency"), "gold_vendor": n("gold.vendor_concentration"),
       "gold_naics": n("gold.spend_by_naics_sector")}
print(out)
dbutils.notebook.exit(str(out))

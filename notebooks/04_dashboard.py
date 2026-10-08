# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Dashboard datasets
# MAGIC These are the queries behind the AI/BI dashboard (build steps in `docs/dashboard-spec.md`).
# MAGIC Run the notebook to check each query returns data, then paste the same SQL into dashboard datasets.
# MAGIC The last section shows the same rows as an admin and as a restricted analyst, for the masking screenshot.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
c = dbutils.widgets.get("catalog")
out = {}

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dataset 1: spend by agency (top 10)

# COMMAND ----------

q1 = f"""SELECT agency, awards, round(total_amount / 1e9, 2) AS total_billions
         FROM {c}.gold.spend_by_agency ORDER BY total_amount DESC LIMIT 10"""
d1 = spark.sql(q1); display(d1); out["agency_rows"] = d1.count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dataset 2: vendor concentration
# MAGIC Share of each agency's spend held by its top 5 vendors. A high number means the agency depends on few suppliers.

# COMMAND ----------

q2 = f"""SELECT agency, round(max(cumulative_share) * 100, 1) AS top5_share_pct
         FROM {c}.gold.vendor_concentration WHERE vendor_rank <= 5
         GROUP BY agency HAVING count(*) = 5 ORDER BY top5_share_pct DESC"""
d2 = spark.sql(q2); display(d2); out["concentration_rows"] = d2.count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Dataset 3: spend share by NAICS sector
# MAGIC Stand-in for small business share (the API used here does not return that flag).

# COMMAND ----------

q3 = f"""SELECT naics_sector, awards, round(share_of_total * 100, 1) AS share_pct
         FROM {c}.gold.spend_by_naics_sector ORDER BY share_pct DESC LIMIT 10"""
d3 = spark.sql(q3); display(d3); out["naics_rows"] = d3.count()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Masking and filtering side by side
# MAGIC Same table, same query, different identity. The policy functions are from notebook 03.

# COMMAND ----------

me = spark.sql("SELECT current_user()").first()[0]
parts = [f"""SELECT '{label}' AS viewer, vendor_name, agency, region,
                    {c}.ref.uei_for('{who}', vendor_uei) AS vendor_uei, award_amount
             FROM {c}.silver.awards WHERE {c}.ref.row_allowed('{who}', agency, region)"""
         for label, who in [("admin", me), ("gsa_public_trust", "analyst.gsa@example.test")]]
d4 = spark.sql(" UNION ALL ".join(f"(SELECT * FROM ({p}) ORDER BY award_amount DESC LIMIT 3)" for p in parts))
display(d4); out["masking_rows"] = d4.count()

dbutils.notebook.exit(str(out))

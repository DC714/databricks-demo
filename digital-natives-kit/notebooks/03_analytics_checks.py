# Databricks notebook source
# MAGIC %md
# MAGIC # 03 Analytics checks
# MAGIC Shows the queries behind the dashboard and checks the health status against the generator's hidden archetype.
# MAGIC Because the data is synthetic, this only proves the scoring logic behaves as intended. It says nothing about real customers.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
c = dbutils.widgets.get("catalog")
out = {}

# COMMAND ----------

# Consumption by segment and month.
d = spark.sql(f"SELECT segment, date_format(month, 'yyyy-MM') AS m, round(units) AS units FROM {c}.dn_gold.segment_trend ORDER BY m, segment")
display(d)
last = spark.sql(f"""SELECT segment, round(sum(units)) AS u FROM {c}.dn_gold.segment_trend
                     WHERE month = (SELECT max(month) FROM {c}.dn_gold.segment_trend) GROUP BY segment""").collect()
out["latest_month_units"] = {r.segment: r.u for r in last}

# COMMAND ----------

# Time to first production workload by segment (days).
t = spark.sql(f"""SELECT segment, count(days_to_production) AS accounts, round(avg(days_to_production)) AS avg_days,
                  percentile_approx(days_to_production, 0.5) AS median_days FROM {c}.dn_gold.time_to_value GROUP BY segment""")
display(t)
out["time_to_value"] = {r.segment: (r.avg_days, r.median_days) for r in t.collect()}

# COMMAND ----------

# Status counts by segment, and validation against the hidden generator archetype.
display(spark.sql(f"SELECT segment, status, count(*) AS accounts FROM {c}.dn_gold.account_status GROUP BY ALL ORDER BY segment, status"))
x = spark.sql(f"SELECT generator_archetype AS archetype, status, count(*) AS n FROM {c}.dn_gold.account_status GROUP BY ALL").collect()
table = {}
for r in x:
    table.setdefault(r.archetype, {})[r.status] = r.n
out["archetype_vs_status"] = table
for k, v in table.items(): print(k, v)
dbutils.notebook.exit(str(out))

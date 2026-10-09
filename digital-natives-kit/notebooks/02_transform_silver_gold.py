# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Silver and gold: consumption analytics and account health
# MAGIC The health score weights are ASSUMPTIONS for illustration. They were not fitted to real customer outcomes.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("rate_per_unit", "0.50")
c = dbutils.widgets.get("catalog")
rate = float(dbutils.widgets.get("rate_per_unit"))  # illustrative price per compute unit, not a real rate

# COMMAND ----------

# Silver: typed and deduplicated.
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_silver.accounts AS
  SELECT account_id, account_name, segment, to_date(signup_date) AS signup_date, region, employee_band, generator_archetype
  FROM {c}.dn_bronze.accounts""")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_silver.usage_weekly AS
  SELECT account_id, week_start, workload, sum(compute_units) AS compute_units FROM (
    SELECT account_id, to_date(week_start) AS week_start, workload, try_cast(compute_units AS DOUBLE) AS compute_units
    FROM {c}.dn_bronze.weekly_usage) WHERE compute_units > 0 GROUP BY account_id, week_start, workload""")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_silver.users_weekly AS
  SELECT DISTINCT account_id, to_date(week_start) AS week_start, try_cast(active_users AS INT) AS active_users
  FROM {c}.dn_bronze.weekly_users""")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_silver.milestones AS
  SELECT DISTINCT account_id, milestone, to_date(milestone_date) AS milestone_date FROM {c}.dn_bronze.milestones""")

# COMMAND ----------

# Gold 1: account by week, then monthly consumption and segment trend.
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_gold.account_weekly AS
  SELECT u.account_id, u.week_start, sum(u.compute_units) AS units, max(w.active_users) AS active_users
  FROM {c}.dn_silver.usage_weekly u LEFT JOIN {c}.dn_silver.users_weekly w USING (account_id, week_start)
  GROUP BY u.account_id, u.week_start""")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_gold.monthly_consumption
  COMMENT 'Monthly compute units and ILLUSTRATIVE cost (rate is a notebook parameter, not a real price)' AS
  SELECT a.account_id, a.account_name, a.segment, date_trunc('month', w.week_start) AS month,
         sum(w.units) AS units, sum(w.units) * {rate} AS est_cost
  FROM {c}.dn_gold.account_weekly w JOIN {c}.dn_silver.accounts a USING (account_id) GROUP BY ALL""")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_gold.segment_trend AS
  SELECT segment, month, count(DISTINCT account_id) AS active_accounts, sum(units) AS units, sum(est_cost) AS est_cost
  FROM {c}.dn_gold.monthly_consumption GROUP BY segment, month""")

# COMMAND ----------

# Gold 2: time to first production workload, by account.
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_gold.time_to_value AS
  SELECT a.account_id, a.segment, a.signup_date, m.milestone_date AS first_production_date,
         datediff(m.milestone_date, a.signup_date) AS days_to_production
  FROM {c}.dn_silver.accounts a LEFT JOIN {c}.dn_silver.milestones m
    ON a.account_id = m.account_id AND m.milestone = 'first_production_workload'""")

# COMMAND ----------

# Gold 3: account health. Windows are relative to the latest week in the data.
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_gold.account_health
COMMENT 'Health score 0-100 from momentum, 13-week trend, workload breadth, and user growth. Weights are assumptions.' AS
WITH asof AS (SELECT max(week_start) AS d FROM {c}.dn_gold.account_weekly),
agg AS (
  SELECT w.account_id,
    sum(IF(w.week_start > date_sub(d, 28), units, 0)) AS last4,
    sum(IF(w.week_start <= date_sub(d, 28) AND w.week_start > date_sub(d, 56), units, 0)) AS prior4,
    sum(IF(w.week_start > date_sub(d, 91), units, 0)) AS last13,
    sum(IF(w.week_start <= date_sub(d, 91) AND w.week_start > date_sub(d, 182), units, 0)) AS prior13,
    avg(IF(w.week_start > date_sub(d, 28), active_users, NULL)) AS users4,
    avg(IF(w.week_start <= date_sub(d, 28) AND w.week_start > date_sub(d, 56), active_users, NULL)) AS users_prior4,
    max(units) AS peak_week,
    avg(IF(w.week_start > date_sub(d, 28), units, NULL)) AS avg_recent_week
  FROM {c}.dn_gold.account_weekly w CROSS JOIN asof GROUP BY w.account_id),
breadth AS (
  SELECT account_id, count_if(share >= 0.10) AS workloads FROM (
    SELECT account_id, workload, sum(compute_units) / sum(sum(compute_units)) OVER (PARTITION BY account_id) AS share
    FROM {c}.dn_silver.usage_weekly u CROSS JOIN asof WHERE u.week_start > date_sub(d, 91) GROUP BY account_id, workload)
  GROUP BY account_id),
scored AS (
  SELECT agg.account_id, s.account_name, s.segment, s.generator_archetype, agg.last4, agg.prior4,
    coalesce(agg.last4 / nullif(agg.prior4, 0), 1.0) AS momentum_ratio,
    coalesce(agg.last13 / nullif(agg.prior13, 0), 1.0) AS trend_ratio,
    coalesce(b.workloads, 0) AS workloads,
    coalesce(agg.users4 / nullif(agg.users_prior4, 0), 1.0) AS user_ratio,
    agg.avg_recent_week / nullif(agg.peak_week, 0) AS retained_vs_peak
  FROM agg JOIN {c}.dn_silver.accounts s ON agg.account_id = s.account_id
  LEFT JOIN breadth b ON b.account_id = agg.account_id)
SELECT *,
  round(100 * (0.35 * least(greatest(momentum_ratio - 0.5, 0), 1)
             + 0.30 * least(greatest((trend_ratio - 0.5) / 1.5, 0), 1)
             + 0.20 * workloads / 3.0
             + 0.15 * least(greatest(user_ratio - 0.5, 0), 1)), 1) AS health_score
FROM scored""")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.dn_gold.account_status
COMMENT 'Health score plus rule-based status. Thresholds are assumptions.' AS
SELECT *, CASE
    WHEN momentum_ratio < 0.85 OR retained_vs_peak < 0.6 OR health_score < 40 THEN 'at_risk'
    WHEN health_score >= 70 AND workloads >= 2 THEN 'expansion_candidate'
    WHEN health_score < 55 THEN 'watch'
    ELSE 'healthy' END AS status
FROM {c}.dn_gold.account_health""")

# COMMAND ----------

n = lambda t: spark.table(f"{c}.{t}").count()
out = {t: n(t) for t in ["dn_silver.usage_weekly", "dn_gold.monthly_consumption", "dn_gold.segment_trend",
                         "dn_gold.time_to_value", "dn_gold.account_status"]}
print(out)
dbutils.notebook.exit(str(out))

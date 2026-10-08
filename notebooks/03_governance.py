# Databricks notebook source
# MAGIC %md
# MAGIC # 03 Governance
# MAGIC Each control states its compliance intent (NIST 800-53 family in brackets).
# MAGIC Free Edition has one user, so the restricted analyst is shown by calling the same policy functions
# MAGIC with a simulated identity from the synthetic roles table. The real row filter and column mask wrap
# MAGIC those functions using `current_user()`.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
c = dbutils.widgets.get("catalog")
me = spark.sql("SELECT current_user()").first()[0]
result = {}

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Grants [AC] least privilege
# MAGIC Analysts get read access to gold only. Silver and bronze stay with the platform team.

# COMMAND ----------

for stmt in [f"GRANT USE CATALOG ON CATALOG {c} TO `account users`",
             f"GRANT USE SCHEMA, SELECT ON SCHEMA {c}.gold TO `account users`"]:
    try:
        spark.sql(stmt); print("ok:", stmt)
    except Exception as e:
        print("skipped:", stmt, "|", str(e)[:120])

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Policy functions [AC]
# MAGIC The caller is registered as an admin row (all agencies, all regions, top clearance) at run time,
# MAGIC so the person running the notebook sees everything. The synthetic analysts see less.

# COMMAND ----------

# Make reruns safe: remove any earlier policy before replacing the functions it uses.
for stmt in [f"ALTER TABLE {c}.silver.awards DROP ROW FILTER", f"ALTER TABLE {c}.silver.awards ALTER COLUMN vendor_uei DROP MASK"]:
    try: spark.sql(stmt)
    except Exception: pass
spark.sql(f"DELETE FROM {c}.ref.analyst_roles WHERE analyst_id = 'ADMIN'")
spark.sql(f"INSERT INTO {c}.ref.analyst_roles VALUES ('ADMIN', '{me}', 'ALL', 'TOP SECRET', 'ALL')")

# Rows: visible when the analyst's agency and region match, or are ALL.
spark.sql(f"""
CREATE OR REPLACE FUNCTION {c}.ref.row_allowed(who STRING, p_agency STRING, p_region STRING)
RETURNS BOOLEAN
COMMENT 'Row policy: analyst sees rows for their agency and region (ALL means no limit)'
RETURN EXISTS (SELECT 1 FROM {c}.ref.analyst_roles r WHERE r.email = who
               AND (r.agency = 'ALL' OR r.agency = p_agency) AND (r.region = 'ALL' OR r.region = p_region))
""")
# Columns: contractor UEI is visible only at SECRET or above.
spark.sql(f"""
CREATE OR REPLACE FUNCTION {c}.ref.uei_for(who STRING, p_uei STRING)
RETURNS STRING
COMMENT 'Column policy: show vendor UEI only to SECRET or TOP SECRET clearance, else mask'
RETURN CASE WHEN EXISTS (SELECT 1 FROM {c}.ref.analyst_roles r WHERE r.email = who
                         AND r.clearance IN ('SECRET', 'TOP SECRET'))
            THEN p_uei ELSE concat('****', right(p_uei, 2)) END
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Row filter and column mask on the table [AC, SC]
# MAGIC The functions the table enforces always use the real caller identity.

# COMMAND ----------

spark.sql(f"""CREATE OR REPLACE FUNCTION {c}.ref.rf_awards(agency STRING, region STRING)
RETURNS BOOLEAN RETURN {c}.ref.row_allowed(current_user(), agency, region)""")
spark.sql(f"""CREATE OR REPLACE FUNCTION {c}.ref.mask_uei(uei STRING)
RETURNS STRING RETURN {c}.ref.uei_for(current_user(), uei)""")

spark.sql(f"ALTER TABLE {c}.silver.awards SET ROW FILTER {c}.ref.rf_awards ON (agency, region)")
spark.sql(f"ALTER TABLE {c}.silver.awards ALTER COLUMN vendor_uei SET MASK {c}.ref.mask_uei")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Demo: same query, three identities
# MAGIC The admin (you) is the real enforced view. The two analysts use the same policy functions with a simulated identity.

# COMMAND ----------

def view_as(who):
    q = f"""SELECT count(*) AS rows_visible, count(DISTINCT agency) AS agencies, min({c}.ref.uei_for('{who}', vendor_uei)) AS sample_uei
            FROM {c}.silver.awards WHERE {c}.ref.row_allowed('{who}', agency, region)"""
    return spark.sql(q).first().asDict()

raw_total = spark.sql(f"SELECT count(*) FROM {c}.silver.awards").first()[0]
result["admin_enforced_rows"] = raw_total
result["admin_sim"] = view_as(me)
result["defense_west_secret_top"] = view_as("analyst.defense.west@example.test")
result["gsa_public_trust"] = view_as("analyst.gsa@example.test")
for k, v in result.items(): print(k, v)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Tags and comments [AU, CM]
# MAGIC Tags record sensitivity so reviewers and tools can find what needs protection.

# COMMAND ----------

spark.sql(f"ALTER TABLE {c}.silver.awards SET TAGS ('data_source' = 'usaspending_public', 'sensitivity' = 'internal')")
spark.sql(f"ALTER TABLE {c}.silver.awards ALTER COLUMN vendor_uei SET TAGS ('sensitivity' = 'masked_identifier')")
spark.sql(f"ALTER TABLE {c}.ref.analyst_roles SET TAGS ('data_source' = 'synthetic')")
spark.sql(f"COMMENT ON COLUMN {c}.silver.awards.vendor_uei IS 'Contractor Unique Entity ID. Masked below SECRET clearance.'")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Lineage and audit [AU]
# MAGIC System tables may need to be enabled and can lag; each query is wrapped so the notebook still finishes.
# MAGIC Lineage is also visible in the Catalog UI: open `gold.spend_by_agency`, then the Lineage tab.

# COMMAND ----------

for label, q in [
    ("lineage", f"""SELECT source_table_full_name, target_table_full_name FROM system.access.table_lineage
                    WHERE target_table_full_name LIKE '{c}.gold.%' LIMIT 10"""),
    ("audit", f"""SELECT event_time, user_identity.email AS who, action_name FROM system.access.audit
                  WHERE request_params.full_name_arg LIKE '{c}.silver.awards%' ORDER BY event_time DESC LIMIT 10""")]:
    try:
        rows = spark.sql(q).collect(); print(label, "rows:", len(rows)); result[label + "_rows"] = len(rows)
    except Exception as e:
        print(label, "unavailable:", str(e)[:150]); result[label + "_rows"] = "unavailable"

dbutils.notebook.exit(str(result))

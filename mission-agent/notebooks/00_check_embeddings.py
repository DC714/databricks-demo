# Databricks notebook source
# MAGIC %md
# MAGIC # 00 Check: can a serverless notebook run a self-hosted embedding model?
# MAGIC Models from China are excluded in this project, so the hosted GTE and BGE endpoints are not used.

# COMMAND ----------

# MAGIC %pip install sentence-transformers -q

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

import time
res = {}
try:
    t = time.time()
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("mixedbread-ai/mxbai-embed-xsmall-v1")
    res["load_s"] = round(time.time() - t, 1)
    t = time.time()
    v = m.encode(["access control policy"] * 200)
    res["dim"] = int(v.shape[1]); res["encode_200_s"] = round(time.time() - t, 2)
except Exception as e:
    res["error"] = str(e)[:300]
print(res)
dbutils.notebook.exit(str(res))

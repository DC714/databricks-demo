# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Load NIST chunks and embed them
# MAGIC Source text: public NIST publications (US government works), chunked by `scripts/build_corpus.py`.
# MAGIC Embeddings come from `mixedbread-ai/mxbai-embed-xsmall-v1`, run inside this notebook on CPU
# MAGIC (no China-origin models are used in this project, so the hosted GTE and BGE endpoints are skipped).

# COMMAND ----------

# MAGIC %pip install sentence-transformers -q

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
c = dbutils.widgets.get("catalog")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {c}.ma")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {c}.ma.raw_files")
spark.sql(f"""CREATE OR REPLACE TABLE {c}.ma.chunks
  COMMENT 'Text chunks of public NIST publications, with page numbers for citation'
  AS SELECT chunk_id, doc_id, title, source_url, try_cast(page AS INT) AS page, text
  FROM read_files('/Volumes/{c}/ma/raw_files/nist_chunks.csv', format => 'csv', header => true, multiLine => true,
                  escape => '"')""")
print(spark.table(f"{c}.ma.chunks").count(), "chunks")

# COMMAND ----------

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("mixedbread-ai/mxbai-embed-xsmall-v1")
rows = spark.table(f"{c}.ma.chunks").select("chunk_id", "text").collect()
vecs = model.encode([r.text for r in rows], batch_size=32, normalize_embeddings=True)
data = [(r.chunk_id, [float(x) for x in v]) for r, v in zip(rows, vecs)]
spark.createDataFrame(data, "chunk_id string, embedding array<float>").write.mode("overwrite") \
     .saveAsTable(f"{c}.ma.chunk_embeddings")
out = {"chunks": len(rows), "dim": int(vecs.shape[1])}
print(out)
dbutils.notebook.exit(str(out))

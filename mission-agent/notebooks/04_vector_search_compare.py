# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Compare retrieval backends and benchmark latency
# MAGIC Backends: in-memory cosine search, Vector Search (vector only), Vector Search hybrid (vector plus keyword),
# MAGIC and Vector Search with a document filter. The index (`ma.chunk_index`) uses my own 384-dimension embeddings.
# MAGIC The hosted reranker is not tested: I cannot verify the origin of its model, and this project excludes
# MAGIC models from Chinese developers.

# COMMAND ----------

# MAGIC %pip install sentence-transformers databricks-vectorsearch -q

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ./02_rag_agent

# COMMAND ----------

import time
import statistics as st
import pandas as pd
from databricks.vector_search.client import VectorSearchClient

idx = VectorSearchClient(disable_notice=True).get_index(endpoint_name="mission-agent-vs", index_name=f"{_c}.ma.chunk_index")
out = {}


def embed(question):
    return _embedder.encode([_QPREFIX + question], normalize_embeddings=True)[0]


def vs(question, k=5, vec=None, hybrid=False, doc=None):
    vec = embed(question) if vec is None else vec
    kw = dict(query_vector=vec.tolist(), columns=["chunk_id", "doc_id"], num_results=k)
    if hybrid:
        kw.update(query_type="HYBRID", query_text=question)
    if doc:
        kw["filters"] = {"doc_id": doc}
    return [(r[0], float(r[-1])) for r in idx.similarity_search(**kw)["result"]["data_array"]]


# COMMAND ----------

# MAGIC %md
# MAGIC ## Latency: warm up, then 5 repeats per query, with the question embedding timed separately

# COMMAND ----------

qs = pd.read_csv(f"/Volumes/{_c}/ma/raw_files/eval_questions.csv").fillna("")
sample = list(qs.question[:8])
for s in sample[:3]:  # warm-up, not timed
    vs(s); retrieve(s)
t_emb, t_mem, t_vs, t_hy = [], [], [], []
for s in sample:
    for _ in range(5):
        t = time.time(); v = embed(s); t_emb.append(time.time() - t)
        t = time.time(); MAT @ v; t_mem.append(time.time() - t)
        t = time.time(); vs(s, vec=v); t_vs.append(time.time() - t)
        t = time.time(); vs(s, vec=v, hybrid=True); t_hy.append(time.time() - t)
ms = lambda a: [round(1000 * st.median(a), 1), round(1000 * sorted(a)[int(0.95 * len(a)) - 1], 1)]
out["latency_ms_median_p95"] = {"embed_question": ms(t_emb), "memory_search_only": ms(t_mem),
                                "vector_search_call": ms(t_vs), "hybrid_call": ms(t_hy)}
print(out["latency_ms_median_p95"])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Retrieval quality on the 32 questions

# COMMAND ----------

rows = []
for r in qs.itertuples():
    v = embed(r.question)
    res = {"memory": retrieve(r.question, 5), "vector": vs(r.question, vec=v), "hybrid": vs(r.question, vec=v, hybrid=True)}
    if r.gold_doc:
        res["vector_filtered"] = vs(r.question, vec=v, doc=r.gold_doc)
    rec = {"qid": r.qid, "category": r.category}
    for name, hits in res.items():
        if r.category == "in_scope":
            text = " ".join(META[h[0]].text for h in hits).lower()
            rec[f"{name}_doc"] = r.gold_doc in {META[h[0]].doc_id for h in hits}
            rec[f"{name}_kw"] = r.must_contain.lower() in text
        rec[f"{name}_top"] = hits[0][1] if hits else None
    rec["hybrid_same_top1_as_vector"] = res["hybrid"][0][0] == res["vector"][0][0]
    rows.append(rec)
d = pd.DataFrame(rows)
ins = d[d.category == "in_scope"]
out["doc@5"] = {n: round(ins[f"{n}_doc"].mean(), 3) for n in ["memory", "vector", "hybrid", "vector_filtered"]}
out["kw@5"] = {n: round(ins[f"{n}_kw"].mean(), 3) for n in ["memory", "vector", "hybrid", "vector_filtered"]}
out["hybrid_same_top1_as_vector"] = round(d.hybrid_same_top1_as_vector.mean(), 3)
out["kw_misses_memory"] = list(ins[~ins.memory_kw.astype(bool)].qid)
out["kw_misses_hybrid"] = list(ins[~ins.hybrid_kw.astype(bool)].qid)
out["hybrid_top_score_range"] = {"in_scope": [round(ins.hybrid_top.min(), 3), round(ins.hybrid_top.max(), 3)],
                                 "other": [round(d[d.category != "in_scope"].hybrid_top.min(), 3), round(d[d.category != "in_scope"].hybrid_top.max(), 3)]}
print(out)
dbutils.notebook.exit(str(out))

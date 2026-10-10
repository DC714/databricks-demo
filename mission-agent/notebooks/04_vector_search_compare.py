# Databricks notebook source
# MAGIC %md
# MAGIC # 04 Compare in-memory retrieval with a Databricks Vector Search index
# MAGIC The index (`ma.chunk_index`) is a Delta Sync index over `ma.chunk_vectors` using my own embeddings
# MAGIC (self-managed, 384 dimensions), so no hosted embedding model is involved.
# MAGIC Only retrieval is compared. Vector Search scores use a different scale than the cosine scores the
# MAGIC relevance gate was set on, so the gate is not applied here.

# COMMAND ----------

# MAGIC %pip install sentence-transformers databricks-vectorsearch -q

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ./02_rag_agent

# COMMAND ----------

import time
import pandas as pd
from databricks.vector_search.client import VectorSearchClient

idx = VectorSearchClient(disable_notice=True).get_index(endpoint_name="mission-agent-vs", index_name=f"{_c}.ma.chunk_index")


def retrieve_vs(question, k=5):
    v = _embedder.encode([_QPREFIX + question], normalize_embeddings=True)[0].tolist()
    r = idx.similarity_search(query_vector=v, columns=["chunk_id", "doc_id"], num_results=k)
    return [(row[0], float(row[-1])) for row in r["result"]["data_array"]]


q = pd.read_csv(f"/Volumes/{_c}/ma/raw_files/eval_questions.csv").fillna("")
rows, t_mem, t_vs = [], [], []
for r in q.itertuples():
    t = time.time(); a = retrieve(r.question, 5); t_mem.append(time.time() - t)
    t = time.time(); b = retrieve_vs(r.question, 5); t_vs.append(time.time() - t)
    rec = {"qid": r.qid, "category": r.category, "overlap_top5": len({x[0] for x in a} & {x[0] for x in b}),
           "same_top1": a[0][0] == b[0][0], "vs_top_score": b[0][1]}
    if r.category == "in_scope":
        for name, hits in [("mem", a), ("vs", b)]:
            text = " ".join(META[h[0]].text for h in hits).lower()
            rec[f"{name}_doc"] = r.gold_doc in {META[h[0]].doc_id for h in hits}
            rec[f"{name}_kw"] = r.must_contain.lower() in text
    rows.append(rec)
d = pd.DataFrame(rows)
ins = d[d.category == "in_scope"]
out = {"mem_doc@5": round(ins.mem_doc.mean(), 3), "vs_doc@5": round(ins.vs_doc.mean(), 3),
       "mem_kw@5": round(ins.mem_kw.mean(), 3), "vs_kw@5": round(ins.vs_kw.mean(), 3),
       "mean_overlap_top5": round(d.overlap_top5.mean(), 2), "same_top1": round(d.same_top1.mean(), 3),
       "latency_ms_mem": round(1000 * sum(t_mem) / len(t_mem)), "latency_ms_vs": round(1000 * sum(t_vs) / len(t_vs)),
       "vs_score_range_in": [round(ins.vs_top_score.min(), 3), round(ins.vs_top_score.max(), 3)],
       "vs_score_range_out": [round(d[d.category != "in_scope"].vs_top_score.min(), 3),
                              round(d[d.category != "in_scope"].vs_top_score.max(), 3)]}
print(out)
dbutils.notebook.exit(str(out))

# Databricks notebook source
# MAGIC %md
# MAGIC # 03 Evaluate retrieval, answers, and guardrails
# MAGIC 32 questions (24 in scope, 6 out of scope, 2 adversarial) in `data/eval_questions.csv`.
# MAGIC Two answering models are compared: Gemma 3 12B (Google) and Llama 3.1 8B (Meta).
# MAGIC Llama 3.3 70B (Meta) scores faithfulness, so no model grades its own family's answers.
# MAGIC The judge is itself a model and can be wrong: hand-check a sample before trusting the scores.

# COMMAND ----------

# MAGIC %pip install sentence-transformers -q

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ./02_rag_agent

# COMMAND ----------

import pandas as pd
q = pd.read_csv(f"/Volumes/{_c}/ma/raw_files/eval_questions.csv").fillna("")
MODELS = ["databricks-gemma-3-12b", "databricks-meta-llama-3-1-8b-instruct"]

# Retrieval quality does not depend on the answering model.
ret = []
for r in q.itertuples():
    hits = retrieve(r.question, 5)
    text = " ".join(META[h[0]].text for h in hits).lower()
    ret.append({"qid": r.qid, "category": r.category, "top_score": hits[0][1],
                "doc_hit": r.gold_doc in {META[h[0]].doc_id for h in hits} if r.gold_doc else None,
                "kw_hit": (r.must_contain.lower() in text) if r.must_contain else None})
ret = pd.DataFrame(ret)
ins = ret[ret.category == "in_scope"]
summary = {"threshold": THRESHOLD, "doc_hit@5": round(ins.doc_hit.mean(), 3), "kw_hit@5": round(ins.kw_hit.mean(), 3),
           "top_score_in_scope": [round(ins.top_score.min(), 3), round(ins.top_score.median(), 3)],
           "top_score_out_of_scope": [round(ret[ret.category != "in_scope"].top_score.median(), 3),
                                      round(ret[ret.category != "in_scope"].top_score.max(), 3)]}
print(summary)

# COMMAND ----------

res = []
for model in MODELS:
    for r in q.itertuples():
        a = answer(model, r.question)
        faith = judge(r.question, a["retrieved"], a["answer"]) if (r.category == "in_scope" and not a["refused"]) else None
        leaked = CANARY in a["answer"] or "Rules:" in a["answer"]
        res.append({"qid": r.qid, "category": r.category, "model": model, "refused": a["refused"], "reason": a["reason"],
                    "cited_valid": bool(a["cited"]), "faithfulness": faith, "leaked": leaked, "answer": a["answer"][:600]})
res = pd.DataFrame(res)
spark.createDataFrame(res).write.mode("overwrite").saveAsTable(f"{_c}.ma.eval_results")

for model in MODELS:
    m = res[res.model == model]
    i, o, adv = m[m.category == "in_scope"], m[m.category == "out_of_scope"], m[m.category == "adversarial"]
    summary[model] = {"answered_in_scope": round((~i.refused).mean(), 3),
                      "mean_faithfulness": round(i.faithfulness.dropna().mean(), 2),
                      "refused_out_of_scope": round(o.refused.mean(), 3), "adversarial_leaks": int(adv.leaked.sum())}
print(summary)
dbutils.notebook.exit(str(summary))

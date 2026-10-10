# Talk track: mission document agent

Use your own words. Every claim below is something the project does.

## 2-minute version

"This is a learning project on Databricks Free Edition. I built a retrieval agent over three public NIST cybersecurity documents, so every answer has to cite a passage and page. I chunked the PDFs, embedded them with a small open model I run in the notebook, and answer with Gemma 3 12B, comparing it with Llama 3.1 8B. I avoided models from Chinese developers, so I did not use the hosted GTE, BGE, or Qwen endpoints.

The part I care about is the guardrails and the measurement. There is a relevance gate that refuses before any model call, a prompt that treats passages as data, a check that every citation is a passage that was really retrieved, and a canary check for leaking the instructions. I wrote 32 evaluation questions. Retrieval found the right document for 22 of 24 in-scope questions, both models refused all out-of-scope questions, and nothing leaked. The models answered about 80 percent of in-scope questions, and every refusal was an honest 'not in the passages' caused by a retrieval miss.

The eval is small and I wrote it myself, so I treat it as a sanity check. Next I would fix identifier extraction, add keyword search, and try Vector Search."

## 5-minute version

1. **Why (30s).** Agency work needs answers you can verify, so I focused on citations and refusals, not on a chat demo.
2. **Pipeline (60s).** PDFs, 200-word chunks with page numbers, embeddings in a Delta table, cosine retrieval in memory. Why not Vector Search: I chose the simplest thing first and list it as a next step.
3. **Model choices (45s).** Gemma 3 12B and Llama 3.1 8B compared, Llama 3.3 70B as the judge so no model grades its own family. Embedding model and why I did not use the hosted ones. Say the lineage caveat out loud.
4. **Guardrails (60s).** The four layers and what each one catches. Use Q27 and Q30 as the example where the gate passes and the model still refuses.
5. **Results and honesty (60s).** Numbers from `docs/evaluation.md`. Faithfulness 5.0 is a ceiling effect, the judge was checked on only two answers, 24 questions cannot separate the models.
6. **Next steps and unknowns (45s).** See below.

## What I built

Corpus builder, embedding notebook, agent with four guardrails, a 32-question eval, two-model comparison, local tests, and an honest write-up.

## What I do not know yet

- How this behaves at agency scale, with thousands of documents and access control per document.
- Whether Vector Search pays off at scale. On 701 chunks it retrieved nearly the same results as in-memory search and was slower per query, so I cannot say.
- Whether the embedding model has the lineage property I wanted. I could not verify it fully.
- How well the judge agrees with a human on harder answers.

## Likely questions

- *"Is this Agent Bricks?"* No, that is not on Free Edition. This is hand-built.
- *"Why is retrieval in memory?"* It fits 701 chunks and kept the first version simple. I also built a Vector Search index and compared retrieval: same top result on all 32 questions, slower per query at this size.
- *"Which model is better?"* My data cannot say. The gap is one question.
- *"What stops prompt injection?"* Passages are framed as data and a canary check catches leaks, but I only tested injection in the question, not planted in a document.

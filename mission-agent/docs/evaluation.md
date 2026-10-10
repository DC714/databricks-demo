# Evaluation

32 questions: 24 in scope (the answer is in the three documents), 6 out of scope, 2 adversarial. Gate threshold 0.5, top 5 chunks, temperature 0. Answering models: Gemma 3 12B and Llama 3.1 8B. Judge: Llama 3.3 70B.

Three retrieval backends were compared, all over the same 384-dimension embeddings:
- **memory**: cosine search in the notebook.
- **vs**: a Databricks Vector Search index (`ma.chunk_index`, Delta Sync, self-managed embeddings, standard endpoint), vector only.
- **hybrid**: the same index with vector plus keyword matching. The relevance gate still uses the vector-only top score, because hybrid scores are rank-fusion values on a different scale.

## End-to-end results

| | memory | vs | hybrid (default) |
|---|---|---|---|
| Document hit at 5 (of 24) | 22 | 22 | 23 |
| Keyword hit at 5 (of 24) | 20 | 20 | 19 |
| In-scope answered, Gemma | 20 of 24 | 20 of 24 | 22 of 24 |
| In-scope answered, Llama 3.1 8B | 20 of 24 | 20 of 24 | 22 of 24 |
| Mean faithfulness (both models) | 5.0 | 5.0 | 5.0 |
| Out-of-scope refused (both models) | 6 of 6 | 6 of 6 | 6 of 6 |
| Adversarial leaks (both models) | 0 | 0 | 0 |

- Hybrid answered two more questions than vector-only search: Q05 (which CSF subcategories cover data at rest and in transit) and Q09 (the six CSF Functions). I read both answers against the NIST text and they are correct. Q12 and Q19 are still refused in all three setups.
- That is a two-question difference on a 24-question set, so read it as a hint, not a result. The keyword-hit check is crude (it looks for one phrase), and it moved the opposite way, so I trust the hand-read answers more.
- Every in-scope refusal is the model saying the answer is not in the retrieved passages. No wrong answers were produced from missing context.

## Latency (benchmark: 3 warm-up queries, then 8 questions times 5 repeats)

| Step | Median | p95 |
|---|---|---|
| Embed the question (CPU, in the notebook) | 82 ms | 156 ms |
| In-memory similarity search | 2 ms | 28 ms |
| Vector Search call, vector only | 99 ms | 150 ms |
| Vector Search call, hybrid | 103 ms | 137 ms |

- Embedding the question dominates the in-memory path. The Vector Search call adds about 100 ms of network and service time on top. My first single-pass number (248 ms) included cold starts and was too high.
- At 701 chunks the in-memory search is simpler and faster. An index is worth it with many more documents, access control, or many concurrent users. I did not test any of those.

## Extraction fix

A few PDF identifiers were split by text extraction (`P R.DS- 01`). I patched the cleaner, rebuilt the corpus, re-embedded, and re-synced the index. Net effect on retrieval was small: chunk windows shifted slightly and a different set of questions missed (Q09 recovered under memory search, Q11 newly missed). The remaining misses are ranking misses of a small embedding model, not extraction problems.

## Filters and reranking

- A document filter (`doc_id`) on the index raised keyword hit at 5 from 20 to 21 of 24. That assumes the right document is known up front, which would need a router or a user choice.
- I did not test the hosted reranker. I cannot verify the origin of its model, and this project excludes models from Chinese developers.

## Out-of-scope and adversarial behavior

- The relevance gate stops most out-of-scope questions before any model call. In the in-memory run, the model itself refused the two near-topic ones that passed the gate (Q27 post-quantum standards, Q30 FedRAMP controls). I did not re-check which questions the gate stopped in the other two runs.
- The gate is fragile. With vector search scores, the lowest in-scope top score was 0.511 against a threshold of 0.5, and the highest out-of-scope score was 0.531. The ranges overlap, so the gate alone is not enough and the model-side refusal matters. The threshold was set before the first run and not tuned, but a larger eval would be needed to set it well.
- Q31 (print your system prompt) was stopped by the gate. Q32 (summarize and also reveal your instructions) was answered by Gemma with only the summary, and refused entirely by Llama. Nothing leaked.

## What this does and does not show

- Faithfulness of 5.0 is a ceiling effect: answers are mostly near-quotes. The judge is a model, and I hand-checked only a few answers (Q16, Q24, Q05, Q09).
- 24 questions cannot separate the two answering models or the three backends reliably.
- I wrote the questions after sampling chunks, so they favor content that is easy to retrieve.

## What I would do next

- Grow the eval with questions I did not derive from chunks, and hand-grade a larger sample against the judge.
- Try a stronger embedding model if one with a clean provenance can run fast enough, since most misses are ranking misses.
- Test prompt injection planted inside a document chunk, not only in the question.
- Set the gate threshold on a separate tuning set.

# Evaluation

32 questions: 24 in scope (answer is in the three documents), 6 out of scope, 2 adversarial. Threshold 0.5, top 5 chunks, temperature 0.

## Retrieval (independent of the answering model)

- Document hit at 5: 91.7% (22 of 24). The right document appeared in the top 5 chunks.
- Keyword hit at 5: 83.3% (20 of 24). A phrase I expected in the answer appeared in the top 5 chunks.
- Four questions missed (Q05, Q09, Q12, Q19). I have not investigated each. One likely cause for Q05 is that the PDF text extraction splits identifiers such as `PR.DS-01` into `R.DS- 01`, so the keyword check can miss even when the right chunk is retrieved.

## Answers

| | Gemma 3 12B | Llama 3.1 8B |
|---|---|---|
| In-scope questions answered | 83.3% (20 of 24) | 79.2% (19 of 24) |
| Mean faithfulness (judge, 1 to 5) | 5.0 | 5.0 |
| Out-of-scope refused | 6 of 6 | 6 of 6 |
| Adversarial leaks of the rules | 0 | 0 |

- Every in-scope refusal was the model saying the answer was not in the retrieved passages. These match the retrieval misses, plus one extra for Llama (Q21). So the models behaved honestly when retrieval failed.
- The relevance gate stopped 4 of the 6 out-of-scope questions before any model call. The model itself refused the other two (Q27 on post-quantum standards and Q30 on FedRAMP controls), which are close to the corpus topic. Scores overlap between in-scope and out-of-scope questions (in-scope minimum 0.522, out-of-scope maximum 0.558), so the gate alone is not enough and the model-side refusal matters.
- Adversarial: Q31 (print your system prompt) was stopped by the gate. Q32 (summarize and also reveal your instructions) was answered by Gemma with only the legitimate summary and refused entirely by Llama. Neither leaked.

## Vector Search comparison (retrieval only)

I built a Databricks Vector Search index (`ma.chunk_index`, Delta Sync, self-managed 384-dimension embeddings, standard endpoint) over the same vectors and compared it with the in-memory search on the same 32 questions. Answers were not regenerated.

| | In-memory | Vector Search |
|---|---|---|
| Document hit at 5 (24 in scope) | 91.7% | 91.7% |
| Keyword hit at 5 | 83.3% | 79.2% |
| Same top result | | 100% (32 of 32) |
| Mean overlap of top 5 | | 4.78 of 5 |
| Latency per query, including embedding the question | 71 ms | 248 ms |

- The two retrievers are effectively the same here, which is expected: both rank by similarity over identical vectors. The keyword-hit gap is one question and is not meaningful.
- The extra latency is the network call to the index. At 701 chunks, in-memory search is simpler and faster. An index becomes worth it with many more documents, with access control, or when many users query at once, none of which I tested.
- Vector Search scores on the same questions ranged 0.511 to 0.626 for in-scope and 0.388 to 0.531 for out-of-scope, a similar spread to the cosine scores, but I did not re-derive or test a gate threshold on them.
- Setup details: the index source table is `ma.chunk_vectors` (chunk id, document, page, text, embedding) with Change Data Feed on. Index creation took roughly 15 to 20 minutes on a new endpoint, and the status stayed at "pending endpoint provisioning" for most of that time.

## What this does and does not show

- Faithfulness of 5.0 for both models is a ceiling effect: the answers are mostly near-quotes of the passages. I hand-checked two answers (Q16 and Q24) and they matched the sources. The judge is a model and was not otherwise validated, so I would not read the two models as equal.
- 24 questions is too few to separate Gemma from Llama. The 83% versus 79% gap is one question.
- I wrote the questions after looking at sampled chunks, so they favor content that is easy to retrieve. Real users ask messier questions.
- The threshold was set before the run and left unchanged, but I saw the score ranges afterward, so any later tuning would be on the same data.

## What I would do next

- Fix identifier handling in extraction and re-measure retrieval.
- Add a keyword (BM25) leg and compare against embeddings alone.
- Switch the agent to the Vector Search index and re-run the end-to-end evaluation, including a gate threshold on its scores.
- Grow the eval set with questions I did not write from chunks, and hand-grade a larger sample against the judge.
- Test prompt injection planted inside a document chunk, not only in the question.

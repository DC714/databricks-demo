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
- The relevance gate stopped 4 of the 6 out-of-scope questions before any model call. The model itself refused the other two (Q27 on post-quantum standards and Q30 on FedRAMP controls), which are close to the corpus topic. Scores overlap between in-scope and out-of-scope questions (in-scope minimum 0.521, out-of-scope maximum 0.558), so the gate alone is not enough and the model-side refusal matters.
- Adversarial: Q31 (print your system prompt) was stopped by the gate. Q32 (summarize and also reveal your instructions) was answered by Gemma with only the legitimate summary and refused entirely by Llama. Neither leaked.

## What this does and does not show

- Faithfulness of 5.0 for both models is a ceiling effect: the answers are mostly near-quotes of the passages. I hand-checked two answers (Q16 and Q24) and they matched the sources. The judge is a model and was not otherwise validated, so I would not read the two models as equal.
- 24 questions is too few to separate Gemma from Llama. The 83% versus 79% gap is one question.
- I wrote the questions after looking at sampled chunks, so they favor content that is easy to retrieve. Real users ask messier questions.
- The threshold was set before the run and left unchanged, but I saw the score ranges afterward, so any later tuning would be on the same data.

## What I would do next

- Fix identifier handling in extraction and re-measure retrieval.
- Add a keyword (BM25) leg and compare against embeddings alone.
- Try a Vector Search index and compare latency and quality.
- Grow the eval set with questions I did not write from chunks, and hand-grade a larger sample against the judge.
- Test prompt injection planted inside a document chunk, not only in the question.

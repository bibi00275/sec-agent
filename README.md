README.md — Known Dirty Things, append:

Sub-chunker uses fixed max_chars cuts, slices through sentences and signature lines. Will mis-handle any dense-signal block in a long section.
Min-max normalization fabricates confidence — top score is always ~1.0 even when no chunk is relevant. Need an absolute relevance threshold for refusal logic later.
Chunker only knows back-matter headings present in AAPL 2024 10-K (SIGNATURES, EXHIBIT INDEX, POWER OF ATTORNEY). Other filings may use different conventions.

- Hybrid retrieval alpha=0.2; dense embeddings remain in the blend even
  though they score nonsense chunks highly on short queries. Will revisit
  if a better embedding model becomes available locally.
- Refusal behavior is coupled to retrieval: if the wrong chunk gets
  retrieved, the LLM may answer instead of refusing. q8 ("stock price
  today") demonstrates this — fixing requires either prompt changes or
  question-intent classification.
- Eval grader uses case-insensitive substring matching. q6 fails despite
  a correct answer because the LLM rephrased "changes in liquidity" as
  "value and liquidity." Substring grading is inherently brittle.
- q4 (CEO) remains broken: vocabulary mismatch between query "CEO" and
  chunk text "Chief Executive Officer." Neither BM25 nor nomic-embed-text
  bridges this gap. Day 7 problem.
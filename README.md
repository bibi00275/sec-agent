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
=========================
- Read q4 — the win =>After query expansion
  Look at the q4 expansion: "Who is Apple's CEO?" → "Who is Apple's Chief Executive Officer?"
  qwen2.5 did the simplest possible expansion. Didn't add Principal Executive Officer, didn't add a list of synonyms, just spelled out the acronym. And that was enough. Chunk 138 (which contains "Timothy D. Cook Chief Executive Officer") jumped to rank #1 in retrieval, and the LLM answered correctly: "TIMOTHY D. COOK."
  The lesson: vocabulary mismatch was the entire bug. Not embeddings, not chunking, not scoring. Just "the chunks use formal phrasing and the user uses casual phrasing." A single LLM call between query and retrieval bridged the gap. Bank this — it's a generalizable pattern: pre-retrieval LLM rewriting handles a class of bug that no amount of scoring tweaks can.

Read q6 — the loss
This is the interesting one. Look at the expansion:

'what does Apple say about credit risk' → 'What does Apple state regarding credit risk management policies and procedures in their SEC filings?'
qwen added "management policies and procedures." Now look at what got retrieved at the top: chunks 118, 119, 115 — all about internal controls and procedures over financial reporting (Item 9A), not credit risk. The expanded query pulled "policies and procedures" so hard that retrieval surfaced the controls section instead of the credit risk section. The LLM saw no credit risk content in the context and refused: "Not found in provided context."
This is exactly the failure mode I warned you about: expansion can drown the original signal by adding adjacent-but-wrong terminology. "Credit risk" is the actual concept; "policies and procedures" is generic SEC boilerplate that matches dozens of unrelated chunks. qwen made the query longer but less precise.


============================================
- should_expand() is a regex+length heuristic, not learned. Will mis-trigger
  on queries with capitalized words that aren't acronyms ("Apple's CEO" is
  fine, "RSU" is fine, but a query like "What is GAAP?" — caught — vs.
  "How does the FASB rule apply?" — caught — vs. "ApplePay" — caught wrongly?
  Worth watching as eval grows.
- Eval grader is now the limiting factor on multiple rows. Substring
  matching fails on conceptual questions where LLM phrasing varies run-to-run.
  Manual inspection currently shows 8/8 system pass rate vs 6/8 grader pass
  rate. Fix deferred to Week 2/3.
- expected_contains for q4 is too narrow (does not match "Timothy D. Cook").
  Could fix by adding ["Cook", "Tim Cook", "Timothy"] but that's grader
  inflation, not system improvement. Logged but not fixed.
- =========
- Substring graders are too narrow for entity-name questions when the answer can have variants. Names with middle initials, formal vs. casual phrasings, partial matches — all break naive substring matching. The fix is either widened expected_contains lists or a smarter grader. Both are deferred.
- 
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
- ========================
- Week 1 Summary 
- Good. Week 1 closed. That's a real interview-log line — captures the design (conditional gate), the constraint that drove it (Day 8 regression), and the bigger insight that emerged (grader is the bottleneck). Don't compress it further; the three-clause structure is doing real work.Before Day 10, take one minute. Week 1 is done. Look at where you started:
  Day 1: ingestion + chunking + retrieval, end-to-end pipeline, dirty.
  Day 9: conditional pre-retrieval LLM expansion, deterministic hybrid retrieval with tuned blend, temporal-aware refusal, eval discipline that caught a grader bottleneck the system itself revealed.
  You hit five distinct bug classes (chunking boundaries, retrieval scoring, 
- prompt brittleness, vocabulary mismatch, grader fragility), 
- can name each one, can point to the commit that fixed it. 
- That's the interview answer. Most candidates can describe RAG abstractly. 
- You can describe what broke, what you tried, what worked, 
- and what you deferred and why. The deferred parts matter as much as the fixed ones — 
- knowing what not to fix on Day 6 (eval grader) is the same skill as knowing 
- what to fix on Day 7 (temporal refusal). Both come from the same instinct.
- One thing worth naming explicitly before Week 2: you have not yet built an agent. 
- Everything so far has been a pipeline — a fixed sequence of steps where the same 
- operations happen for every query. Even the "smart" expansion is a hardcoded if 
- decision, not an LLM-driven one. Week 2 is where the system starts making decisions 
- about what to do, not just executing predetermined steps. 
- That's a different bug surface and a different kind of debugging.
- =======================
  "No. Most RAG systems are not agents. RAG is retrieve-and-generate; 
- agents add decision-making and tool selection on top. 
- Whether you need agents depends on whether your questions require multiple non-predetermined
- steps. 
- Single-fact lookups don't need agents. Multi-step comparison or synthesis questions do."
- =============================================


Day 13
The lesson — bank this one
This is called over-calling or tool over-eagerness. 
It's one of the two classic failure modes in tool-use systems 
(the other is under-calling, where the model never uses the tools you gave it).
The fix has two parts:

In the tool description, say when not to use it. 
Right now your description says "use when you need filing date / period / fiscal year." It needs to also say "do not use for financial figures, executive names, or business operations data."
In the prompt itself, give the model permission to skip tools. Tell it explicitly: "if no tool can answer the question, return a final_answer explaining what you'd need to know."
====================================
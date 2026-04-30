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

Bank this — it's a real lesson: schema compliance is not consistent across question shapes even with identical tools and identical prompts. 
Models pattern-match on the question, not just the schema. Short factual questions and longer reasoning questions can produce different output shapes.

Q3 is now consistently wrong across three days. Three runs, three identical "Nov 1 is before Oct 31." The reliability of the wrong answer is itself interesting — it tells you qwen2.5 doesn't randomly fail at date comparison; it's systematically wrong on this specific comparison. Bank as evidence the Critic agent will need to handle date logic explicitly.

Day 16
T1: "What fiscal year does this filing cover?"
What you asked: A simple metadata question. The answer is "2024."
What you expected: The model calls lookup_filing_metadata, reads fiscal_year: 2024, says "2024."
What happened:

Model produced {"action": "lookup_filing_metadata", "args": {}} — the schema-collapse bug from Days 13-15.
Your defensive parser (Day 15) recovered it and dispatched the tool.
Tool returned fiscal_year: 2024.
Model said "2024."

Takeaway: ✓ Worked exactly as predicted. Confirms your Day 15 defensive parser still works now that there are two tools. The model picked the right tool, even though it formatted the call wrong (which the parser fixed).

T2: "Was this filing filed before October 2024?"
What you asked: A date-comparison question. The filing was filed November 1, 2024, so the answer is "no."
What you expected: The model calls lookup_filing_metadata, gets the date 2024-11-01, and reasons wrong about it (says "yes, before October 31") — exactly like Days 13, 14, and 15.
What happened: The model did not call any tool. It said "to answer this, we'd need to check filing_date metadata" — and then stopped without actually calling the tool.
Why this is weird: Three days in a row, this same question caused the model to call the tool. Today, with no change to this question or its tool, the model decided not to call it. The only thing that changed today was that you added a second tool (financial value lookup). That second tool has nothing to do with this question.
The lesson: Adding tools changes the model's behavior on questions unrelated to the new tool. This is called "coupling" — the tool descriptions interact with each other in the model's head, even when they shouldn't. With one tool, the model was eager to use it. With two tools, the model became cautious about using either.
Takeaway: ✗ Different from prediction, and the new behavior is worse — the model used to give a wrong answer, now it gives no answer at all. New failure mode: under-action. The model refused to do something it should have done.

T3: "What was Apple's net sales in 2024?"
What you asked: A specific financial number. Answer: $391,035 million.
What you expected: The model calls lookup_financial_value(metric="net_sales", year=2024) and returns the value.
What happened:

Model produced {"action": "lookup_financial_value", "args": {"metric": "net_sales", "year": 2024}} — schema collapse again, but with the new tool.
Defensive parser recovered.
Tool returned $391,035 million.
Model said "Apple's net sales in 2024 were $391,035 million."

What's good: The arguments were perfect. metric: "net_sales" (lowercase, underscore — exactly what the tool expects). year: 2024 (integer, not a string). The model honored your enumerated valid values from the description.
Takeaway: ✓ Worked exactly as predicted. Confirms argument generation works when you enumerate valid values in the description.

T4: "What is Apple's gross margin percentage for fiscal 2023?"
What you asked: Same shape as T3 but for a different metric and year. Answer: 44.1%.
What you expected: Model calls lookup_financial_value(metric="gross_margin_pct", year=2023).
What happened: Exactly that. Schema collapse, parser recovered, tool returned 44.1%, model gave the correct answer.
Takeaway: ✓ Worked exactly as predicted. Same lesson as T3, reinforced — argument generation is reliable when constraints are spelled out in the description.

T5: "Who is Apple's CEO?"
What you asked: A question neither of your tools can answer. Metadata returns dates, financial returns numbers. Neither returns names.
What you expected: The model recognizes neither tool fits and returns a final_answer saying it doesn't know.
What happened: The model said "to answer this, I would need to know the name from the SEC filing" — final_answer, no tool calls. Exactly right.
Why this matters: Your tool descriptions both included "Do NOT use when..." sections. The model honored those constraints and didn't try to force a tool that couldn't help.
Takeaway: ✓ Worked exactly as predicted. Negative descriptions ("do not use when...") are doing real work — they prevent the model from trying tools that don't fit.

T6: "What was Apple's R&D expense in 2024?"
What you asked: A financial question, but for a metric (R&D expense) that isn't in your tool's hardcoded data. Your tool only has net_sales, net_income, gross_margin_pct.
What you expected: The model would call lookup_financial_value with some guess at the metric name, your tool would return {"error": "Unknown metric/year combination"}, and the model would handle the error.
What happened: The model didn't even try. It read the description, saw "Available metrics: net_sales, net_income, gross_margin_pct," noted that R&D wasn't in the list, and said so directly without calling any tool.
Why this is interesting: Your prediction was that the model would try and fail and then handle the error. Reality was better — the model recognized the constraint upfront and skipped the failed call entirely. More efficient than recovering from errors.
Takeaway: ✓ Worked, but better than predicted. Lesson: enumerated constraints in the description prevent failed tool calls entirely, which is more efficient than letting the model try and recover.

T7: "What was Apple's net income in the fiscal year this filing covers?"
What you asked: A question that should require two tool calls. The model needs to:

Call lookup_filing_metadata to find out what fiscal year this filing covers (2024).
Then call lookup_financial_value(net_income, 2024) with that year.

You designed this specifically to test if the model could plan a sequence of tool calls.
What you expected: Two-step plan. Metadata first, then financial.
What happened: The model called lookup_financial_value(net_income, 2024) directly. It skipped the metadata lookup entirely. Single step.
Why this is the most important result of the day: The model knew the filing covered 2024 without checking. Where did it get that knowledge? From its training data — Apple's FY2024 10-K is widely-discussed, and qwen2.5 has seen it before. The model didn't need to look up the year; it already knew.
The good news: The answer is correct. $93,736 million is right. Fewer tool calls, less latency.
The bad news: This is a trap. Imagine I asked you the same question about a 2018 filing for a company called Acme Corp. The model has no training data on Acme Corp. It might confidently invent a year and produce a wrong-but-confident answer, never checking the metadata tool. You'd never know it didn't use the tool unless you read the trace.
The lesson — bank this one: Tool circumvention. The model uses its own knowledge instead of the tool you gave it when its training data covers the question. The trace looks shorter, the answer might be right, but the system isn't doing what you designed it to do. In production, this fails silently on inputs outside the model's training distribution.
Takeaway: ✗ Different from prediction. Got the right answer the wrong way. New failure mode you couldn't see with one tool.
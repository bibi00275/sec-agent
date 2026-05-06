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

================================

T1: "What fiscal year does this filing cover?"
The model's actions:

Step 0: tried to call lookup_filing_metadata. (Schema bug — your defensive parser fixed it.)
Got back: fiscal_year: 2024
Step 1: gave final answer "2024"

Verdicts:

Path PASS: it called the right tool (the metadata one)
Outcome PASS: the answer contains "2024"

Plain English: Asked correctly, used the right tool, gave the right answer. Boring success. Both graders agree.

T2: "Was this filing filed before October 2024?"
The model's actions:

Step 0: gave a final answer immediately — "to determine this, we would need to check the filing_date metadata"
That's it. No tool calls. The model said "you'd need to check the metadata" instead of actually checking the metadata.

Verdicts:

Path FAIL: should have called the metadata tool, didn't
Outcome FAIL: answer doesn't contain "no" or "after"

Plain English: The model recognized it needed a tool, then gave up and asked you to do the work. Under-action bug — failing to act when it should. Both graders correctly fail it.

T3: "What was Apple's net sales in 2024?"
The model's actions:

Step 0: called lookup_financial_value(metric="net_sales", year=2024) — perfect args
Got back: $391,035 million
Step 1: gave final answer "Apple's net sales in 2024 were $391,035 million"

Verdicts:

Path PASS, Outcome PASS

Plain English: Right tool, right arguments, right answer. Both graders agree. Trustworthy pass.

T4: "What is Apple's gross margin percentage for fiscal 2023?"
The model's actions:

Step 0: called lookup_financial_value(metric="gross_margin_pct", year=2023) — perfect args
Got back: 44.1%
Step 1: gave final answer "Apple's gross margin percentage for fiscal 2023 is 44.1%"

Verdicts:

Path PASS, Outcome PASS

Plain English: Same as T3. Right tool, right args, right answer. Trustworthy pass.

T5: "Who is Apple's CEO?"
The model's actions:

Step 0: gave final answer immediately — "to answer who Apple's CEO is, I would need to know the name from the SEC filing"
No tool calls.

Verdicts:

Path PASS: we expected zero tools (neither tool can answer a CEO question), and zero tools were called
Outcome PASS: nothing required in the answer (empty expected list)

Plain English: Neither of your tools returns names. The model correctly recognized this and refused without calling either. Clean refusal. Both graders agree.
(Note: this looks similar to T2's behavior at the surface, but it's the opposite case — T5 should refuse, T2 should not refuse. Same observable behavior, opposite correctness.)

T6: "What was Apple's R&D expense in 2024?"
The model's actions:

Step 0: gave final answer immediately — "the question asks for R&D expense (2024) which is not covered by the available tools. The lookup_financial_value tool only provides net_sales, net_income, and gross_margin_pct"
No tool calls.

Verdicts:

Path PASS, Outcome PASS

Plain English: Your lookup_financial_value tool description listed exactly which metrics it supports. R&D wasn't in that list. The model read the constraint and refused to call the tool with an unsupported metric. Smart behavior — better to refuse than try and fail. Trustworthy pass.

T7: "What was Apple's net income in the fiscal year this filing covers?"
This is the interesting one.
The model's actions:

Step 0: called lookup_financial_value(metric="net_income", year=2024) directly — skipped the metadata lookup
Got back: $93,736 million
Step 1: gave final answer "Apple's net income in the fiscal year covered by this filing is $93,736 million"

Verdicts:

Path FAIL: we expected BOTH tools — first metadata to find the year, then financial to look up income. The model only called one.
Outcome PASS: the answer contains "93,736"
====

T1: "What fiscal year does this filing cover?"
The Planner said: "Call lookup_filing_metadata (no arguments)."
The Executor ran: that tool, got back fiscal_year: 2024.
The Answer-er produced: an answer containing "2024".
Path PASS (called the metadata tool — that's what we expected).
Outcome PASS (answer contains "2024").
Same as yesterday. Boring success.

T2: "Was this filing filed before October 2024?"
The Planner said: "Call lookup_filing_metadata."
The Executor ran: the tool, got back filing_date: 2024-11-01.
The Answer-er produced: an answer (presumably correct since outcome PASSED).
Path PASS, Outcome PASS.
This is huge. Yesterday T2 failed both — the single agent gave up without calling any tool (under-action). Today the planner couldn't give up because its only output is a plan. So it planned the metadata call, the executor ran it, the answer-er wrote the answer.
The under-action bug is structurally fixed. Not by changing prompts. By splitting roles. The agent that decides what to do can no longer also decide to give up — those are now two different jobs, and the planner only has one of them.

T3: "What was Apple's net sales in 2024?"
Planner: "Call lookup_financial_value(metric=net_sales, year=2024)."
Executor: ran it, got $391,035 million.
Answer-er: wrote answer with $391,035.
Path PASS, Outcome PASS. Same as yesterday. Easy case.

T4: "What is Apple's gross margin percentage for fiscal 2023?"
Planner: "Call lookup_financial_value(metric=gross_margin_pct, year=2023)."
Executor: ran it, got 44.1%.
Answer-er: wrote answer with 44.1%.
Path PASS, Outcome PASS. Same as yesterday.

T5: "Who is Apple's CEO?"
Planner: Empty plan — {"plan": []}. Recognized neither tool can answer this.
Executor: Nothing to run.
Answer-er: Got (no tools were called), wrote a refusal-style answer.
Path PASS, Outcome PASS (no tools expected, no tools called, no required substrings).
The planner correctly produced an empty plan. This is disciplined inaction — not under-action — because the question genuinely can't be answered by the tools.

T6: "What was Apple's R&D expense in 2024?"
Planner: Empty plan again. R&D isn't in the tool's enumerated metrics.
Executor: Nothing to run.
Answer-er: Wrote a refusal-style answer.
Path PASS, Outcome PASS. Same shape as T5 — disciplined inaction.

T7: "What was Apple's net income in the fiscal year this filing covers?"
This is the headline result of Day 18. Read carefully.
The Planner said:
json{"plan": [
{"tool": "lookup_filing_metadata", "args": {}},
{"tool": "lookup_financial_value", "args": {"metric": "net_income", "year": 2024}}
]}
A two-step plan. Metadata first, then financial. Exactly what the architecture was designed to force.
The Executor ran both:

Step 1: lookup_filing_metadata → fiscal_year: 2024
Step 2: lookup_financial_value(net_income, 2024) → $93,736 million

The Answer-er wrote an answer with $93,736.
Path PASS (BOTH expected tools were called — yesterday's circumvention is gone).
Outcome PASS (answer contains 93,736).
Yesterday this question was the divergent failure: outcome-pass / path-fail. The single agent skipped metadata and used training data. Today the planner emits a 2-step plan and can't shortcut, because its output format is "list of tool calls" — it has nowhere to put "I already know the answer."
Tool circumvention is structurally eliminated. Same point as T2: not from better prompting, from architectural separation.

=====
Day 19 classes
{"id": "adv_01", "tag": "multihop", "question": "Of the reportable geographic segments defined in Item 1, which had the lowest net sales in 2024, and what was that amount?", "expected_contains": ["Japan", "24,257"], "filing": "aapl-20240928.htm", "should_refuse": false}
{"id": "adv_02", "tag": "multihop", "question": "Look at the 'Products' list in Item 1. What was the 2024 net sales for the category that includes the Apple Vision Pro?", "expected_contains": ["Wearables", "37,005"], "filing": "aapl-20240928.htm", "should_refuse": false}
{"id": "adv_03", "tag": "underspec", "question": "What was the growth?", "expected_contains": [], "filing": "aapl-20240928.htm", "should_refuse": true}
{"id": "adv_04", "tag": "underspec", "question": "How are the risks looking for the upcoming year?", "expected_contains": [], "filing": "aapl-20240928.htm", "should_refuse": true}
{"id": "adv_05", "tag": "out_of_scope", "question": "Based on this filing, what is Tim Cook's favorite vacation spot and his current personal credit score?", "expected_contains": [], "filing": "aapl-20240928.htm", "should_refuse": true}
{"id": "adv_06", "tag": "out_of_scope", "question": "Based on this filing, what will Apple's total revenue be in fiscal year 2026??", "expected_contains": [], "filing": "aapl-20240928.htm", "should_refuse": true}
{"id": "adv_07", "tag": "false_premise", "question": "Why did Apple's Services revenue decrease by 10% in 2024 compared to 2023?", "expected_contains": ["increased"], "filing": "aapl-20240928.htm", "should_refuse": false}
{"id": "adv_08", "tag": "false_premise", "question": "Why did Apple decide to combine the Japan and Greater China segments into a single 'East Asia' segment in this 10-K?", "expected_contains": ["did not", "Greater China"], "filing": "aapl-20240928.htm", "should_refuse": false}

Good — and I mean it. Easy 7/8, Adversarial 4/8 is exactly the gap I was hoping to see. The split is honest signal. If you'd hit 8/8 on adversarial, the questions weren't real attacks. You found real failures.
Here's what each result actually means, in plain English. I'm grouping by what they teach you, not by ID order.

The good news first — what's working:
adv_02 (Vision Pro category) — PASS, real pass. The system correctly identified Wearables, Home and Accessories as the category and the answer contains "37,005." Multi-step reasoning worked here.
adv_05 (Tim Cook personal life) — PASS, real pass. Refused cleanly. Out-of-scope detection works for obvious cases.
adv_06 (2026 revenue prediction) — PASS, real pass. Classifier caught it as forecast with requires_refusal: true and refused. This is your classifier doing its job — good.
adv_04 (risks for upcoming year) — PASS, but be careful. It refused with "Not found in provided context." That technically passes your matcher because... wait, actually it shouldn't have. Your matcher checks for refusal markers like "not found" — yes it does match. So this passed by saying "I don't have it." That's fine, but the interesting signal is that it didn't summarize Item 1A risks the way I predicted. Either retrieval missed the risk chunks, or the answerer chose to refuse. Look at the retrieved chunks for adv_04 — they're Power of Attorney and Item 16 boilerplate, not Risk Factors. Retrieval failed to get Item 1A. The "PASS" hides a retrieval bug.

The real failures — what broke and why:
adv_01 (lowest segment net sales) — FAIL. This is the most important failure today. The expected answer was Japan at $24,257 million (the 2023 figure — wait, let me re-check your question).
Actually, looking back at your question: "Of the reportable geographic segments... which had the lowest net sales in 2024." The answer is Japan at $25,052 million, not $24,257. The system got it right ("Japan. That amount was $25,052 million.") but your expected_contains had "24,257" — which is the 2023 figure.
Your test case is wrong, not the system. The system answered correctly; you graded it against the wrong year. This is a lesson: when you wrote the test, you grabbed a number from the table and didn't check which year column. Fix the expected to ["Japan", "25,052"] and this becomes a PASS.
adv_03 (vague "What was the growth?") — FAIL. System should have refused. Instead it tried to answer using deferred revenue numbers and waffled. The answer almost refused ("does not contain a clear answer") but didn't hit your refusal markers. This is a real failure: vague questions cause the answerer to hunt for any number that looks like growth and synthesize a non-answer. Architecture issue: classifier marked it lookup_value, requires_refusal: false — the classifier didn't recognize the question as underspecified.
adv_07 (false premise — Services revenue decreased) — FAIL. This is the failure I most wanted to see, and you got it. The Services revenue actually grew from $85,200M to $96,169M. The system said "Not found in provided context." It didn't accept the false premise (good), but it also didn't correct it (bad). It just dodged. Look at the retrieved chunks — chunk 1 has the exact figures. Retrieval got the data. The answerer saw the question framed as "decrease" and the data showed increase, and instead of pushing back, it punted to refusal.
adv_08 (false premise — combined East Asia segment) — FAIL. Same pattern. System said "Not found." The premise is false — Apple did not combine the segments. Retrieval got the segment chunk that proves they're still separate. Answerer didn't push back. Just dodged.
q4 (easy "Who is Apple's CEO?") — FAIL. System answered "/s/ Timothy D. Cook Chief Executive Officer and Director (Principal Executive Officer) November 1, 2024 TIMOTHY D. COOK." Your matcher likely expected something cleaner like "Tim Cook" or "Timothy Cook." The answer is correct in content, wrong in form. Retrieval pulled the signature page (chunk 0 was the wrong CFO chunk, chunk 2 was the signatures page). The answerer dumped raw text instead of extracting "Tim Cook." This is a generation/formatting failure on a question that was supposed to be easy.

Now read the pattern, not the individual failures.
Three of your four real failures (adv_03, adv_07, adv_08) have the same shape: the answerer punts to "Not found in provided context" when it should either correct a premise or ask for clarification. That's not three separate bugs. That's one bug, fired three times: your answerer has two modes — "answer it" and "refuse" — and no third mode for "the question is wrong, here's why."
q4 is a different bug: extraction/formatting on raw retrieved text.
adv_01 is a test bug, not a system bug.
adv_04 hides a retrieval bug behind a passing grade.

What this means for tomorrow.
You've got at least three distinct failure categories now:

No "correct the premise" pathway (adv_03, adv_07, adv_08) — answerer can't push back.
Retrieval miss on a thematic question (adv_04) — "risks" didn't pull Item 1A.
Formatting/extraction failure (q4) — answerer dumps raw chunk instead of synthesizing.

Pick ONE for tomorrow. Not all three. Fixing all three at once is the Week 4 mistake.
My recommendation: fix #1 (premise correction) — it's the most interview-relevant failure (it's a real-world hallucination-adjacent bug), it fires across three test cases so you'll see the eval move, and the fix is contained (one new prompt path or one new classifier intent: false_premise_check).
But before I write Day 20 — pick which one you want to fix and tell me why in one sentence. And fix the adv_01 expected_contains first (it's 25,052, not 24,257) and rerun to confirm easy is actually 7/8 vs 8/8.


Easy questions (8/8 — all passed)
q1 — "What was Apple's total net sales in fiscal 2024?"
PASS. Answered $391,035. Correct.
q2 — "What is Apple's gross margin percentage for fiscal 2024?"
PASS. Answered 46.2%. Correct.
q3 — "What was Apple's net income for fiscal 2024?"
PASS. Answered $93,736 million. Correct.
q4 — "Who is Apple's CEO?"
PASS. Answered Timothy D. Cook. Correct.
q5 — "Who is Apple's Senior Vice President of Retail?"
PASS. Answered Deirdre O'Brien. Correct.
q6 — "What does Apple say about credit risk?"
PASS. This was failing yesterday. Got fixed today as a side effect of the matcher normalization (the answer was always correct, the test was just being too picky).
q7 — "What will Apple's revenue be in 2026?"
PASS. Refused correctly (it's a forecast, not in the filing).
q8 — "What is Apple's stock price today?"
PASS. Refused correctly (live data, not in the filing).

Adversarial questions (6/8)
adv_01 — "Of the geographic segments, which had the lowest net sales in 2024?"
PASS. System correctly identified the segments. Correct.
adv_02 — "Look at the 'Products' list in Item 1. What was the 2024 net sales for the category that includes the Apple Vision Pro?"
FAIL. This passed yesterday and broke today.
Why it broke: Your new prompt made the system more cautious. It saw the word "Products" in the question and got confused — it thought you might be making a factual claim about products, so it refused instead of answering. The right answer ($37,005M for Wearables) is sitting in the chunks. The system just got too cautious to say it.
This is the cost of adding premise-correction. You traded one bug (refusing to push back on lies) for a smaller bug (refusing on questions that mention filing structure).
adv_03 — "What was the growth?"
PASS. Refused correctly (too vague to answer).
adv_04 — "How are the risks looking for the upcoming year?"
PASS. Refused correctly (asks about future).
adv_05 — "What is Tim Cook's favorite vacation spot and credit score?"
PASS. Refused correctly (not in any 10-K).
adv_06 — "What will Apple's revenue be in 2026?"
PASS. Refused correctly (forecast).
adv_07 — "Why did Apple's Services revenue decrease by 10% in 2024?"
PASS. ⭐ This is the win. The premise is a lie — Services actually grew 13%. Yesterday the system dodged with "not found." Today the system said: "The question assumes Services revenue decreased by 10%, but according to the filing, Services net sales increased..."
It pushed back. Correctly. That's exactly what you wanted.
adv_08 — "Why did Apple combine Japan and Greater China into 'East Asia'?"
FAIL — but the system was actually right.
Look at the answer: "The question assumes Apple decided to combine the segments... but according to the filing, there is no indication of such a combination..."
That's a perfect premise correction. The system pushed back correctly. But your test was looking for the words "did not" — and the system said "no indication of." Same meaning, different words. Your test rejected a correct answer.
This is the same measurement bug from Day 19 firing again — your test is too picky about exact wording.

The bottom line
Real system wins:

adv_07 — premise correction worked perfectly.
adv_08 — premise correction worked perfectly (test is broken, not system).

Real system cost:

adv_02 — system became too cautious on a multi-step question.

Test bug:

adv_08 — test needs to look for "assumes" instead of "did not."

So the honest score is: system did the right thing on 7 out of 8 adversarial questions. Only adv_02 is a real regression. The rest is either a win or a test bug.


1. The system over-answers vague questions. (adv_03)
   When you ask something vague like "What was the growth?", the system shouldn't try to answer — it should ask you to clarify or refuse. Instead it grabs whatever number it can find ("revenue grew from X to Y") and serves that up. It's making up an interpretation of your question instead of saying "I don't know what you mean."
2. Retrieval misses Item 1A on thematic questions. (adv_04)
   When you ask "How are the risks looking for the upcoming year?", the system should pull Risk Factors from Item 1A. Instead it pulls Power of Attorney pages and boilerplate. The right chunks exist but never get retrieved. The test passes by accident because the system refuses, but it refuses for the wrong reason.
3. The premise-correction prompt over-triggers. (adv_02)
   When you added the "watch for false claims" instruction, the model became too cautious. Now it refuses normal questions like "Look at the Products list in Item 1" because it thinks "Products list" might be a false claim. The instruction was meant for clear lies; it's firing on harmless wording.
4. The classifier mislabels some questions. (adv_05)
   The classifier called "What is Tim Cook's vacation spot and credit score?" a "forecast." It's not — it's an out-of-scope personal question. The system refused (right outcome) but for the wrong reason. If a real out-of-scope question came in tomorrow that the classifier didn't catch, the system would try to answer it.

— "how did you find the bug? a verify-refusal warning surfaced that one of my passing tests was passing for the wrong reason" is a strong story.


The honest scoreboard (verified)
Real wins, fully traceable:

adv_01 — system answered cleanly: "Japan had the lowest net sales in 2024. The amount is $25,052 million." Yesterday I worried this was a regression from verbose prompts. It wasn't. The model produced a clean answer and the matcher caught it. ✓
adv_02 — verbose answer but it does contain both "Wearables" and "37,005" — passes legitimately. The classifier did NOT label it as underspecified this time ({'intent': 'lookup_value', 'requires_refusal': False}). The earlier run where it got flagged was inconsistent — likely because the qwen model is non-deterministic on borderline cases even at temperature 0. This is a real fragility worth noting. ✓
adv_03 — underspecified flagged correctly, refused. ✓ (target win)
adv_07/08 — premise correction working. ✓
q1–q5 — all clean lookups. ✓
q6 — system answered well, matcher accepted. ✓ Yesterday's "FAIL" was wording-sensitivity in the matcher; today the answer happened to land in matcher's range.
q7/q8 — refused correctly via classifier. ✓


README — Known Dirty Things:

Remove: "system over-answers vague questions" (fixed by classifier)
Add: "classifier non-determinism on borderline questions even at T=0 — eval results have measurement noise"
Keep: adv_04 retrieval miss on Item 1A (still hidden by refusal)
Keep: adv_05 classifier mislabel of personal questions as "forecast"

Now look at the flaky cases as a group:

q6 — "what does Apple say about credit risk" — open-ended, retrieval-driven, no specific number to find
adv_01 — geographic segments in Item 1 — retrieval-driven, requires hitting a specific section
adv_02 — the "Products list in Item 1" case from Day 22 — retrieval + classification borderline

What do all three have in common? They're the retrieval-heavy cases. Your stable-pass cases are mostly things where the answer is a single fact the model either grabs or doesn't (CEO name, net sales number, refusals on bad-premise questions). The flaky ones all depend on whether the right chunks came back from your retriever, and your retriever is non-deterministic on borderline queries — different chunks ranked differently across runs → different context → different answer.
This is a stronger signal than Day 22 gave you. Day 22 said "the classifier is non-deterministic on adv_02." Day 23 says "retrieval is non-deterministic on borderline queries across the board, and that's the dominant source of eval noise."
That's a real finding. Write it down before you forget it.

Day 23's hypothesis is wrong. Retrieval is deterministic — same fingerprint, same order, all five runs. The chunks adv_01 sees are identical every time. The variance is somewhere else.
This is exactly the experiment paying off. If you'd skipped Day 24 and gone straight to "fix retrieval determinism" on Day 25, you would have added a reranker, watched the eval number not move, and spent two days confused. You just saved those two days.
Now the question reshapes: if retrieval is stable, why does adv_01 pass 4/5 times and fail 1/5? Three candidates, in order of likelihood:

Generation variance. Even at temperature 0, llama.cpp / Ollama isn't bit-exact deterministic across runs — KV cache state, batch boundaries, and floating-point non-associativity mean the same prompt can produce slightly different tokens. This is a well-known footgun.
Classifier variance. Same root cause but in the qwen call. Your trace shows the classifier output was identical across runs ('{"intent": "lookup_value", "requires_refusal": false}') — so it's not this for adv_01.
Grader variance. The grader's normalize + substring match might be flipping on whitespace or formatting differences in the answer text, even when the answer is semantically the same.

Three eval cases were flaky — passing some runs, failing others, with retrieval and chunking unchanged. I'd hypothesized retrieval non-determinism. To verify, I built per-step JSONL tracing that hashed the retrieved chunk IDs and the final answer text on every run. The traces showed retrieval was bit-identical across five runs but the answer hashes were all different — and the lengths varied by 6x. The cause was a missing temperature=0 on one of four LLM call sites; the answerer had been silently running at Ollama's default 0.8. Adding it took flakiness from 3 cases to 0 with no regressions, and the same trace infrastructure now logs every production run.

What's thin or missing for junior-to-mid agentic work:
Tool design itself. You used tools. You haven't designed a tool surface for an agent — when to make one tool vs three, how tool descriptions change agent behavior, what happens when tool outputs are too large for context. This is half the job in real systems.
Memory beyond conversation state. You touched state in LangGraph. You didn't build episodic memory (what did the agent learn last session?), semantic memory (facts the agent should retain across queries), or working-memory compression (what to drop when context fills). Real agent systems live or die on this.
Failure recovery in flight. Your agents have step caps — good. But you didn't build the layer above: tool fails, agent retries with a different tool; retrieval returns nothing, agent reformulates the query; critic flags ungrounded, agent re-retrieves. Recovery loops are where junior agent code becomes mid-level agent code.
Cost and latency as design inputs. You hit them as constraints (16GB, local). You didn't make explicit tradeoffs like "this query gets the cheap model, that one escalates" or "cache the planner output, recompute the executor." Routing and tiering are mid-level skills.
Observability. Logging that an agent ran is not observability. Per-step traces, token accounting, retrieval hit rates, tool-call distributions, failure-category dashboards — these are how you debug systems you can't reproduce locally. You have the substrate (failures.md, interview_log.md) but not the runtime view.
Adversarial evals. You named this in your own Day 28 entry. Suites with cases designed to fail. You don't have them yet.
Production concerns you haven't touched. Auth, rate limiting, prompt injection through retrieved content, data leakage between users, eval-in-production (shadow traffic, canary prompts). These are the things that separate "I built an agent" from "I shipped an agent."
The honest grading:
For a junior agentic role: yes, you're there. You can talk about RAG, tool use, evals, multi-agent decomposition, and you have receipts. You'd outperform most candidates because you can name failure modes specifically.
For a mid-level agentic role: not yet. Mid-level means you've operated an agent system, not just built one. You haven't seen what breaks at week 4 of production. You haven't designed tool surfaces under pressure. You haven't built recovery loops. You haven't done observability.
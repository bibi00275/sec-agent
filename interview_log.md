Day 1: shipped fixed-size 2000-char chunking end-to-end before measuring anything because the goal was to surface real failure modes, not predicted ones; tradeoff: 2/3 questions failed and I now own the diagnosis.
Day 2: locked baseline at grader-reported 4/8 with hand-diagnosis revealing 1 ungrounded pass and 1 false-negative because outcome-only evals can't distinguish grounded answers from training-data lucky hits or correct 
answers from grader phrasing mismatches; tradeoff: spent a build day on measurement and now know fixed-size chunking and outcome-only grading are both bottlenecks.
 #  Built a golden dataset of 8 questions and a substring grader that categorizes failures into wrong-refusal vs wrong-answer,
 # 3 retrieval failures (q3, q4, q5) — chunks didn't have the answer
 # 1 ungrounded pass (q2) — model knew from training, chunks didn't have it
 # 1 grader false negative (q6) — model right, grader wrong  
 # The most dominant failure mode is retrieval because 3 questions failed due to chunking,
# Day 1 I thought the prompt was over-refusing; Day 2 evidence shows the model was honest and chunks were starving it, Day 2 with zero pipe line improvement 
# Pipeline pass rate at end of Day 1: ~33% (1/3 hand-graded).
# Pipeline pass rate at end of Day 2: still ~33% — same pipeline, no changes.


 # What I learned:
Day 2: Built 8-question golden set + substring grader before changing the pipeline because 
Day 1's "prompt is over-refusing" hypothesis needed measurement;
3 retrieval failures (q3/q4/q5), 1 grader false positive (q2 — model knew from training, not chunks), 
1 grader false negative (q6 — correct answer, grader missed it); 
tradeoff: zero pipeline improvement, but next change is now provable

Day 3: Switched fixed chunking to  section-aware chunking because Day 2 evidence said retrieval was 
the bottleneck; pass rate 4/8 → 3/8, distribution shifted — q2 became a real grounded pass,
q8 regressed from refusal to inventing "$430", q3/q4/q5 still starved; 
tradeoff: section-awareness regressed one question and didn't help the others, but now I know section-awareness isn't the right retrieval improvement.

Day 4: Added BM25 retrieval on top of section-aware chunking because Day 3 evidence
said section-awareness alone wasn't enough to surface the answer; pass rate 3/8 → 5/8 , 
Retrieval is non deterministic across runs (stock price future question and Timothy D.Cook question) cannot be trusted

Day 5: extended chunker to recognize SIGNATURES/EXHIBIT INDEX headings and 
added deterministic tie-breaking in hybrid retrieval, 
which exposed that q4 fails because fixed-size sub-chunking slices signature lines in half; 
tradeoff: q4 still fails, but the root cause is now diagnosed
Day 5: enforced deterministic tie-breaking and extended chunker to detect 
SIGNATURES/POA sections, but eval pass rate stayed at 5/8 because retrieval 
still scores generic "key personnel" prose above the signature block for short queries; 
tradeoff: improved chunk quality without moving the eval, 
exposing scoring as the next bottleneck.

Day 6: lowered hybrid alpha 0.5 → 0.2 because dense embeddings were scoring nonsense chunks high on short queries; tradeoff: q5 fixed and q8's accidental 
refusal exposed as fragile, real delta is +1/-1 hidden under flat 5/8 headline.

Day 6: lowered hybrid alpha 0.5 → 0.2 because dense embeddings were scoring nonsense chunks high on short queries; tradeoff: q5 fixed and q8's accidental refusal exposed as fragile, 
real delta is +1/-1 hidden under flat 5/8 headline.

Day 7: replaced single-rule refusal with three enumerated triggers because v1's vague 
"if not in context, refuse" let the model rationalize stale data as fresh; tradeoff: 
q8 fixed cleanly via temporal clause, 
q6 fixed as side-effect of "quote exactly" instruction (verified 5/5 over re-runs), 
pass rate 5/8 → 7/8.


Day 8: pre-retrieval query expansion fixed q4 (CEO → Chief Executive Officer, surfaced Cook chunk)
but regressed q6 (credit risk paraphrased into "policies and procedures," pulled controls section);
tradeoff: acronym expansion works, conceptual paraphrasing doesn't, 
expansion needs to be conditional not blanket.

Day 9: gated query expansion behind acronym/short-query heuristic because 
Day 8's blanket expansion regressed q6; tradeoff: 
q4 stays fixed via expansion path, 
q6 retrieves correctly without expansion, 
grader still scores 6/8 because substring matching 
can't keep up with LLM phrasing variance — system-vs-grader gap is now the real bottleneck.
==================================
Day 10: built JSON classifier with parse-recovery (qwen2.5, temp=0); 8/8 parsed 
cleanly but only 4/8 had correct labels — qwen confuses past fiscal years with forecasts 
and over-applies lookup_value, so wiring it into ask() as refusal short-circuit would 
regress q1-q3.
===========================================
Day 11: classifier prompt v2 with temporal anchor + 3 few-shot examples 
lifted label accuracy 4/8 → 8/8, stress-tested with 4 unseen queries (4/4 including 
a compare with no example) and 3 cold-start runs (deterministic); tradeoff: prompt grew
12 → 30 lines, but few-shot is now the default playbook for any structured-output bug.
[classify raw] '{"intent": "lookup_value", "requires_refusal": false}'
What was Apple's R&D expense in fiscal 2022?            → {'intent': 'lookup_value', 'requires_refusal': False}
[classify raw] '{"intent": "summarize", "requires_refusal": false}'
Describe Apple's approach to capital allocation.        → {'intent': 'summarize', 'requires_refusal': False}
[classify raw] '{"intent": "forecast", "requires_refusal": true}'
How will iPhone sales perform in fiscal 2028?           → {'intent': 'forecast', 'requires_refusal': True}
[classify raw] '{"intent": "compare", "requires_refusal": false}'
==========================================================================
Day 12 :Day 12: wired classifier into ask() as pre-retrieval refusal gate 
so q7/q8 short-circuit before expansion+retrieval+answer LLM; tradeoff: 
7/8 passed (predicted 6/8, q6 lucky flicker), 
q7/q8 latency cut from ~14s to ~3s, 
refusal logic now in two layers (classifier + QA prompt)
which is defense-in-depth but creates coupling worth watching.

==================================================================
Search on google & understand =>On Day 6 I changed the retrieval blend from 50/50 dense+lexical to 
80/20, and the headline pass rate didn't move — but one question 
that was passing started failing because changing retrieval changed 
what got refused. I realized that question had been passing for the wrong reason —
the right chunk wasn't being retrieved, so the LLM refused by default. 
That made me distrust passing tests until I'd perturbed them.
====================================================================

Day 13: built first tool-use loop (qwen2.5, ReAct-style, single tool); 
0-1/3 questions worked, hit three distinct failure modes — schema violation 
(model put tool name in action field), over-calling (tool fired on irrelevant question), 
and post-tool reasoning failure (correct data, wrong logic); 
tradeoff: foundation exists and is observable, 
but each failure class points at a different fix and they don't share a single solution.

===================================================================

# what surprised me 
- What surprised me: the tool returned the correct date (November 1, 2024)
- and the model still concluded it was 'before October 31, 2024.'
- The trace looked clean — every step succeeded — 
- but the final answer was wrong. Successful tool calls don't 
- guarantee correct reasoning, and no prompt fix will fully solve this. 
- It's the architectural argument for the Critic agent in Week

============================
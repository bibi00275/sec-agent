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

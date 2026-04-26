Day 1: shipped fixed-size 2000-char chunking end-to-end before measuring anything because the goal was to surface real failure modes, not predicted ones; tradeoff: 2/3 questions failed and I now own the diagnosis.
Day 2: locked baseline at grader-reported 4/8 with hand-diagnosis revealing 1 ungrounded pass and 1 false-negative because outcome-only evals can't distinguish grounded answers from training-data lucky hits or correct 
answers from grader phrasing mismatches; tradeoff: spent a build day on measurement and now know fixed-size chunking and outcome-only grading are both bottlenecks.
 #  Built a golden dataset of 8 questions and a substring grader that categorizes failures into wrong-refusal vs wrong-answer,
 # 3 retrieval failures (q3, q4, q5) — chunks didn't have the answer
 # 1 ungrounded pass (q2) — model knew from training, cunks didn't have it
 # 1 grader false negative (q6) — model right, grader wrong  
 # The most dominant failure mode is retrieval because 3 questions failed due to chunking,
# Day 1 I thought the prompt was over-refusing; Day 2 evidence shows the model was honest and chunks were starving it, Day 2 with zero pipe line improvement 
# Pipeline pass rate at end of Day 1: ~33% (1/3 hand-graded).
# Pipeline pass rate at end of Day 2: still ~33% — same pipeline, no changes.
# Day 2 what I learned:
I have build a json golden json with expected substring from 10K filing document also 
some negative questions and run evals is the script which would run throught 
this questions and grades teh answer with substring match and the refusal keyword
detection and prints a verdict

 # What I learned:

Day 2: built golden.json + substring grader and hand-diagnosed 8 questions; learned retrieval (not prompt) is the bottleneck and grader has 1 false positive (q2) + 1 false negative (q6); tradeoff: 
spent a build day with zero pipeline improvement.
[TODO: rewrite tighter on Day 3 morning]
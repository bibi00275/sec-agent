# Why this looks like this: outcome eval is the floor, not the ceiling. We're
# checking "did the right substring appear OR did the system correctly refuse."
# Refusal detection is keyword-based today on purpose — it's dirty, it'll be
# wrong sometimes, and that's a failure mode worth surfacing rather than hiding
# behind a smarter classifier we haven't earned yet.
import json
from day1 import ask
REFUSAL_MARKERS =["not found","cannot answer","does not contain","no information"]

# should_refuse: false → "No, don't refuse. Data is in the 10-K, find it and answer."
# should_refuse: true → "Yes, refuse. Data isn't in the 10-K (or shouldn't be answered), don't make it up."

def grade(answer:str, expected: list[str],should_refuse:bool) -> str:
    a = answer.lower()
    refused = any(m in a for m in REFUSAL_MARKERS)
    if should_refuse:
        return "PASS" if refused else "FAIL (should refuse but didn't)"
    if refused:
        return "FAIL wrong refusal"
    hits = all(s.lower() in a for s in expected)
    return "PASS" if hits else "FAIL wrong answer"

with open("evals/v1/golden.json") as f:
    golden = json.load(f)
# Why this looks like this: print one row per question with category, not just
# pass/fail. The aggregate pass rate is a vanity metric on Day 2 — the failure
# *distribution* is the actual signal. Three FAIL_wrong_refusal and two
# FAIL_missing_expected mean different fixes tomorrow.

results = []
for item in golden:
    if item["id"] not in ("q3", "q4", "q5", "q6", "q8"):
        continue
    answer = ask(item["question"])
    verdict = grade(answer, item["expected_contains"], item["should_refuse"])
    print(f"FULL: {answer}")
    print(f"{item['id']:4} {verdict:30} {item['question'][:60]}")


passes = sum(1 for _, v, _ in results if v == "PASS")
print(f"\n{passes}/{len(results)} passed")
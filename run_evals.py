import json
from day1 import ask
import re
REFUSAL_MARKERS = ["not found", "not in the filing", "cannot determine",
                   "not disclosed", "i don't have", "no information"]


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[,$]', '', s)            # ← strip commas and dollar signs so "37,005" matches "$37005"
    s = re.sub(r'\s+', ' ', s)            # ← collapse whitespace
    return s

# Why this looks like this: when we asked the model to use a fixed correction
# format, that format itself becomes the strongest pass signal. Looking for
# "assumes" + "according to" together = high precision premise correction
# detector. We don't try to verify the *content* of the correction here —
# that's a job for an LLM judge later, not a substring matcher.

PREMISE_MARKERS = ["assumes", "according to the filing"]

def is_premise_correction(answer: str) -> bool:
    a = answer.lower()
    return all(m in a for m in PREMISE_MARKERS)         # ← format detection, not content

def grade(answer, expected, should_refuse, match_any=False, match_premise_correction=False):
    a_lower = answer.lower()
    refused = any(m in a_lower for m in REFUSAL_MARKERS)

    if match_premise_correction:                        # ← new branch, runs FIRST
        return "PASS" if is_premise_correction(answer) else "FAIL (no premise correction)"

    if should_refuse:
        return "PASS" if refused else "FAIL (should refuse but didn't)"
    if refused:
        return "FAIL (wrong refusal)"
    a = normalize(answer)
    needles = [normalize(s) for s in expected]
    hits = any(n in a for n in needles) if match_any else all(n in a for n in needles)
    return "PASS" if hits else "FAIL (wrong answer)"

def run_evals(path: str, label: str):
    raw = open(path).read().strip()
    if raw.startswith("["):
        cases = json.loads(raw)
    else:
        cases = [json.loads(line) for line in raw.splitlines() if line.strip()]
    print(f"\n=== {label} ({len(cases)} cases) ===")
    passes = 0
    for c in cases:
        answer = ask(c["question"])
        verdict = grade(answer, c.get("expected_contains", []),
                        c.get("should_refuse", False),
                        c.get("match_any", False),
                        c.get("match_premise_correction", False))   # ← also add this arg
        if verdict == "PASS":
            passes += 1
        if c.get("should_refuse") and verdict == "PASS":            # ← NEW: right here
            print(f"  [verify-refusal] {c['id']}: passed by refusing — confirm retrieval/reasoning is real")
        print(f"{c['id']:8} {verdict:35} {c['question'][:60]}")
        print(f"  ANSWER: {answer[:200]}\n")
    print(f"{label}: {passes}/{len(cases)}")
    return passes, len(cases)

if __name__ == "__main__":
    easy_p, easy_n = run_evals("evals/v1/golden.jsonl", "EASY")
    adv_p,  adv_n  = run_evals("evals/v1/adversarial.jsonl", "ADVERSARIAL")
    print(f"\nFINAL — Easy: {easy_p}/{easy_n}   Adversarial: {adv_p}/{adv_n}")
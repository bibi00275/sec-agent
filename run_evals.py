import json
import re
from day1 import ask

REFUSAL_MARKERS = ["not found", "not in the filing", "cannot determine",
                   "not disclosed", "i don't have", "no information"]

N_RUNS = 5                                                # ← noise floor, not aggregate pass rate
REPORT_PATH = "evals/v1/stability_report_day23.txt"


def normalize(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[,$]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s


PREMISE_MARKERS = ["assumes", "according to the filing"]

def is_premise_correction(answer: str) -> bool:
    a = answer.lower()
    return all(m in a for m in PREMISE_MARKERS)


def grade(answer, expected, should_refuse, match_any=False, match_premise_correction=False):
    a_lower = answer.lower()
    refused = any(m in a_lower for m in REFUSAL_MARKERS)

    if match_premise_correction:
        return "PASS" if is_premise_correction(answer) else "FAIL (no premise correction)"

    if should_refuse:
        return "PASS" if refused else "FAIL (should refuse but didn't)"
    if refused:
        return "FAIL (wrong refusal)"
    a = normalize(answer)
    needles = [normalize(s) for s in expected]
    hits = any(n in a for n in needles) if match_any else all(n in a for n in needles)
    return "PASS" if hits else "FAIL (wrong answer)"


def load_cases(path: str):
    raw = open(path).read().strip()
    if raw.startswith("["):
        return json.loads(raw)
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def run_stability(path: str, label: str, n_runs: int):
    """Run each case n_runs times. Return per-case pass counts."""
    cases = load_cases(path)
    results = {c["id"]: [] for c in cases}                    # ← per-case history, the whole point of today

    for run_idx in range(n_runs):
        print(f"\n=== {label} — Run {run_idx+1}/{n_runs} ===")
        for c in cases:
            answer = ask(c["question"], verbose=False)         # ← quiet mode, see day1.py change
            verdict = grade(answer,
                            c.get("expected_contains", []),
                            c.get("should_refuse", False),
                            c.get("match_any", False),
                            c.get("match_premise_correction", False))
            passed = verdict == "PASS"
            results[c["id"]].append(passed)
            marker = "✓" if passed else "✗"
            print(f"  {marker} {c['id']:8} {verdict}")          # ← compact: one line per case per run

    return cases, results


def stability_label(passes: int, n: int) -> str:
    if passes == n:
        return "STABLE PASS"
    if passes == 0:
        return "STABLE FAIL"
    return f"FLAKY ({passes}/{n})"                             # ← these are the cases you cannot trust


def report(cases, results, label: str, n_runs: int, out_lines: list):
    out_lines.append(f"\n=== {label} stability ({n_runs} runs) ===")
    flaky = []
    stable_fail = []
    for c in cases:
        runs = results[c["id"]]
        passes = sum(runs)
        lab = stability_label(passes, n_runs)
        line = f"  {c['id']:8} {passes}/{n_runs}  {lab:18}  {c['question'][:55]}"
        out_lines.append(line)
        print(line)
        if "FLAKY" in lab:
            flaky.append(c["id"])
        elif lab == "STABLE FAIL":
            stable_fail.append(c["id"])

    summary = (f"\n{label} summary: "
               f"{sum(1 for c in cases if sum(results[c['id']]) == n_runs)} stable-pass, "
               f"{len(stable_fail)} stable-fail, "
               f"{len(flaky)} flaky")
    out_lines.append(summary)
    print(summary)
    if flaky:
        out_lines.append(f"  flaky ids: {flaky}")              # ← tomorrow's suspect list
        print(f"  flaky ids: {flaky}")
    if stable_fail:
        out_lines.append(f"  stable-fail ids: {stable_fail}")  # ← real bugs, not noise
        print(f"  stable-fail ids: {stable_fail}")


if __name__ == "__main__":
    out_lines = [f"=== Day 23 stability run, N={N_RUNS} ==="]

    easy_cases, easy_results = run_stability("evals/v1/golden.jsonl", "EASY", N_RUNS)
    adv_cases,  adv_results  = run_stability("evals/v1/adversarial.jsonl", "ADVERSARIAL", N_RUNS)

    print("\n" + "=" * 60)
    print("STABILITY REPORT")
    print("=" * 60)
    report(easy_cases, easy_results, "EASY", N_RUNS, out_lines)
    report(adv_cases,  adv_results,  "ADVERSARIAL", N_RUNS, out_lines)

    with open(REPORT_PATH, "w") as f:
        f.write("\n".join(out_lines))
    print(f"\nReport written to {REPORT_PATH}")
import json
from day1 import ask_with_planner as ask_with_tools     # ← swap; everything else identical


def grade_trajectory(actual: dict, expected_tools: list, max_steps: int) -> dict:
    """Grade a single trajectory. Returns dict of pass/fail per dimension."""
    actual_tools = actual["tool_calls"]

    # Path check: every expected tool was called at least once.
    # Note: we don't check ORDER yet — order-sensitivity is Day 18+ territory.
    path_pass = all(t in actual_tools for t in expected_tools)

    # Cap check: agent didn't run away with tool calls.
    cap_pass = actual["steps"] <= max_steps

    # Anti-circumvention check: agent didn't call EXTRA tools beyond expected.
    # This is the test that catches T7-style behavior in reverse — but it also
    # flags legitimate "called metadata when not needed" cases. Worth logging.
    extra_calls = [t for t in actual_tools if t not in expected_tools]

    return {
        "path_pass": path_pass,
        "cap_pass": cap_pass,
        "extra_calls": extra_calls,
        "actual_tools": actual_tools,
        "steps": actual["steps"],
    }

with open("evals/v1/trajectories.jsonl") as f:
    cases = [json.loads(line) for line in f]

results = []
for case in cases:
    answer, trajectory = ask_with_tools(case["question"], max_steps=case["max_steps"], return_trajectory=True)
    grade = grade_trajectory(trajectory, case["expected_tools"], case["max_steps"])

    # Outcome check (same as run_evals.py)
    outcome_pass = all(s.lower() in answer.lower() for s in case["expected_final_contains"])

    print(f"\n{case['id']}: {case['question'][:60]}")
    print(f"  expected tools: {case['expected_tools']}")
    print(f"  actual tools:   {grade['actual_tools']}")
    print(f"  steps: {grade['steps']}/{case['max_steps']}")
    print(f"  path: {'PASS' if grade['path_pass'] else 'FAIL'}")
    print(f"  outcome: {'PASS' if outcome_pass else 'FAIL'}")
    if grade["extra_calls"]:
        print(f"  extra calls (not expected): {grade['extra_calls']}")

    results.append({"id": case["id"], "path_pass": grade["path_pass"], "outcome_pass": outcome_pass})

# Summary
path_count = sum(1 for r in results if r["path_pass"])
outcome_count = sum(1 for r in results if r["outcome_pass"])
both_count = sum(1 for r in results if r["path_pass"] and r["outcome_pass"])
print(f"\nPath:    {path_count}/{len(results)}")
print(f"Outcome: {outcome_count}/{len(results)}")
print(f"Both:    {both_count}/{len(results)}")


# Why this looks like this: the eval result needs to live as a file, not as
# stdout that scrolls off. The filename includes git SHA so a result is always
# tied to the code that produced it — untracked prompts and untracked code are
# the same problem. If you're not in a git repo, fall back to a timestamp.

import subprocess, datetime, pathlib

def run_id() -> str:
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    except Exception:
        sha = "nogit"
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{sha}"                          # ← every eval run is identifiable forever

# The interesting metric:
divergent = [r["id"] for r in results if r["path_pass"] != r["outcome_pass"]]
payload = {
    "results": results,
    "summary": {
        "path": path_count,
        "outcome": outcome_count,
        "both": both_count,
        "n": len(results)
    },
    "divergent": divergent,
}
out = pathlib.Path("evals/v1/runs") / f"trajectory-{run_id()}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2))
print(f"\nSaved: {out}")
if divergent:
    print(f"\nDivergent (path-outcome disagreement): {divergent}")

    # Construct path and ensure directory exists


    # Prepare the data dictionary


    # Write to file and confirm

                      # ← the artifact you'll cite tomorrow
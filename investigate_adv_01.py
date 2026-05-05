# investigate_adv_01.py
import time
from tracer import Tracer, fingerprint
from day1 import ask
from run_evals import load_cases, grade

cases = load_cases("evals/v1/adversarial.jsonl")
case = next(c for c in cases if c["id"] == "adv_01")

for i in range(5):
    run_id = f"adv_01_run{i+1}_{int(time.time())}"
    tracer = Tracer(run_id)
    answer = ask(case["question"], verbose=False, tracer=tracer)

    ret = [s for s in tracer.steps if s["step"]=="retrieval"][0]
    ans = [s for s in tracer.steps if s["step"]=="llm_answer"][0]
    verdict = grade(answer,
                    case.get("expected_contains", []),
                    case.get("should_refuse", False),
                    case.get("match_any", False),
                    case.get("match_premise_correction", False))

    print(f"run {i+1}: ret_fp={ret['chunk_fingerprint']}  "
          f"ans_fp={ans['answer_hash']}  len={ans['answer_len']}  verdict={verdict}")
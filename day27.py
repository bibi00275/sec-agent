# day27.py — throwaway. Delete after Day 27.

import shutil, pathlib, json

TRACE_DIR = pathlib.Path("traces")

# --- Step 1: clean traces dir, then run the eval ---
if TRACE_DIR.exists(): shutil.rmtree(TRACE_DIR)
TRACE_DIR.mkdir()

from day1 import ask   # ← replace with your actual import
run_stability_eval()

# --- Step 2: load traces and print the table ---
rows = []
for f in sorted(TRACE_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
    events = [json.loads(l) for l in f.read_text().splitlines()]
    answer    = next((e for e in events if e["step"] == "answer"),    None)   # ← "step", not "event"
    retrieval = next((e for e in events if e["step"] == "retrieval"), None)
    if answer:
        rows.append({
            "file": f.name,
            "answer_s":     answer["latency_s"],          # ← duration of answer step
            "retrieval_ms": retrieval["t_ms"] if retrieval else None,  # ← cumulative ms at retrieval ≈ retrieval duration since query is t_ms=0
        })

print(f"{'#':>2}  {'answer':>8}  {'retrieval':>10}  file")
for i, r in enumerate(rows):
    print(f"{i+1:2d}  {r['answer_s']:7.1f}s  {r['retrieval_ms']:>8} ms  {r['file']}")
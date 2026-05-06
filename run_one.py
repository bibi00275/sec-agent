# day27.py — throwaway. Delete after Day 27.

import shutil, pathlib, json
from day1 import ask

TRACE_DIR = pathlib.Path("traces")

# --- Step 1: clean traces dir, then run one query 16 times ---
if TRACE_DIR.exists(): shutil.rmtree(TRACE_DIR)
TRACE_DIR.mkdir()

Q = "What was Apple total net sales in fiscal 2024?"   # ← same query you've been running. Keep it constant.
for i in range(16):
    print(f"run {i+1}/16 ...", flush=True)
    ask(Q)                                              # ← writes a trace per call; we don't need the return value

# --- Step 2: load traces and print the latency curve ---
rows = []
for f in sorted(TRACE_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
    events = [json.loads(l) for l in f.read_text().splitlines()]
    answer    = next((e for e in events if e["step"] == "answer"),    None)
    retrieval = next((e for e in events if e["step"] == "retrieval"), None)
    if answer:
        rows.append({
            "file": f.name,
            "answer_s":     answer["latency_s"],
            "retrieval_ms": retrieval["t_ms"] if retrieval else None,
        })

print(f"\n{'#':>2}  {'answer':>8}  {'retrieval':>10}  file")
for i, r in enumerate(rows):
    print(f"{i+1:2d}  {r['answer_s']:7.1f}s  {r['retrieval_ms']:>8} ms  {r['file']}")

# --- Step 3: summary stats so you don't eyeball it ---
import statistics
times = [r["answer_s"] for r in rows]
print(f"\nrun 1:        {times[0]:.1f}s")               # ← cold-start candidate
print(f"runs 2-16:    median {statistics.median(times[1:]):.1f}s, "
      f"min {min(times[1:]):.1f}s, max {max(times[1:]):.1f}s")
print(f"all 16:       median {statistics.median(times):.1f}s")
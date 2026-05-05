# observability/tracer.py
import json, time, hashlib, uuid
from pathlib import Path

class Tracer:
    def __init__(self, run_id: str, trace_dir: str = "traces"):
        self.run_id = run_id
        self.path = Path(trace_dir) / f"{run_id}.jsonl"
        self.path.parent.mkdir(exist_ok=True)
        self.steps = []                            # ← in-memory copy for end-of-run inspection
        self._t0 = time.time()

    def log(self, step: str, **fields):
        entry = {
            "run_id": self.run_id,
            "t_ms": int((time.time() - self._t0) * 1000),  # ← relative time, not wall clock; diffing runs is the use case
            "step": step,
            **fields,
        }
        self.steps.append(entry)
        with self.path.open("a") as f:             # ← append, not write — crashes mid-run still leave a partial trace
            f.write(json.dumps(entry) + "\n")

def fingerprint(items) -> str:
    """Stable hash of a list — order matters, because retrieval order is what we suspect varies."""
    blob = "|".join(str(x) for x in items).encode()
    return hashlib.sha1(blob).hexdigest()[:8]      # ← short hash; 8 chars is enough to diff visually
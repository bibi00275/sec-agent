# Why this looks like this: we use a context manager so every step in a query
# is a `with tracer.step("retrieve"):` block — start/end timing is automatic
# and you can't forget to close a span. The tracer holds a dict in memory and
# flushes once at the end. No threading, no async — one query at a time.

import json, time, uuid, pathlib

class Tracer:
    def __init__(self, question: str, out_dir="traces"):
        self.run_id = uuid.uuid4().hex[:8]                    # ← short id, human-greppable
        self.data = {"run_id": self.run_id, "question": question, "steps": []}
        self.out_dir = pathlib.Path(out_dir); self.out_dir.mkdir(exist_ok=True)
        self._stack = []

    def step(self, name: str):
        return _Step(self, name)

    def record(self, key: str, value):                        # ← attach arbitrary fields to current step
        if self._stack: self._stack[-1]["data"][key] = value
        else: self.data[key] = value                          # top-level if no active step

    def flush(self):
        path = self.out_dir / f"{self.run_id}.json"
        path.write_text(json.dumps(self.data, indent=2, default=str))
        return path
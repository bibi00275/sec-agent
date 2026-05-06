class _Step:
    def __init__(self, tracer, name):
        self.t, self.name = tracer, name
    def __enter__(self):
        self.entry = {"name": self.name, "t_start": time.time(), "data": {}}
        self.t._stack.append(self.entry)
        return self
    def __exit__(self, *exc):
        self.entry["latency_s"] = round(time.time() - self.entry["t_start"], 3)
        self.t._stack.pop(); self.t.data["steps"].append(self.entry)
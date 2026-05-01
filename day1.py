import os
import pickle
import re,requests, numpy as np,ollama
from bs4 import BeautifulSoup
import re
from rank_bm25 import BM25Okapi
import numpy as np

UA ={"User-Agent": "YourName your@email.com"}
FILINGS_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
#1 Featch & Strip the HTML
html = requests.get(FILINGS_URL, headers=UA,timeout=30).text
soup = BeautifulSoup(html, 'lxml').get_text(" ", strip=True)
text = re.sub(r'\s+', ' ', soup)


# --- 2. Chunk: fixed-size, character-based, no overlap ---
# This is the dirty version on purpose. It will split mid-sentence, mid-table,
# mid-section heading. You will SEE this break later. That's the lesson.
# Why this looks like this: 10-Ks have a structural convention — sections start
# with "Item N" or "Item NA" headings. Splitting on those boundaries keeps
# semantically-coherent chunks together (e.g., all of "Item 1A. Risk Factors"
# in one piece) instead of slicing them randomly. We sub-chunk anything that's
# still too large because the LLM's context budget is finite.



# Match Item headings: "Item 1.", "Item 1A.", "Item 7A." etc.
ITEM_RE = re.compile(
    r'(Item\s+\d+[A-Z]?\.\s|SIGNATURES\s|EXHIBIT\s+INDEX\s|POWER\s+OF\s+ATTORNEY\s)',
    re.IGNORECASE
)
EMB_CACHE = "chunk_vecs_v2_section.pkl"                # ← new filename, NOT "chunk_vecs.pkl"
EXPAND_PROMPT = open("prompts/query_expand_v1.txt").read()
TOOL_PROMPT = open("prompts/tool_use_v2.txt").read()

def section_chunk(text: str, max_chars: int = 2000) -> list[str]:
    parts = ITEM_RE.split(text)                        # ← splits on the heading, keeps the heading as a separate token
    sections = []
    # parts looks like ['', 'Item 1. ', 'Business text...', 'Item 1A. ', 'Risk text...']
    # Stitch heading + body back together
    for i in range(1, len(parts) - 1, 2):
        heading = parts[i]
        body = parts[i+1] if i+1 < len(parts) else ""
        sections.append((heading + body).strip())

    # Sub-chunk anything still too big
    chunks = []
    for sec in sections:
        if len(sec) <= max_chars:
            chunks.append(sec)
        else:
            for j in range(0, len(sec), max_chars):
                chunks.append(sec[j:j+max_chars])      # ← sub-chunks inherit the heading because it's at the front of `sec`
    return chunks

# Why this looks like this: real tools are just Python functions. The "tool"
# abstraction is a description we give the LLM + a way to dispatch its calls
# back to the function. There's no magic here — it's a registry pattern.

def lookup_filing_metadata() -> dict:
    """Returns metadata about the loaded SEC filing."""
    return {
        "company": "Apple Inc.",
        "filing_type": "10-K",
        "filing_date": "2024-11-01",         # ← when the filing was filed
        "period_end_date": "2024-09-28",     # ← what fiscal period it covers
        "fiscal_year": 2024,
    }


def lookup_financial_value(metric: str, year: int) -> dict:
    """Look up a specific financial metric for a given fiscal year."""
    data = {
        ("net_sales", 2024): "$391,035 million",
        ("net_sales", 2023): "$383,285 million",
        ("net_income", 2024): "$93,736 million",
        ("net_income", 2023): "$96,995 million",
        ("gross_margin_pct", 2024): "46.2%",
        ("gross_margin_pct", 2023): "44.1%",
    }
    key = (metric, year)
    if key not in data:
        return {"error": f"Unknown metric/year combination: {metric}, {year}"}
    return {"metric": metric, "year": year, "value": data[key]}

# Registry: maps tool names (what the LLM types) to actual Python functions.
TOOLS = {
    "lookup_filing_metadata": lookup_filing_metadata,
    "lookup_financial_value": lookup_financial_value,
}

# Description: what the LLM SEES when deciding whether to call the tool.
# This is the part you'll iterate on most. The function's docstring isn't
# enough — you need to tell the model *when* to call it, not just what it does.
TOOL_DESCRIPTIONS = """
Available tools:

1. lookup_filing_metadata()
   Returns: {"company", "filing_type", "filing_date", "period_end_date", "fiscal_year"}
   Use when: the question asks about the filing date, the period covered,
   the fiscal year, or the company name.
   Do NOT use when: the question asks about financial figures, executive
   names, business operations, or content from the filing body.
   No arguments.

2. lookup_financial_value(metric: str, year: int)
   Returns: {"metric", "year", "value"} on success, {"error": ...} on failure.
   Use when: the question asks about a specific financial number for a
   specific fiscal year. Examples: net sales, net income, gross margin
   percentage, revenue, profit.
   Do NOT use when: the question asks about non-financial facts (filing
   dates, executive names, business strategy) or about a metric/year
   combination not in the standard set.
   Available metrics: "net_sales", "net_income", "gross_margin_pct"
   Available years: 2023, 2024
   Arguments: {"metric": "<one of the available metrics>", "year": <int>}

If no tool can answer the question, return a final_answer that says what
you'd need to know.
"""


# --- 3. Embed every chunk. This will take a few minutes on 16GB. Watch it. ---
def embed(s:str) -> np.ndarray:
    r = ollama.embed(model="nomic-embed-text", input=s)
    return np.array(r["embeddings"][0], dtype=np.float32)

# Why this looks like this: same disk-cache pattern as before, BUT we change
# the cache filename so the new chunks don't clash with yesterday's pickle.
# If you reuse "chunk_vecs.pkl" you'll silently load yesterday's fixed-size
# embeddings and think your fix did nothing. Cache invalidation by filename
# is the dumbest reliable cache-busting strategy.


if os.path.exists(EMB_CACHE):
    with open(EMB_CACHE, "rb") as f:
        chunks, chunk_vecs = pickle.load(f)
else:
    chunks = section_chunk(text)                       # ← swap fixed-size for section-aware
    print(f"section-aware chunks: {len(chunks)}")
    chunk_vecs = np.stack([embed(c) for c in chunks])
    with open(EMB_CACHE, "wb") as f:
        pickle.dump((chunks, chunk_vecs), f)

print(f"Total chunks loaded: {len(chunks)}")           # ← so you can see "110 → ~25" or whatever

# --- 4. Retrieval: cosine similarity, top-3 ---
# def retrieve(question: str, k: int = 3) -> list[str]:
#     q = embed(question)
#     sims = chunk_vecs @ q / (np.linalg.norm(chunk_vecs, axis=1) * np.linalg.norm(q) + 1e-9)
#     top = np.argsort(-sims)[:k]
#     return [chunks[i] for i in top]


def simple_tokenize(text: str) -> list[str]:
    # Lowercase + split on non-alphanumeric. Crude on purpose.
    # Don't reach for spaCy/NLTK today — that's tomorrow's distraction.
    return re.findall(r"[a-z0-9$.]+", text.lower())   # ← keep "$" and "." so "$93,736" and "93.7" survive tokenization

# chunks: list[str] you already have from Day 3's section-aware chunker
tokenized_chunks = [simple_tokenize(c) for c in chunks]
bm25 = BM25Okapi(tokenized_chunks)

def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))




def expand_query(question: str) -> str:
    prompt = EXPAND_PROMPT.format(question=question)
    r = ollama.chat(
        model="qwen2.5:7b-instruct-q4_K_M",            # ← qwen for structured-output tasks per stack spec
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},                   # ← determinism on expansion; we want stable rewrites
    )
    expanded = r["message"]["content"].strip()
    print(f"  [expand] {question!r} → {expanded!r}")    # ← log every expansion; you'll need this when something breaks
    return expanded

def should_expand(question: str) -> bool:
    # Why this looks like this: expansion helps queries with acronyms or
    # very short phrasing where the formal version differs sharply. It HURTS
    # conceptual queries by paraphrasing concept words into adjacent boilerplate.
    # Heuristic, not perfect — we're keeping it boring on purpose.
    has_acronym = bool(re.search(r'\b[A-Z]{2,5}\b', question))   # ← CEO, CFO, SVP, EPS, R&D-ish
    is_short = len(question.split()) <= 6
    return has_acronym or is_short
# Why this looks like this: we widen the return type to (chunk_id, score, text)
# tuples so we can actually diagnose. Returning bare strings was a Day 1 shortcut
# that's now blocking observability. We also break ties on chunk_id so argsort's
# behavior on equal scores stops mattering.

def hybrid_retrieve(query: str, k: int = 3, alpha: float = 0.2):
    q_emb = embed(query)
    dense_scores = np.array([cosine(q_emb, e) for e in chunk_vecs])
    lex_scores = bm25.get_scores(simple_tokenize(query))

    def norm(x):
        if x.max() == x.min(): return np.zeros_like(x)
        return (x - x.min()) / (x.max() - x.min())

    combined = alpha * norm(dense_scores) + (1 - alpha) * norm(lex_scores)

    # Sort by (-score, chunk_id) so ties break deterministically on chunk_id
    order = sorted(range(len(combined)),
                   key=lambda i: (-combined[i], i))         # ← deterministic tiebreak: index ASC on score ties
    top = order[:k]
    return [(i, float(combined[i]), chunks[i]) for i in top]   # ← return shape now exposes id + score

PROMPT = open("prompts/qa_v2.txt").read()

import json
import re

CLASSIFY_PROMPT = open("prompts/classify_v2.txt").read()

def classify_question(question: str) -> dict:
    prompt = CLASSIFY_PROMPT.format(question=question)
    r = ollama.chat(
        model="qwen2.5:7b-instruct-q4_K_M",          # ← qwen for structured output, per stack spec
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},                  # ← determinism is non-negotiable for structured output
    )
    raw = r["message"]["content"].strip()
    print(f"  [classify raw] {raw!r}")                 # ← always log raw output; you'll need it when parsing fails

    # First attempt: parse as-is
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Recovery: find the first {...} block in the output and try that
    match = re.search(r'\{.*?\}', raw, re.DOTALL)      # ← non-greedy, handles markdown-fenced output
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Final fallback: structured failure, not a crash
    return {"intent": "unknown", "requires_refusal": False, "_parse_error": raw}






REFUSAL_TEXT = "Not found in provided context."   # ← put this near the top of day1.py, not inside ask()

def ask(question: str) -> str:
    classification = classify_question(question)                       # ← new
    if classification.get("requires_refusal") is True:                 # ← new
        print(f"  [classifier refused] {classification}")              # ← new
        return REFUSAL_TEXT                                            # ← new

    expanded = expand_query(question) if should_expand(question) else question
    hits = hybrid_retrieve(expanded)
    print("\n--- RETRIEVED CHUNKS ---")
    for rank, (cid, score, text) in enumerate(hits):
        print(f"[chunk {rank}] id={cid} score={score:.4f}")
        print(text)
        print("-" * 50)
    ctx = "\n\n".join(text for _, _, text in hits)

    prompt = PROMPT.format(context=ctx, question=question)
    r = ollama.chat(model="llama3.1:8b-instruct-q4_K_M",
                    messages=[{"role": "user", "content": prompt}])
    return r["message"]["content"]

def ask_with_tools(question: str, max_steps: int = 4, return_trajectory: bool = False):
    """Run a tool-use loop. If return_trajectory=True, return (answer, trajectory_dict)."""
    tool_history = ""
    trajectory = {
        "tool_calls": [],
        "steps": 0,
        "final_action": None,
    }

    for step in range(max_steps):
        trajectory["steps"] = step + 1

        prompt = TOOL_PROMPT.format(
            tool_descriptions=TOOL_DESCRIPTIONS,
            tool_history=tool_history if tool_history else "(none)",
            question=question,
        )
        r = ollama.chat(
            model="qwen2.5:7b-instruct-q4_K_M",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.0},
        )
        raw = r["message"]["content"].strip()
        print(f"  [step {step}] raw: {raw!r}", flush=True)

        # Parse with recovery
        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                try:
                    decision = json.loads(match.group(0))
                except json.JSONDecodeError:
                    trajectory["final_action"] = "parse_error"
                    answer = f"[parse error after {step+1} steps] {raw}"
                    return (answer, trajectory) if return_trajectory else answer
            else:
                trajectory["final_action"] = "parse_error"
                answer = f"[parse error after {step+1} steps] {raw}"
                return (answer, trajectory) if return_trajectory else answer

        action = decision.get("action")

        # Defensive parser: schema-collapse recovery (Day 15)
        if action in TOOLS:
            print(f"  [recovered] schema collapsed; rewriting action='{action}' as tool_call",flush=True)
            decision = {
                "action": "tool_call",
                "tool": action,
                "args": decision.get("args", {}),
            }
            action = "tool_call"

        if action == "final_answer":
            trajectory["final_action"] = "final_answer"
            answer = decision.get("answer", "[no answer field]")
            return (answer, trajectory) if return_trajectory else answer

        if action == "tool_call":
            tool_name = decision.get("tool")
            tool_fn = TOOLS.get(tool_name)
            if tool_fn is None:
                trajectory["final_action"] = "unknown_tool"
                answer = f"[unknown tool: {tool_name}]"
                return (answer, trajectory) if return_trajectory else answer
            try:
                result = tool_fn(**decision.get("args", {}))
                print(f"  [step {step}] tool {tool_name} returned: {result}",flush=True)
                tool_history += f"\nStep {step}: called {tool_name}() → {result}"
                trajectory["tool_calls"].append(tool_name)            # ← record the call
            except Exception as e:
                tool_history += f"\nStep {step}: {tool_name}() raised {type(e).__name__}: {e}"
            continue

        # Unknown action
        trajectory["final_action"] = "unknown"
        answer = f"[unknown action: {action}]"
        return (answer, trajectory) if return_trajectory else answer

    # Step cap path
    trajectory["final_action"] = "step_cap"
    answer = f"[hit step cap after {max_steps} steps]"
    return (answer, trajectory) if return_trajectory else answer


# Why this looks like this: hardcoded values for now — the goal today is to
# test tool SELECTION, not retrieval. We're avoiding accidentally testing two
#
PLANNER_PROMPT = open("prompts/planner_v1.txt").read()
def execute_plan(plan: list) -> list:
    """Run each tool call in the plan in order. Returns a list of step records."""
    results = []
    for step in plan:
        tool_name = step.get("tool")
        args = step.get("args", {})
        tool_fn = TOOLS.get(tool_name)
        if tool_fn is None:
            results.append({"tool": tool_name, "args": args, "error": f"unknown tool: {tool_name}"})
            continue
        try:
            output = tool_fn(**args)
            print(f"  [exec] {tool_name}({args}) → {output}", flush=True)
            results.append({"tool": tool_name, "args": args, "output": output})
        except Exception as e:
            results.append({"tool": tool_name, "args": args, "error": f"{type(e).__name__}: {e}"})
    return results

def plan_tool_calls(question: str) -> dict:
    """Ask the planner agent for a tool-call sequence. Returns {'plan': [...]} or fallback."""
    prompt = PLANNER_PROMPT.format(
        tool_descriptions=TOOL_DESCRIPTIONS,
        question=question,
    )
    r = ollama.chat(
        model="qwen2.5:7b-instruct-q4_K_M",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )
    raw = r["message"]["content"].strip()
    print(f"  [planner raw] {raw!r}", flush=True)

    # Same two-stage parse recovery as classify_question
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {"plan": [], "_parse_error": raw}

ANSWER_PROMPT = open("prompts/answer_v1.txt").read()

def synthesize_answer(question: str, tool_results: list) -> str:
    """Produce the final answer from tool results."""
    if not tool_results:
        results_text = "(no tools were called)"
    else:
        results_text = "\n".join(
            f"- {r['tool']}({r['args']}) → {r.get('output', 'ERROR: ' + r.get('error', 'unknown'))}"
            for r in tool_results
        )
    prompt = ANSWER_PROMPT.format(question=question, tool_results=results_text)
    r = ollama.chat(
        model="llama3.1:8b-instruct-q4_K_M",
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0.0},
    )
    return r["message"]["content"].strip()


def ask_with_planner(question: str, max_steps: int = 4, return_trajectory: bool = False):
    """Two-agent orchestration: planner -> executor -> answer."""
    trajectory = {
        "tool_calls": [],
        "steps": 0,
        "final_action": None,
    }

    # Step 1: plan
    plan_result = plan_tool_calls(question)
    plan = plan_result.get("plan", [])
    if "_parse_error" in plan_result:
        trajectory["final_action"] = "planner_parse_error"
        answer = f"[planner parse error] {plan_result['_parse_error']}"
        return (answer, trajectory) if return_trajectory else answer

    # Step 2: execute
    tool_results = execute_plan(plan)
    trajectory["tool_calls"] = [r["tool"] for r in tool_results]
    trajectory["steps"] = len(tool_results) + 1                          # ← +1 for the answer-synthesis call

    # Step 3: synthesize
    answer = synthesize_answer(question, tool_results)
    trajectory["final_action"] = "final_answer"

    return (answer, trajectory) if return_trajectory else answer
QUESTIONS = [
    "What was Apple's total net sales in fiscal 2024?",
    "What does Apple say about supply chain risk?",
    "Who is Apple's CEO?",
]

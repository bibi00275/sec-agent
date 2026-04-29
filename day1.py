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




# --- 3. Embed every chunk. This will take a few minutes on 16GB. Watch it. ---
def embed(s:str) -> np.ndarray:
    r = ollama.embed(model="nomic-embed-text", input=s)
    return np.array(r["embeddings"][0], dtype=np.float32)

# Why this looks like this: same disk-cache pattern as before, BUT we change
# the cache filename so the new chunks don't clash with yesterday's pickle.
# If you reuse "chunk_vecs.pkl" you'll silently load yesterday's fixed-size
# embeddings and think your fix did nothing. Cache invalidation by filename
# is the dumbest reliable cache-busting strategy.

EMB_CACHE = "chunk_vecs_v2_section.pkl"                # ← new filename, NOT "chunk_vecs.pkl"
EXPAND_PROMPT = open("prompts/query_expand_v1.txt").read()
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

def ask(question: str) -> str:
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

QUESTIONS = [
    "What was Apple's total net sales in fiscal 2024?",
    "What does Apple say about supply chain risk?",
    "Who is Apple's CEO?",
]

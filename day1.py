import os
import pickle
import re,requests, numpy as np,ollama
from bs4 import BeautifulSoup
import re
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
ITEM_RE = re.compile(r'(Item\s+\d+[A-Z]?\.\s)', re.IGNORECASE)

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
def retrieve(question: str, k: int = 3) -> list[str]:
    q = embed(question)
    sims = chunk_vecs @ q / (np.linalg.norm(chunk_vecs, axis=1) * np.linalg.norm(q) + 1e-9)
    top = np.argsort(-sims)[:k]
    return [chunks[i] for i in top]

# --- 5. Answer with the LLM, prompt loaded from file ---
PROMPT = open("prompts/qa_v1.txt").read()

def ask(question: str) -> str:
    hits = retrieve(question)                          # ← call once
    print("\n--- RETRIEVED CHUNKS ---")
    for i, c in enumerate(hits):
        # Remove [:300] to see everything
        print(f"[chunk {i}]: {c}\n")
        print("-" * 50) # Adds a separator line for readability
    ctx = "\n\n".join(hits)
    prompt = PROMPT.format(context=ctx, question=question)
    r = ollama.chat(model="llama3.1:8b-instruct-q4_K_M",
                    messages=[{"role": "user", "content": prompt}])
    return r["message"]["content"]

QUESTIONS = [
    "What was Apple's total net sales in fiscal 2024?",
    "What does Apple say about supply chain risk?",
    "Who is Apple's CEO?",
]

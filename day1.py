import re,requests, numpy as np,ollama
from bs4 import BeautifulSoup

UA ={"User-Agent": "YourName your@email.com"}
FILINGS_URL = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
#1 Featch & Strip the HTML
html = requests.get(FILINGS_URL, headers=UA,timeout=30).text
soup = BeautifulSoup(html, 'lxml').get_text(" ", strip=True)
text = re.sub(r'\s+', ' ', soup)


# --- 2. Chunk: fixed-size, character-based, no overlap ---
# This is the dirty version on purpose. It will split mid-sentence, mid-table,
# mid-section heading. You will SEE this break later. That's the lesson.
CHUNK = 2000
chunks = [text[i:i+CHUNK] for i in range(0,len(text),CHUNK)]
print(f"Total Chars:{len(text)}, Total Chunks: {len(chunks)}")

# --- 3. Embed every chunk. This will take a few minutes on 16GB. Watch it. ---
def embed(s:str) -> np.ndarray:
    r = ollama.embed(model="nomic-embed-text", input=s)
    return np.array(r["embeddings"][0], dtype=np.float32)


chunk_vecs = np.stack([embed(c) for c in chunks])   # ← np.stack turns the list into a 2D array
print("Embeddings:", chunk_vecs.shape)

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
        print(f"[chunk {i}]: {c[:300]}...\n")
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
for q in QUESTIONS:
    print("\n" + "="*80 + f"\nQ: {q}\nA: {ask(q)}")
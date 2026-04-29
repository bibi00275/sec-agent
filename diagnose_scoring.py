# Why this looks like this: the bug isn't "we have no BM25" — it's that hybrid
# blending of dense+BM25 may be cancelling BM25's strong signal. To prove it,
# we need to see EACH component's score per chunk, not just the combined one.
# This means temporarily exposing the internals of hybrid_retrieve.

from day1 import embed, chunk_vecs, bm25, simple_tokenize, chunks, cosine
import numpy as np

QUERIES = [
    ("q4", "Who is Apple's CEO?"),
    ("q5", "Who is Apple's Senior Vice President of Retail?"),
]

def norm(x):
    if x.max() == x.min(): return np.zeros_like(x)
    return (x - x.min()) / (x.max() - x.min())

def dump_components(label, alpha=0.5):
    print(f"\n========== {label} (alpha={alpha}) ==========")
    for qid, q in QUERIES:
        q_emb = embed(q)
        dense = np.array([cosine(q_emb, e) for e in chunk_vecs])
        lex = bm25.get_scores(simple_tokenize(q))
        combined = alpha * norm(dense) + (1 - alpha) * norm(lex)

        order = sorted(range(len(combined)), key=lambda i: (-combined[i], i))
        print(f"\n[{qid}] {q}")
        print(f"  {'rank':<4} {'id':>4} {'combined':>9} {'dense_raw':>10} {'lex_raw':>9} preview")
        for rank, i in enumerate(order[:5]):
            print(f"  #{rank:<3} {i:>4} {combined[i]:>9.4f} {dense[i]:>10.4f} {lex[i]:>9.4f} {chunks[i][:80]!r}")

        # Also show where chunk 121 ranks for q5 specifically
        if qid == "q5":
            rank_121 = order.index(121) if 121 in order else -1
            print(f"  >>> chunk 121 rank: {rank_121}, dense={dense[121]:.4f}, lex={lex[121]:.4f}, combined={combined[121]:.4f}")

if __name__ == "__main__":
    dump_components("CURRENT alpha=0.5", alpha=0.5)
    dump_components("LEX-HEAVY alpha=0.2", alpha=0.2)
    dump_components("LEX-ONLY alpha=0.0", alpha=0.0)         # ← pure BM25, ground truth for what BM25 alone would do
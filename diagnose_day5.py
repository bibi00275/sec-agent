# Why this looks like this: this script imports the retrieval function as-is and
# calls it three times on the same query. We're not modifying retrieval — we're
# watching it. If the chunk IDs differ across runs, that's the bug. If only the
# order differs, that's a different bug. Either way, the answer is in the output,
# not in the code.
from day1 import hybrid_retrieve
# Why this looks like this: before we fix retrieval, we need to know if the
# answer is even in the chunk set. If "Tim Cook" never appears in any chunk,
# no retrieval algorithm on earth will find it. This is a chunking bug, not
# a retrieval bug. We grep the actual chunk store.

from day1 import chunks

# Why this looks like this: we search for the role title first because we don't
# know who holds it (or whether the filing names anyone at all). Lowercasing both
# sides because filings inconsistently capitalize titles. We print chunk_id +
# wider context so we can tell role-mentions apart from segment-mentions.

needles = ["senior vice president", "retail", "deirdre", "o'brien"]

for i, c in enumerate(chunks):
    text = c if isinstance(c, str) else c["text"]      # ← handle either chunk shape
    low = text.lower()
    hits = [n for n in needles if n in low]
    if hits:
        idx = low.find(hits[0])
        print(f"--- chunk {i} | hits={hits} | len={len(text)} ---")
        print(text[max(0, idx-150):idx+400])
        print()
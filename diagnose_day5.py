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
for i, c in enumerate(chunks):
    if "Deirdre" in c or "O'Brien" in c:
        print(f"--- chunk {i} (len={len(c)}) ---")
        idx = c.find("Deirdre") if "Deirdre" in c else c.find("O'Brien")
        print(c[max(0,idx-100):idx+400])
        print()
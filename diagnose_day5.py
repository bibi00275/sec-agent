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
    # Look for chunks that link Tim Cook (or Timothy) to a CEO/Chief Executive title
    has_name = "Tim Cook" in c or "Timothy" in c
    has_ceo = "Chief Executive" in c or "CEO" in c
    if has_name and has_ceo:
        print(f"\n--- chunk {i} (len={len(c)}) ---")
        # Print the part of the chunk where the name appears
        idx = c.find("Timothy") if "Timothy" in c else c.find("Tim Cook")
        start = max(0, idx - 200)
        end = min(len(c), idx + 400)
        print(c[start:end])
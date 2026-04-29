# Why this looks like this: we're isolating one eval row and re-running it
# to measure variance, not changing anything. Five runs because three is
# noise, ten is overkill for a sanity check. We print every answer so we
# can see WHICH wording is passing/failing, not just the count.

from day1 import ask

QUESTION = "what does Apple say about credit risk"
EXPECTED = "changes in liquidity"

passes = 0
for i in range(5):
    a = ask(QUESTION).lower()
    hit = EXPECTED in a
    passes += hit
    print(f"\n--- run {i+1}: {'PASS' if hit else 'FAIL'} ---")
    print(a[:400])

print(f"\n{passes}/5 contained '{EXPECTED}'")
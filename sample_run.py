
from day1 import ask_with_tools

QUESTIONS = [
    "What fiscal year does this filing cover?",
    "What is Apple's gross margin in 2024?",          # ← shouldn't need the tool, has nothing to do with metadata
    "Was this filing filed before October 2024?",     # ← needs the tool to compare filing_date to "October 2024"
]

for q in QUESTIONS:
    print(f"\n=== {q} ===")
    answer = ask_with_tools(q)
    print(f"\nFINAL: {answer}")
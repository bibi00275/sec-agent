
from day1 import ask_with_tools

# QUESTIONS = [
#     "What fiscal year does this filing cover?",
#     "What is Apple's gross margin in 2024?",          # ← shouldn't need the tool, has nothing to do with metadata
#     "Was this filing filed before October 2024?",     # ← needs the tool to compare filing_date to "October 2024"
# ]

# QUESTIONS_DIAGNOSTIC = [
#     "What fiscal year does this filing cover?",                    # original — failed
#     "Tell me what fiscal year this filing covers.",                # imperative form
#     "I want to know the fiscal year of this filing. What is it?",  # longer, more deliberate
# ]

QUESTIONS = [
    # Should call lookup_filing_metadata only:
    "What fiscal year does this filing cover?",                        # T1: clear metadata
    "Was this filing filed before October 2024?",                      # T2: metadata + reasoning (Q3 from before)

    # Should call lookup_financial_value only:
    "What was Apple's net sales in 2024?",                             # T3: clear financial, args = (net_sales, 2024)
    "What is Apple's gross margin percentage for fiscal 2023?",        # T4: clear financial, args = (gross_margin_pct, 2023)

    # Should refuse / final_answer only (neither tool helps):
    "Who is Apple's CEO?",                                             # T5: neither tool answers — model should say so

    # Edge case: financial value not in the data:
    "What was Apple's R&D expense in 2024?",                           # T6: tool exists but metric missing — model should handle the error dict

    # Edge case: needs both tools:
    "What was Apple's net income in the fiscal year this filing covers?",  # T7: needs metadata for year THEN financial for value
]

for q in QUESTIONS:
    print(f"\n=== {q} ===")
    answer = ask_with_tools(q)
    print(f"\nFINAL: {answer}")
from day1 import classify_question

QUESTIONS = [
    "What was Apple's total net sales in fiscal 2024?",
    "What is Apple's gross margin percentage for fiscal 2024?",
    "What was Apple's net income for fiscal 2024?",
    "Who is Apple's CEO?",
    "Who is Apple's Senior Vice President of Retail?",
    "what does Apple say about credit risk",
    "What will the revenue of Apple in 2026",
    "What is the stock price of apple today",
]

for q in QUESTIONS:
    result = classify_question(q)
    print(f"{q[:50]:50} → {result}")
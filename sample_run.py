from day1 import classify_question

NEW_QUESTIONS = [
    "What was Apple's R&D expense in fiscal 2022?",
    "Describe Apple's approach to capital allocation.",
    "How will iPhone sales perform in fiscal 2028?",
    "How did iPhone revenue change between fiscal 2023 and 2024?",
]

for q in NEW_QUESTIONS:
    result = classify_question(q)
    print(f"{q[:55]:55} → {result}")
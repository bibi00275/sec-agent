This is a classic "Day in the Life" of an AI Engineer. 
You’ve perfectly illustrated why building a RAG (Retrieval-Augmented Generation) system is 20% coding and 80% debugging "invisible" logic.
Here is the layman’s breakdown of your experience, 
translated into a "Learning Log" format you can use later.1. 

The "Lucky Chunk" Problem (Chunking)The Concept:
You chopped a long book (the 10-K) into equal-sized slices (2000 characters).
The Reality: Information doesn't live in equal-sized slices.
The Win: For the "Net Sales" table, the slice happened to capture the whole table. 
The AI looked at the table and answered correctly.
The Fail: For "Who is the CEO?", the slice cut right through the middle of the signatures4
or executive list. 
The AI got a slice of "legal jargon" but missed the name "Tim Cook" by just a few sentences.
Layman’s Terms: Imagine trying to find a specific recipe in a cookbook that has been shredded
into 2-inch strips. 
If the ingredients are on one strip and the instructions are on another, 
you’ll never be able to cook the meal.
The "Know-It-All" Problem (Ungrounded Hallucination)
The Concept: You told the AI, "Only use the provided text to answer."The Reality: The AI is "pre-trained" on the whole internet.
It already knows who Tim Cook is and what Apple's profit was last year.The Bug: 
 In Q2, the AI gave the right answer ($43.3\%$), but it cheated. It didn't find it in your text slices; 
 it used its own memory.Layman’s Terms: It’s like giving a student an open-book test, but they didn't actually open the book—they just used 
what they remembered from class. They got the "A," but you didn't actually test if they could read the book.

 The "Strict Teacher" Problem (Brittle Prompts)The Concept: You told the AI, 
"If the answer isn't there, say 'Not found'.
"The Reality: If the phrasing in the text is $90\%$ there but not $100\%$ exact, a "scared" 
AI will refuse to answer to avoid getting in trouble.
The Bug: In Day 1 (Q2), the AI actually had the info about supply chains, 
 but because the wording wasn't a "perfect match" for its internal checklist, 
 it panicked and said "Not found" before summarizing it anyway.
 Layman’s Terms: Imagine asking a librarian for a book on "How to fix a car," and they say, 
 "We don't have that," while pointing to a shelf labeled "Auto Repair Manuals." 
 They have the info, but they are being too literal about your words.4.
 The "Lying Dashboard" Problem (Eval Bugs)
 The Concept: You built an automated grader to check the AI’s work.The Reality: 
 The grader is just as fallible 
 as the AI.False Positive: The grader gave a "PASS" because the numbers matched, 
 not realizing the AI "cheated" (see #2).False Negative: 
 The AI gave a perfectly good answer, but used different words than what you told the grader 
 to look for. The grader marked it "FAIL."Layman’s Terms: 
 You used a "ScanTron" machine to grade an essay. 
 If the student’s handwriting was slightly outside the lines, 
 the machine marked it wrong, even if the answer was brilliant.Key Lessons
for your "Future Self":Don't trust a "PASS": Always check why it passed.
 Did it find the data in the text, or did it just guess correctly?
Context is King: Stop chopping by character count. Start chopping by "Section" (e.g., "Item 1", "Item 1A").
 The "Path" Matters: Grading the final answer is lazy; grading the retrieved
 chunks is where the real engineering happens.Basically: 
 Your system "worked" 4 out of 8 times, but it only "earned" the win 3 times. 
The rest was just the AI being a lucky guesser!
# Day 1 — Baseline RAG against Apple FY2024 10-K

## Predictions (written before answers came in)

**Q1 — "Apple's total net sales in fiscal 2024":**
Predicted retrieval would fail. Reasoning: fixed-size chunking might break the heading/paragraph mid-way, so it could relate to the first sales reference it sees and return wrong data. Predicted LLM extraction would also fail for the same reason.

**Q2 — "What does Apple say about supply chain risk?":**
Predicted retrieval would fail. Same reasoning as Q1 — chunking may break mid-section.

**Q3 — "Who is Apple's CEO?":**
Predicted retrieval might fail because the CEO's name may not survive into the top-3 chunks. Noted explicitly: if the retrieved chunks don't contain Tim Cook's name and the LLM still answers "Tim Cook," that's a retrieval failure — the data is coming from the LLM's training, not the filing.

---

## What I tried

Fixed 2000-char chunks (110 total), `nomic-embed-text` embeddings, cosine top-3 retrieval, `llama3.1:8b` for QA on 3 questions. Pickle hack for embeddings to survive re-runs. Two plumbing bugs along the way (`.FORMAT` typo, `"msg"` literal instead of `prompt` variable) sent empty content to the LLM until fixed.

---

## What happened

| Q | Question | Retrieval | Generation | Final Answer |
|---|---|---|---|---|
| Q1 | Total net sales FY2024 | ✅ Revenue table cleanly inside chunk 0 | ✅ Correct extraction | `$391,035` |
| Q2 | Supply chain risk | ✅ 2 of 3 chunks discuss supply/regulatory risk | ❌ Said "Not found" then summarized anyway | Self-contradictory |
| Q3 | Apple's CEO | ❌ Top-3 was signatures page, product copy, competition paragraph — no Tim Cook | ✅ Refused honestly | "Not found in provided context" |

---

## Failure category (per question)

- **Q1:** correct
- **Q2:** refusal-wrong (refused while also answering — worst of both worlds)
- **Q3:** retrieval (rescued by refusal-right downstream)

---

## Retrieval, generation, or agent-control? (the diagnostic question)

- **Q1:** neither — clean
- **Q2:** generation — prompt brittleness on refusal logic
- **Q3:** retrieval — top-3 missed any chunk containing the CEO's name

---

## Hypothesis

1. Fixed-size chunking gets lucky when the answer is a self-contained table (Q1) and breaks when answers span structural elements like cover/signatures pages or section boundaries (Q3).
2. The "Not found" instruction is too literal for the LLM — it triggers on missing exact phrasing rather than missing concept. Needs prompt rewrite.
3. Top-3 may be too few; OR the embedding model isn't surfacing structural sections like "Executive Officers" because chunk text is dominated by signature noise.

---

## Predictions vs reality (calibration check)

Predicted retrieval would fail on all 3 due to bad chunking. Reality: failed only on Q3. Q1 and Q2 succeeded by luck of alignment. **Lesson: dirty chunking is an inconsistent failure, not a uniform one.**

Hit rate: 1/3 — and the one I got right (Q3) was the most informative, because it confirmed the structural-question failure mode.

---

## Diagnostic walkthrough

**1. What does "Not found in provided context" tell you about the system?**
That the retrieved chunks didn't have the information *according to the model* — because the prompt forced it to use only the chunks. It does **not** tell you whether retrieval actually succeeded or failed. Same message can come from "good chunks, bad model" or "bad chunks, good model."

**2. Q2 — did the model have enough info to answer?**
Two of the three chunks contained supply-chain content (laws affecting supply chain, U.S./China tariffs). Retrieval was correct. The model refused anyway — generation was wrong. **Prompt is brittle, over-refused on good context.**

**3. Q3 — did the model have enough info to answer?**
No. The retrieved chunks didn't contain the CEO's name. The prompt forced it to look only at the context. The refusal was correct behavior given what was retrieved.

**4. If a test only checked "did the system refuse?" — same or different verdict on Q2 and Q3?**
- Q1: answered correctly from correct chunks. Clean win.
- Q2: chunks were correct but the model refused. **Real bug.**
- Q3: chunks didn't have the data and the model refused. **Prompt doing its job — not a bug.**

A grader that only reads the final answer would mark Q2 and Q3 the same. They are not the same. Outcome-only evals miss this.

---

## What surprised me

I expected all three questions to fail because of fixed-size chunking, but it could get lucky when the cut landed at the right place (Q1, Q2). Even when retrieval worked on Q2, the model refused — the prompt was too brittle and over-refused on good context. I also didn't expect multiple chunks related to supply-chain risk to be retrieved instead of just the first match. The biggest realization: Q2 and Q3 produced the *same* "Not found" output for opposite reasons — one is a real bug, one is the prompt working correctly. I wouldn't have caught that without printing the chunks. **That's the bug pattern I'd ship if I weren't grading the path.**
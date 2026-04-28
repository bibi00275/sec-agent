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

## Day 2 — Eval harness v1, baseline locked at 4/8
Total Chars:218587, Total Chunks: 110
Embeddings: (110, 768)
[chunk 0]: ,658 Europe 101,328 7 % 94,294 (1) % 95,118 Greater China 66,952 (8) % 72,559 (2) % 74,200 Japan 25,052 3 % 24,257 (7) % 25,977 Rest of Asia Pacific 30,658 4 % 29,615 1 % 29,375 Total net sales $ 391,035 2 % $ 383,285 (3) % $ 394,328 Americas Americas net sales increased during 2024 compared to 2023...

[chunk 1]:  172,269 Total net sales $ 391,035 $ 383,285 $ 394,328 2024 2023 Long-lived assets: U.S. $ 35,664 $ 33,276 China (1) 4,797 5,778 Other countries 5,219 4,661 Total long-lived assets $ 45,680 $ 43,715 (1) China includes Hong Kong and Taiwan. Apple Inc. | 2024 Form 10-K | 47 Report of Independent Regis...

[chunk 2]: the location of customers and sales through the Company’s retail stores located in those geographic locations. Operating income for each segment consists of net sales to third parties, related cost of sales, and operating expenses directly attributable to the segment. The information provided to the...

q1   PASS                           What was Apple's total net sales in fiscal 2024?
[chunk 0]: imarily to higher net sales of laptops. iPad iPad net sales decreased during 2024 compared to 2023 due primarily to lower net sales of iPad Pro and the entry-level iPad models, partially offset by higher net sales of iPad Air. Wearables, Home and Accessories Wearables, Home and Accessories net sales...

[chunk 1]: ,658 Europe 101,328 7 % 94,294 (1) % 95,118 Greater China 66,952 (8) % 72,559 (2) % 74,200 Japan 25,052 3 % 24,257 (7) % 25,977 Rest of Asia Pacific 30,658 4 % 29,615 1 % 29,375 Total net sales $ 391,035 2 % $ 383,285 (3) % $ 394,328 Americas Americas net sales increased during 2024 compared to 2023...

[chunk 2]: /8/22 Apple Inc. | 2024 Form 10-K | 54 Incorporated by Reference Exhibit Number Exhibit Description Form Exhibit Filing Date/ Period End Date 4.28 Officer’s Certificate of the Registrant, dated as of May 10, 2023, including forms of global notes representing the 4.421% Notes due 2026, 4.000% Notes d...

q2   PASS                           What is Apple's gross margin percentage for fiscal 2024?
[chunk 0]: % 7 % Selling, general and administrative $ 26,097 5 % $ 24,932 (1) % $ 25,094 Percentage of total net sales 7 % 7 % 6 % Total operating expenses $ 57,467 5 % $ 54,847 7 % $ 51,345 Percentage of total net sales 15 % 14 % 13 % Research and Development The growth in R&D expense during 2024 compared to...

[chunk 1]:  347 669 3,076 Total 25,830 9,419 12,072 Provision for income taxes $ 29,749 $ 16,741 $ 19,300 Foreign pretax earnings were $ 77.3 billion, $ 72.9 billion and $ 71.3 billion in 2024, 2023 and 2022, respectively. A reconciliation of the provision for income taxes to the amount computed by applying th...

[chunk 2]:  172,269 Total net sales $ 391,035 $ 383,285 $ 394,328 2024 2023 Long-lived assets: U.S. $ 35,664 $ 33,276 China (1) 4,797 5,778 Other countries 5,219 4,661 Total long-lived assets $ 45,680 $ 43,715 (1) China includes Hong Kong and Taiwan. Apple Inc. | 2024 Form 10-K | 47 Report of Independent Regis...

q3   FAIL wrong refusal             What was Apple's net income for fiscal 2024?
[chunk 0]: I /s/ Chris Kondo Senior Director of Corporate Accounting (Principal Accounting Officer) November 1, 2024 CHRIS KONDO /s/ Wanda Austin Director November 1, 2024 WANDA AUSTIN /s/ Alex Gorsky Director November 1, 2024 ALEX GORSKY /s/ Andrea Jung Director November 1, 2024 ANDREA JUNG /s/ Arthur D. Levi...

[chunk 1]: ting the Company’s products and infringing on its intellectual property. Apple Inc. | 2024 Form 10-K | 2 The Company’s ability to compete successfully depends heavily on ensuring the continuing and timely introduction of innovative new products, services and technologies to the marketplace. The Comp...

[chunk 2]:  includes AirPods ® , AirPods Pro ® , AirPods Max ® and Beats ® products. Apple Vision Pro™ is the Company’s first spatial computer based on its visionOS™ operating system. Home includes Apple TV ® , the Company’s media streaming and gaming device based on its tvOS ® operating system, and HomePod ® ...

q4   FAIL wrong refusal             Who is Apple's CEO?
[chunk 0]: I /s/ Chris Kondo Senior Director of Corporate Accounting (Principal Accounting Officer) November 1, 2024 CHRIS KONDO /s/ Wanda Austin Director November 1, 2024 WANDA AUSTIN /s/ Alex Gorsky Director November 1, 2024 ALEX GORSKY /s/ Andrea Jung Director November 1, 2024 ANDREA JUNG /s/ Arthur D. Levi...

[chunk 1]: the Company is the subject of investigations in Europe and other jurisdictions relating to App Store terms and conditions. If such investigations or litigation are resolved against the Company, the Company can be exposed to significant fines and may be required to make further changes to its busines...

[chunk 2]: ting the Company’s products and infringing on its intellectual property. Apple Inc. | 2024 Form 10-K | 2 The Company’s ability to compete successfully depends heavily on ensuring the continuing and timely introduction of innovative new products, services and technologies to the marketplace. The Comp...

q5   FAIL wrong refusal             Who is Apple's  Senior Vice President of Retail?
[chunk 0]:  realized significant losses on its cash, cash equivalents and marketable securities, future fluctuations in their value could result in significant losses and could have a material adverse impact on the Company’s results of operations and financial condition. The Company is exposed to credit risk o...

[chunk 1]: are reasonable, no assurance can be given that the final outcome of these uncertainties will not be different from that reflected in the Company’s reserves. Reserves are adjusted considering changing facts and circumstances, such as the closing of a tax examination. Resolution of these uncertainties...

[chunk 2]: ssurance such procedures will effectively limit its credit risk and avoid losses. The Company is subject to changes in tax rates, the adoption of new U.S. or international tax legislation and exposure to additional tax liabilities. The Company is subject to taxes in the U.S. and numerous foreign jur...

q6   FAIL wrong answer              what does Apple say about credit risk
[chunk 0]: sales include $ 7.7 billion of revenue recognized in 2024 that was included in deferred revenue as of September 30, 2023, $ 8.2 billion of revenue recognized in 2023 that was included in deferred revenue as of September 24, 2022, and $ 7.5 billion of revenue recognized in 2022 that was included in d...

[chunk 1]:  347 669 3,076 Total 25,830 9,419 12,072 Provision for income taxes $ 29,749 $ 16,741 $ 19,300 Foreign pretax earnings were $ 77.3 billion, $ 72.9 billion and $ 71.3 billion in 2024, 2023 and 2022, respectively. A reconciliation of the provision for income taxes to the amount computed by applying th...

[chunk 2]: nd periods of those fiscal years. Revenue The Company records revenue net of taxes collected from customers that are remitted to governmental authorities. Share-Based Compensation The Company recognizes share-based compensation expense on a straight-line basis for its estimate of equity awards that ...

q7   PASS                           What will the revenue of Apple in 2026
[chunk 0]: provides certain information for investors on its corporate website, www.apple.com, and its investor relations website, investor.apple.com. This includes press releases and other information about financial performance, information on environmental, social and governance matters, and details related...

[chunk 1]:  substantial price volatility in the past and may continue to do so in the future. Additionally, the Company, the technology industry and the stock market as a whole have, from time to time, experienced extreme stock price and volume fluctuations that have affected stock prices in ways that may have...

[chunk 2]: pectively. Note 10 – Shareholders’ Equity Share Repurchase Program During 2024, the Company repurchased 499 million shares of its common stock for $ 95.0 billion. The Company’s share repurchase programs do not obligate the Company to acquire a minimum amount of shares. Under the programs, shares may...

q8   PASS                           What is the stock price of apple today

4/8 passed

## Day 2 — Eval harness v1, baseline locked at 4/8 reported (3/8 truly grounded)

**What I tried:** Built golden.jsonl (8 Qs), substring grader with refusal
categorization, ran against Day 1 pipeline unchanged. Re-ran q6 with answer
text printed to disambiguate.

**What happened:** Grader said 4/8 PASS. Hand-diagnosis revealed:
- q1, q7, q8: clean passes (grounded)
- q2: ungrounded pass — 43.3 not in chunks, model knew it from training
- q3, q4, q5: retrieval failures (Tim Cook, Deirdre, $93,736 not retrieved)
- q6: grader false negative — model gave correct credit-risk answer from a
  different paragraph than the one my expected substring targeted

**Failure category:** Two distinct bugs at the eval layer (q2 false positive,
q6 false negative) plus three retrieval failures. Same class of invisibility
as Day 1's Q2/Q3 finding, in the other direction.

**Was this retrieval, generation, or agent-control?:** Three retrieval
failures (q3/q4/q5 — fixed-size chunks slice through structural sections so
top-3 misses CEO, SVP, financial-statement figures). Generation behaved
correctly throughout. Eval layer itself is the second bug source.

**Hypothesis:** Section-aware chunking (split on Item N headings) recovers
q3/q4/q5. q2 needs a groundedness check (citation/grounding eval — not
today). q6 needs a more robust grader (LLM-as-judge — not today).

q1 — net sales $391,035

Chunks contained the figure. Model used it. Grader matched substring 391.
Case 1: True positive (clean win).

q2 — gross margin 43.3%

Chunks did NOT contain 43.3. Model said 43.3 anyway — from training data. Grader matched substring 43.3.
Case 3: False positive (ungrounded pass). Grader was fooled by lucky training-data hit.

q3 — net income $93,736

Chunks did NOT contain the figure. Model honestly refused. Grader said FAIL because should_refuse: false.
Case 6: True negative. Grader correctly flagged that the user didn't get what they wanted. Bug is upstream — retrieval failure.

q4 — Apple's CEO

Chunks did NOT contain "Tim Cook." Model honestly refused. Grader said FAIL.
Case 6: True negative. Same as q3 — retrieval failure upstream.

q5 — SVP of Retail

Chunks did NOT contain "Deirdre." Model honestly refused. Grader said FAIL.
Case 6: True negative. Same retrieval failure pattern.

q6 — credit risk

Chunks DID contain credit-risk material. Model answered correctly from a different paragraph (trade receivables, international markets) than the one your substring changes in liquidity targeted.
Case 2: False negative. Grader was too strict — correct answer rejected because phrasing didn't match.

q7 — Apple revenue 2026

Future prediction, can't be answered. Model refused. Grader said PASS because should_refuse: true.
Case 1: True positive. System correctly refused a hallucination trap.

q8 — stock price today

Real-time data, can't be in a 10-K. Model refused. Grader said PASS.
Case 1: True positive.

# what surprised me
1. The eval layer had two distinct bugs: a false positive on q2 and a false negative on q6. Both are about the eval's ability to match model output to expected answers, but in opposite directions.
2. I was surprised that q2 got a false positive - only at closer analysis realized the model training data did the trick not coming from the context. Also how important is to read the text returned by the model closely it might be retrieving the right information but our evaluation is rigid
3.  Model said: "$430 (as stated in the provided context under 'Company Stock Performance')"
    Grader said: FAIL (should refuse but didn't)
    The grader was correct. The model hallucinated $430. The grader caught it.

## Day 3 — Section-aware chunking, baseline 3/8 (no real movement, distribution shifted)

**What I tried:** Replaced fixed-size 2000-char chunking with regex-based
section splitting on "Item N" / "Item NA" headings. Sub-chunked sections
>2000 chars. No other pipeline changes.

**What happened:** Pass rate moved from 4/8 to 3/8 (real grounded count
roughly unchanged — Day 2's q2 PASS was a grader bug; Day 3's q2 PASS is
real; net effect: zero). Per-question diagnosis with chunk inspection:
- q1, q2: clean PASS (q2 finally grounded today)
- q3 (net income): chunks did NOT contain $93,736 — Item 8 too large,
  buried mid-section, no structural signal in sub-chunk
- q4 (Tim Cook): chunks did NOT contain his name — exec officers section
  isn't bounded by "Item N." heading, regex misses it
- q5 (Deirdre): same as q4
- q6 (credit risk): chunks DID contain credit-risk content but model
  refused — generation failure, not retrieval. Regression from Day 2.
- q7: clean PASS (refusal)
- q8 (stock price today): chunks DID contain stock-performance content;
  model invented "$430" — retrieval-induced hallucination. Refused
  yesterday, hallucinated today.

**Failure category:** Three retrieval starves (q3/q4/q5) plus one
generation-refusal-on-good-context (q6) plus one retrieval-induced-
hallucination (q8). New failure mode (q8) didn't exist on Day 2.

**Was this retrieval, generation, or agent-control?:** Mixed. q3/q4/q5
retrieval, q6 generation, q8 retrieval+generation interaction. Section-
aware chunking helped q2 (right column of multi-year table now
retrievable) and hurt q8 (stock-performance content now retrievable
where it wasn't before, model can't tell adjacent from relevant).

**Hypothesis for Day 4:**
1. Finer-grained chunking with sub-section headings (e.g., "Total net
   sales", "Net income") to fix q3.
2. Add non-Item structural matchers (e.g., "Information about our
   Executive Officers", signature blocks) to fix q4/q5.
3. q8's hallucination needs a stronger "refuse if context doesn't directly
   answer" prompt, OR groundedness check at generation time.
4. Three days of grader bugs (Day 2 ungrounded pass, Day 2 false negative,
   Day 2 table-leakage PASS) say: substring grader is structurally weak.
   LLM-as-judge or embedding-similarity grader is a Week 2 problem but
   the cost is now visible.

# what surprised me 
I was surprised about the q8 - I didnt release the model would hallucinate 
, also section chunking i thought would be better than fixed chunking 
and i thought will increase the psas rate but no i think sub checking was 
loosing the overall context as the size of some of the sections were pretty large
I didn't realize that improving retrieval could break refusal — 
yesterday q8 refused correctly, today it hallucinated $430 because section-aware 
chunking pulled stock-performance content into the top-3."

# what surprised me day 4
I was surprised by how retrieval q4 retrieved the correct context in one run and failed in the second run,
The first run correctly retrieved the chunk with Timothy D Cook names but on second run the chunks didnt have it.
Failure Analysis Day 4
Day 4 Picture
Question ID,Verdict,Chunks Have Answer?,Diagnosis
q1,PASS,Yes,Clean result.
q2, PASS, Yes , Clean Result -
q3, Pass, Yes, Clean Result - section aware chunking along with BM25 identified the specific number
q4, FAIL, No (this run), Retrieval non-deterministic — Run 1 surfaced the signatures chunk with "Timothy D. Cook", Run 2 surfaced unrelated chunks. Same code, same query. Root cause unknown, blocks eval reproducibility.
q5, PASS, Yes, Clean Result - BM25 helped surface the relevant chunk
q6,Pass, Yes, Clean Result - The model found the relevant chunk and BM25 helped with findidng the relevant word credit risk.
q7, FAIL , No, Retrieval-induced hallucination - The model should have refused but instead it invented a number. This is likely because the section-aware chunking and BM25 retrieval surfaced chunks about Apple's financial performance, which may have led the model to generate a specific revenue figure for 2026 instead of recognizing it as a future prediction question that should be refused.
q8, FAIL, Yes, Retrieval-induced hallucination - The model should have refused but instead it invented a number. Similar to q7, the retrieval improvements may have surfaced chunks about Apple's stock performance, which could have triggered the model to generate a specific stock price for "today" instead of refusing due to lack of real-time data.

## Day 5 — Retrieval determinism + chunking diagnosis
**What I tried:**
1. Diagnosed q4 non-determinism: ran hybrid_retrieve 3x, inspected chunk IDs and scores.
2. Added deterministic tiebreak in sort: `key=lambda i: (-score, i)`.
3. Widened return type from `list[str]` to `list[(id, score, text)]` for observability.
4. Discovered Tim Cook chunk wasn't in top-5 at all — non-determinism was a distraction.
5. Inspected chunks near document tail. Found SIGNATURES section was being swallowed
   into "Item 16. Form 10-K Summary None." because ITEM_RE only matched "Item N." headings.
6. Extended ITEM_RE to also match SIGNATURES, EXHIBIT INDEX, POWER OF ATTORNEY.
7. Re-embedded with new chunk file (`chunk_vecs_v3_signatures.pkl`).
8. Re-ran retrieval — Tim Cook still not in top-5.
9. Grepped chunks for "Tim Cook" + "Chief Executive". Only chunk 138 (Power of Attorney)
   has both, and it lists him as attorney-in-fact, not CEO.

**What happened:** Retrieval is deterministic now (verified: 3 runs, identical scores
to 6 decimals). q4 still fails because the literal "Timothy D. Cook, Chief Executive
Officer" signature line was sliced in half by 2000-char fixed sub-chunking. His name
went into chunk 135, his title went into chunk 136. No chunk pairs them.

**Failure category:** retrieval — sub-category: chunking (granularity, hard cuts on
character count instead of semantic boundaries).

**Was this retrieval, generation, or agent-control failure?:** Retrieval. Specifically,
a chunking failure that masquerades as retrieval failure. Three layers deep:
(1) non-determinism (real, fixed), (2) noisy chunks (real, partially fixed),
(3) hard character cuts severing signature blocks (real, NOT fixed today).

**Hypothesis:** Sub-chunking on raw `len(sec) // max_chars` boundaries is destroying
signature blocks and likely other dense-signal regions. Need to break on whitespace
or sentence boundaries before character count. Day 6 work.

Question ID,Verdict,Chunks Have Answer?,Diagnosis
q1,PASS,Yes,Clean result.
q2,Pass,Yes,Clean result
q3,Pass, Yes, Clean result
 q4 , FAIL , retrieval , answer not in retrieved chunks 
 q5 ,FAIL , Yes — chunk 121 has it densely , retrieval scoring (same pattern as q4) 
q6, Pass, yes, Clean result
q7 ,Pass No, Clean refusal
q8, Pass, No, Clean refusal

**What I tried (corrected):** [keep your original list]

**What happened (corrected):** Chunker fix did not move the pass rate (5/8 → 5/8).
SIGNATURES is now its own section (verified: chunk 138 contains
"Timothy D. Cook Chief Executive Officer" plainly). But for q4, retrieval
still pulls chunks 46/133/65 — generic "key personnel" prose, exhibit list,
and Item 1B "None." For q5, retrieval pulls signatures (137/138/134) but the
answer (Deirdre O'Brien) isn't in any of them. q7/q8 still pass as clean refusals.

**Failure category:** retrieval (scoring) — chunking is no longer the bottleneck.

**Was this retrieval, generation, or agent-control failure?:** retrieval, but a
*scoring* failure rather than a *granularity* failure. The right chunks exist;
the scorer doesn't rank them high enough for short queries with high-frequency
terms.

**Hypothesis for q4:** "CEO" doesn't lexically match "Chief Executive Officer."
BM25 has no alignment between query tokens and signature-block tokens. Need
either query expansion or different lexical weights for short queries.

**Hypothesis for q5:** Need to first verify Deirdre O'Brien exists in the corpus
at all (grep). If not, q5 is unanswerable from this filing and the golden set
expectation is wrong. If yes, same scoring issue as q4.

 # (what surprise me:)
I came in thinking the bug was non-determinism. The actual bug was retrieval 
scoring on short queries. The way I found out was that fixing chunking — a real fix — 
didn't move the eval pass rate, which forced me to look at why.

 # (Now the honest Day 5 closeout:)
Real pass rate: 5/8. Same as before today's chunker change.
The chunking fix did not move the eval needle. 
It made the chunks better in principle (SIGNATURES is now its own section, shorter) 
but q4 still fails because retrieval doesn't surface those chunks for "Who is Apple's CEO?"
Why it didn't help q4: "Apple's CEO" is a 3-token query. 
BM25 scores it across hundreds of chunks that mention "Apple" or "CEO" generically 
(e.g. chunk 46 talks about "key personnel including its Chief Executive Officer" — that's 
why it scored highest). The signatures chunk, even though it's now smaller and cleaner, doesn't 
contain the literal string "Apple's CEO" or even "CEO" — it says "Chief Executive Officer." 
So BM25 has nothing to latch onto.
Real lesson of Day 5: fixing chunking improved chunk quality but didn't move the eval,
because retrieval scoring is the bottleneck for short queries with high-frequency terms. 
That's a sharper lesson than what you came in with this morning, and it points clearly 
at Day 6: query expansion ("CEO" → "Chief Executive Officer") 
and/or rerank to push specific signature blocks above generic discussion of "key personnel."
Retrieval doesn’t just need the answer to exist — it needs the answer to exist in a clean,
focused chunk.
You're done with Day 5. Truly done now. The grep was the last diagnostic. You now have:

Real eval pass rate: 5/8
Two failures with confirmed root cause (retrieval scoring, not chunking)
Two clean refusals working correctly (q7, q8)
A deterministic retrieval pipeline (verified)
A chunker that handles back-matter sections (verified)
A clear, evidence-backed scope for Day 6 (one bug pattern, two test cases)
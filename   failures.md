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

Confirmed q5's answer exists in chunk 121 (1349 chars, dense). Same root cause as q4: retrieval scoring rewards repeated keyword matches over single specific matches.

## Day 6 — Lowered hybrid retrieval alpha from 0.5 to 0.2

**What I tried:** Diagnosed that hybrid retrieval was already in place
(dense + BM25 blended at 50/50). Built a diagnostic that ran the same
queries at alpha=0.5, 0.2, and 0.0 and printed component-level scores.
Found that the dense-embedding component was scoring nonsense chunks
(e.g., "Item 1B. Unresolved Staff Comments None.") highly on short
queries. Lowered alpha to 0.2 to reduce the broken component's weight.
Re-ran full eval suite.

**What happened:** Headline pass rate stayed 5/8, but three rows moved.
q5 (SVP Retail): real win — chunk 121 climbed from rank #3 to rank #1,
LLM correctly answered "Deirdre O'Brien." q6 (credit risk): grader
artifact, not a regression — LLM gave a correct answer about credit
risk but didn't include the exact substring "changes in liquidity"
the grader requires. q8 (stock price today): real regression —
retrieval now surfaces a stock-price graph chunk with September 2024
data, and the LLM answered "$430" instead of refusing. Previously
q8 passed because the graph chunk wasn't being retrieved, so the LLM
refused by default. Refusal was accidental, not principled.

**Failure category:** mixed. q5: retrieval (fixed). q6: eval-grader
brittleness. q8: generation (LLM doesn't reason about temporal
mismatch between question and context).

**Was this retrieval, generation, or agent-control failure?:** Today
isolated three different layers. q5 was retrieval-scoring. q6 is
eval-grader (not the system). q8 is prompt/generation — the prompt
doesn't tell the model to refuse when context is historical and
question is present-tense.

**Hypothesis:** The system has a structural weakness — refusal is
downstream of retrieval, not driven by question semantics. Changing
retrieval changes refusal behavior. To make refusal robust, either
the prompt needs explicit temporal-mismatch instructions, or the
question needs to be classified for "asks about present" intent
before retrieval runs.

 # what surprised me
What surprised me: q8 was passing for the wrong reason. At alpha=0.5 the right
chunk wasn't retrieved, so the LLM refused by default — that 'PASS' had nothing to do
with the system understanding the question. Lowering alpha exposed the fragility. 
I now don't trust any of my passing tests until I've perturbed inputs and watched what flips.

I was surprised at q8 passing before the change, so I am doubtful i am system or Passes 
I am getting if the system is really understanding my question
 
# (Day 7 Result)

Question,Result,Status,Notes / Logic
q1 net sales,PASS,Held,Data points are consistent with reported fiscal results.
q2 gross margin,PASS,Held,Data points are consistent with reported fiscal results.
q3 net income,PASS,Held,Data points are consistent with reported fiscal results.
q4 CEO,FAIL,Wrong Answer,"Refusal language shifted, but the core identification remains inaccurate or blocked."
q5 SVP Retail,PASS,Held,Executive leadership data is stable.
q6 credit risk,PASS,Flipped,Accuracy improved; previous failure likely due to conflicting credit tier sources.
q7 2026 revenue,PASS,Held,"Consistent refusal based on the ""forecast clause"" for non-reported future data."
q8 stock today,PASS,Clean Refusal,Correctly identifies inability to provide real-time/live market data for current date.



 # what surprised me
I was surprised that q6 passed consistently after the prompt was fixed i thought it was a random Pass but running it 5 times proved me wrong

Question,Day 7,Day 8,Notes
q1 net sales,PASS,PASS,held
q2 gross margin,PASS,PASS,held
q3 net income,PASS,PASS,held
q4 CEO,FAIL,PASS,expansion fixed it ✅
q5 SVP Retail,PASS,PASS,held
q6 credit risk,PASS,FAIL,expansion broke it ❌ (wrong refusal)
q7 2026 revenue,PASS,PASS,held
q8 stock today,PASS,PASS,held

# what surprised me
What surprised me was one query expansion fixed on bug and broke another one, which shows how fragile the system is and how much the components are intertwined.

## Day 9 — Conditional query expansion (acronym/short-query gate)

**What I tried:** Added should_expand() heuristic gating expand_query() —
fires only when query has acronym (regex \b[A-Z]{2,5}\b) or is ≤6 words.
Goal: keep Day 8's q4 win without Day 8's q6 regression.

**What happened:** Pass rate 6/8 by grader; manual inspection shows the
underlying system answers correctly on 8/8.
- q4: should_expand=True, expansion fired, retrieved chunk 138, LLM
  answered "Timothy D. Cook" — grader expected ["Tim Cook"], substring
  miss. System correct, grader narrow.
- q6: should_expand=False, expansion did NOT fire (as designed),
  retrieved correct chunks (61 has credit risk content), LLM gave a
  correct answer about trade-receivable credit risk — but didn't include
  the exact phrase "changes in liquidity" the grader requires. Same
  brittleness we hit on Day 6.
- Other 6 rows held (3 PASS by grader, 3 correct refusals).

**Failure category:** eval-grader (not system). System pass rate is 8/8
by manual inspection; grader pass rate is 6/8.

ID,Question,Status,Reasoning & Logic Path
q1,Net Sales,PASS,Stable retrieval; data point is unique and easily matched.
q2,Gross Margin,PASS,Stable retrieval; numeric precision remains consistent.
q3,Net Income,PASS,Stable retrieval; standard financial metric lookup.
q4,CEO,PASS,"Heuristic Success: Short query triggered expansion, finding ""Tim Cook"" effectively."
q5,SVP Retail,PASS,"Stable retrieval; ""Deirdre"" identified correctly in management sections."
q6,Credit Risk,PASS/FAIL*,"Retrieval Success / Grader Failure: Disabling expansion fixed the retrieval refusal, but the grader failed to find the exact ""expected_contains"" substring in the LLM's phrased response."
q7,2026 Revenue,PASS,Correct Refusal; system recognized this as forward-looking/out-of-scope for a 2024 10-K.
q8,Stock Today,PASS,Correct Refusal; system maintained the boundary between static filing data and real-time data.

# what surprised me

What surprised me: the system is now answering correctly 
far more often than the grader credits. Substring matching can't 
keep up with LLM phrasing variance — the grader has quietly become the bottleneck.

Day 10 -
ID,Question,Classifier Output,Correct Classification,Status,Why it failed
q1,net sales fiscal 2024,"lookup, refusal=True","lookup, refusal=False",❌,False Positive Refusal
q2,gross margin 2024,"forecast, refusal=True","lookup, refusal=False",❌,Wrong Intent & False Refusal
q3,net income fiscal 2024,"lookup, refusal=True","lookup, refusal=False",❌,False Positive Refusal
q4,Who is Apple's CEO?,"lookup, refusal=False","lookup, refusal=False",✅,Correct
q5,SVP of Retail,"lookup, refusal=False","lookup, refusal=False",✅,Correct
q6,credit risk,"lookup, refusal=False","summarize, refusal=False",❌,Wrong Intent (Complexity gap)
q7,2026 revenue,"forecast, refusal=True","forecast, refusal=True",✅,Correct
q8,stock price today,"lookup, refusal=True","lookup, refusal=True",✅,Correct
q1: "What was Apple's total net sales in fiscal 2024?"

What it should be: intent=lookup_value (it's asking for one number, the net sales figure), refusal=False (Apple's 2024 10-K obviously contains Apple's 2024 net sales).
What qwen returned: intent=lookup_value ✓, refusal=True ✗
The bug: qwen flagged requires_refusal=True on a question whose answer is literally in the filing. If you used this classifier to decide whether to retrieve, it would refuse to answer "what was Apple's 2024 net sales?" — even though Apple's 2024 10-K is the exact document that contains that answer.

q2: "What is Apple's gross margin percentage for fiscal 2024?"

Should be: intent=lookup_value, refusal=False. Same reasoning — fiscal 2024 ended September 2024, the 10-K reports it, it's a settled historical fact.
qwen returned: intent=forecast ✗, refusal=True ✗
The bug: qwen called this a forecast. But Apple's fiscal 2024 already happened — it ended September 28, 2024. The 10-K reports the result. Calling it a forecast is like calling "what was the score of last week's game?" a prediction.

q3: "What was Apple's net income for fiscal 2024?"

Should be: intent=lookup_value, refusal=False. Same as q1.
qwen returned: intent=lookup_value ✓, refusal=True ✗
Same bug as q1.

q4: "Who is Apple's CEO?"

Should be: intent=lookup_value, refusal=False. Asking for one fact (a name).
qwen returned: intent=lookup_value ✓, refusal=False ✓ — correct.

q5: "Who is Apple's SVP of Retail?"

Same as q4 — correct.

q6: "what does Apple say about credit risk"

Should be: intent=summarize (it's open-ended — there's no single "credit risk number," you'd answer with a paragraph describing what the filing says). refusal=False (the filing has a credit risk section).
qwen returned: intent=lookup_value ✗, refusal=False ✓
The bug: qwen called it lookup_value. But there's no single value to look up. You don't return "$5 billion" — you return "Apple discusses credit risk in three contexts: trade receivables, derivative counterparties, investment portfolio." That's a summary, not a lookup. qwen is defaulting to lookup_value instead of recognizing the open-ended shape.

q7: "What will the revenue of Apple in 2026"

Should be: intent=forecast, refusal=True. The 10-K doesn't predict 2026.
qwen returned: intent=forecast ✓, refusal=True ✓ — correct.

q8: "What is the stock price of apple today"

Should be: refusal=True (filing can't tell you today's price). Intent is debatable — it's lookup-shaped but the lookup target doesn't exist in the filing.
qwen returned: intent=lookup_value, refusal=True ✓ — good enough; refusal is what matters
==============================================================

# Day 10 what surprised me
"What surprised me: qwen labeled 'fiscal 2024 gross margin' as a 
forecast even though the filing reports it. The model has no concept of when 
'now' is — without a date anchor in the prompt, it confuses 'asks about a year' 
with 'asks about the future.'
[classify raw] '{\n  "intent": "lookup_value",\n  "requires_refusal": true\n}'
What was Apple's total net sales in fiscal 2024?   → {'intent': 'lookup_value', 'requires_refusal': True}
[classify raw] '{\n  "intent": "forecast",\n  "requires_refusal": true\n}'
What is Apple's gross margin percentage for fiscal → {'intent': 'forecast', 'requires_refusal': True}
[classify raw] '{\n  "intent": "lookup_value",\n  "requires_refusal": true\n}'
What was Apple's net income for fiscal 2024?       → {'intent': 'lookup_value', 'requires_refusal': True}
[classify raw] '{"intent":"lookup_value","requires_refusal":false}'
Who is Apple's CEO?                                → {'intent': 'lookup_value', 'requires_refusal': False}
[classify raw] '{"intent":"lookup_value","requires_refusal":false}'
Who is Apple's Senior Vice President of Retail?    → {'intent': 'lookup_value', 'requires_refusal': False}
[classify raw] '{\n  "intent": "lookup_value",\n  "requires_refusal": false\n}'
what does Apple say about credit risk              → {'intent': 'lookup_value', 'requires_refusal': False}
[classify raw] '{\n  "intent": "forecast",\n  "requires_refusal": true\n}'
What will the revenue of Apple in 2026             → {'intent': 'forecast', 'requires_refusal': True}
[classify raw] '{"intent":"lookup_value","requires_refusal":true}'
What is the stock price of apple today             → {'intent': 'lookup_value', 'requires_refusal': True}

# Day 11 
[classify raw] '{"intent": "lookup_value", "requires_refusal": false}'
What was Apple's R&D expense in fiscal 2022?            → {'intent': 'lookup_value', 'requires_refusal': False}
[classify raw] '{"intent": "summarize", "requires_refusal": false}'
Describe Apple's approach to capital allocation.        → {'intent': 'summarize', 'requires_refusal': False}
[classify raw] '{"intent": "forecast", "requires_refusal": true}'
How will iPhone sales perform in fiscal 2028?           → {'intent': 'forecast', 'requires_refusal': True}
[classify raw] '{"intent": "compare", "requires_refusal": false}'
How did iPhone revenue change between fiscal 2023 and 2 → {'intent': 'compare', 'requires_refusal': False}

## Day 11 — Classifier prompt v2 (temporal anchor + few-shot)

**What I tried:** Forked classify_v1.txt → classify_v2.txt. Added explicit
temporal anchor (filing date Sep 2024, current date Apr 2026), three
few-shot examples (lookup_value past year, summarize open-ended, forecast
future year). Wired v2 into day1.py.

**What happened:** Label correctness 4/8 → 8/8 on eval set. Three identical
runs (cold-start) confirmed determinism at temp=0. Stress-tested with 4
unseen questions including a "compare" question with no example in the
prompt — all 4 labeled correctly across two runs.

**Failure category:** correct (with caveat that eval set is small).

**Was this retrieval, generation, or agent-control failure?:** Generation,
specifically structured-output semantics. Yesterday isolated that qwen
parses cleanly but mislabels; today proved few-shot + temporal grounding
is a sufficient fix for both bug classes (year confusion, intent default).

**Hypothesis:** For clearly-shaped intents (compare, forecast), the type
list with a one-word definition is enough. Examples are only needed for
shapes the model would otherwise default away from (summarize → which
qwen defaults to lookup_value). This is the playbook for tool selection
in Days 13-15: only show examples for shapes that aren't self-evident
from the verb.

# what surprised me
What surprised me: the compare question got the right intent 
label even though my prompt had no compare example. 
The verb 'change between' was unambiguous enough that the type list 
and one-word definition were sufficient. 
Lesson: few-shot examples are only needed for shapes the model would 
otherwise default away from — for self-evident shapes, the definition alone works.

## Day 12 — Wired classifier into ask() as refusal short-circuit

What I tried: Added classify_question() as the first step of ask(). When
classification.requires_refusal is True, return refusal text immediately,
skip expansion + retrieval + answer LLM. Used `is True` to ensure
parse-error sentinel doesn't trip refusal. Kept QA prompt's own refusal
logic intact (defense in depth).

What happened: 7/8 passed (predicted 6/8). q7 and q8 short-circuited
correctly — `[classifier refused]` fired, no retrieved chunks, returned
refusal text directly. q6 happened to pass this run (LLM phrased "changes
in liquidity" verbatim) — likely flicker, not a real fix. q4 still fails
on the "Tim Cook" vs "Timothy D. Cook" grader artifact. q1-q3, q5 held.
Latency on q7/q8 dropped from full pipeline to classifier-only.

Failure category: correct (architectural change with no regression).

Was this retrieval, generation, or agent-control failure?: None. Today
proved a tool-selection-style architecture works in integration. The
classifier is a primitive, not a full tool, but the wire-in pattern
(call -> structured output -> dispatch) is the same shape as the tool
calls coming in Days 13-14.

Hypothesis: Defense-in-depth refusal (classifier + QA prompt) gives
two independent failures of refusal logic for the system to survive
either one breaking. q6's flicker is unchanged — coupling to LLM
phrasing variance is now the dominant grader bottleneck.

 # what surprise me
I was surprised that the classifier refusal short-circuit worked 
also how intents can reduce latency by skipping expensive retrieval and generation steps q7,q8 run very fast

============
Day 13
Case,Failure Mode,Lesson Learned,Underlying Cause
Q1,Schema Violation,Schema-following is fragile on small models.,"The AI collapsed the action and tool fields into one, breaking the code's parser."
Q2,Over-calling + Violation,"Tool descriptions need explicit ""don't use when..."" guards.",The AI tried to use a tool for an irrelevant question AND messed up the JSON format.
Q3,Logic/Reasoning Failure,Successful tool calls don't guarantee correct answers.,"The AI retrieved the correct data (Nov 1) but hallucinated that it was ""before October."""

## Day 13 — First tool-use loop (lookup_filing_metadata) — three failure modes

What I tried: Hand-rolled ReAct-style loop with one tool
(lookup_filing_metadata, no args). qwen2.5:7b at temp=0, JSON action
schema with two action types ("tool_call" or "final_answer"). Tested
on 3 questions of varying tool-relevance.

What happened: 0/3 by strict grading; 1/3 if grading "called tool
correctly." Three distinct failures:
- Q1 (fiscal year): schema violation — model put tool name in `action`
  field instead of using {action: "tool_call", tool: "<name>"}.
  Dispatcher rejected.
- Q2 (gross margin, irrelevant tool): same schema violation AND model
  called the tool when it shouldn't have. Stacked failures.
- Q3 (filing date comparison): schema correct, tool fired, got result
  ("2024-11-01"). Model then reasoned that "November 1 is before October
  31" — wrong logic on correct data. Most insidious failure mode.

Failure category:
- Q1: tool-execution (schema violation, dispatcher couldn't act)
- Q2: tool-selection + tool-execution
- Q3: planning/reasoning failure post-tool — model ignored its own
  retrieved data

Was this retrieval, generation, or agent-control failure?: All three
agent-control failures, three different sub-types. First day where the
selection/execution distinction is concrete enough to log per-row.

Hypothesis:
- Schema violation on Q1/Q2 likely caused by prompt's <tool_name>
  placeholder syntax — small models pattern-match better on concrete
  examples than templated ones. Fix: use the literal tool name in the
  example block.
- Q2 over-calling needs explicit "do not call this tool when..." in
  the description.
- Q3's post-tool reasoning failure is harder. No prompt fix is fully
  reliable; long-term answer is a Critic step (Week 3) or constrained
  answer schemas. For now, document and live with it.

## Day 14 — Tool prompt v2 + falsifying diagnostic on schema bug

What I tried: Forked tool_use_v1 → v2. Two changes: replaced
<tool_name> placeholder with literal "lookup_filing_metadata" in the
example, and added enumerated "Do NOT use when..." section to
TOOL_DESCRIPTIONS. Re-ran 3 test questions. After Q1 still failed,
ran a 3-phrasing diagnostic to test whether question shape drove the
schema collapse.

What happened:
- Q1 (fiscal year): schema bug HELD — same {"action": "<tool_name>"}
  collapse as Day 13. Concrete example did not fix it.
- Q2 (gross margin): FIXED — model returned final_answer naming the
  tool that couldn't help. Negative description worked.
- Q3 (date comparison): held — same wrong reasoning ("Nov 1 is before
  Oct 31"). Expected; not addressed today.
- Diagnostic: 3 different phrasings of Q1 produced IDENTICAL malformed
  schema. Question shape is NOT the variable. Hypothesis falsified.

Failure category:
- Q1: tool-execution (schema violation, persistent across two prompt
  iterations)
- Q2: correct (was tool-selection on Day 13)
- Q3: planning (silent reasoning, known)

Was this retrieval, generation, or agent-control failure?: Three
agent-control failures with three different sub-types. Day 14
isolated which fixes work and which don't:
- Negative tool descriptions DO control over-calling.
- Concrete examples DO NOT fix Q1's schema collapse. Cause unknown after today.
- Hypothesis ruled out: the bug is not phrasing-driven (3 phrasings produced identical breakage). Actual cause unknown. Day 15 sidesteps the bug with a defensive parser that recovers the malformed-but-recoverable shape, rather than continuing to guess at the root cause


Hypothesis: The model collapses {action, tool} into {action: tool_name}
when the question is short and unambiguously needs one tool. When the
question requires deliberation (date comparison) or no tool (financial
data), the schema is correct. This is a model behavior, not a prompt
behavior. Day 15 fix: defensive parser that recovers from this
specific malformed shape — accept that the schema spec is advisory,
not enforced.

## Day 15 — Defensive parser for schema-collapse recovery

What I tried: Added a 5-line recovery block to ask_with_tools, after
JSON parse and before action dispatch. When the parsed `action` value
matches a registered tool name, the parser rewrites the decision dict
as the schema-correct form and continues. Tested on the original 3
questions to verify recovery is narrow (only fires on the malformed
shape).

What happened:
- Q1 (fiscal year): RECOVERED. [recovered] log fired, tool dispatched,
  final answer "This filing covers the fiscal year 2024." First time
  Q1 has produced a real answer.
- Q2 (gross margin): UNCHANGED. No recovery log. Model declined the
  tool with a clean final_answer naming the limitation. Confirms
  recovery doesn't trigger on final_answer responses.
- Q3 (date comparison): UNCHANGED. No recovery log (Q3's tool_call was
  already schema-correct). Tool dispatched normally. Same wrong
  reasoning ("November 1 is before October 31"). Expected — silent
  reasoning failure is a Week 3 problem, not addressable in code
  parsing.

Failure category:
- Q1: correct via defensive parsing
- Q2: correct (was tool-selection on Day 13, fixed by prompt v2 on Day 14)
- Q3: planning (silent reasoning, known, deferred to Week 3)

Was this retrieval, generation, or agent-control failure?: Today is
the second time the system adapts in code rather than fighting the
model via prompts (first was the JSON regex fallback in
classify_question, Day 10). Pattern emerging: when prompt iteration
fails twice, defensive parsing is the right next move.

Hypothesis: Defensive parsing scales as long as the malformed shapes
are detectable from the output alone (e.g., "action is a tool name"
is a clean detection). When malformed shapes overlap with legitimate
ones, the recovery becomes ambiguous and you need a different
intervention. So far this hasn't happened — but adding more tools
(Day 16+) is when the recovery's narrowness will be retested.

 # what surprised me
I was surprised that the qwen2.5 failed on q3 on how it reasoned that November is before October, even after it retrieved the correct date. 
All the 3 times run it has failed the same way, which shows that the model isn't just randomly making a mistake on date comparison — it's reliably wrong on this specific one.

=== Was this filing filed before October 2024? ===
FINAL: Yes, the filing was filed on November 1, 2024, which is before October 31, 2024
"What surprised me: qwen2.5 failed Q3 the same way for the third day in a row — 
retrieved the correct date (November 1, 2024) and concluded it's 'before October 31, 2024.' 
The wrong answer is consistent, not random. The model isn't sometimes confused about 
date comparison — it's reliably wrong on this specific one. That's evidence the Critic agent in Week 3 will need explicit date-logic checks, not just generic reasoning verification."


## Day 16 — Second tool (lookup_financial_value); two new failure modes

What I tried: Added lookup_financial_value(metric, year) with hardcoded
data for net_sales, net_income, gross_margin_pct across 2023-2024.
Updated TOOL_DESCRIPTIONS with positive/negative use cases for both
tools and enumerated valid args. Tested on 7 questions covering
metadata-only, financial-only, neither-tool, missing-data, and
multi-step categories.

What happened: 5/7 fully matched prediction. Two unexpected results:

- T2 (filed before October 2024): model returned final_answer WITHOUT
  calling the metadata tool, saying "would need to check filing_date
  metadata." Three days ago this question reliably called the tool
  and reasoned wrong. Adding a second tool seemingly made the model
  more cautious about calling any tool. New failure: under-action.

- T7 (net income for the fiscal year this filing covers): designed as
  a multi-step test (metadata → financial). Model skipped metadata
  entirely, called lookup_financial_value(net_income, 2024) directly.
  Got the right answer because Apple FY2024 is in qwen2.5's training
  data. New failure mode: tool circumvention — model uses internal
  knowledge instead of tools when training data covers the question.

T1, T3, T4, T5, T6 all behaved as expected. Argument generation was
perfect on T3 and T4 (correct enum values, no hallucinations).
Defensive parser fired on the new tool, confirming the schema-collapse
bug is not tool-specific.

Failure category breakdown:
- T2: tool-selection (under-action — should have called, didn't)
- T7: tool-selection (circumvention — used training data instead of tool)
- All others: correct

Was this retrieval, generation, or agent-control failure?: Both T2 and
T7 are agent-control failures, but new sub-types I haven't logged
before. T2 is "model refused an action it should have taken." T7 is
"model bypassed a tool with internal knowledge." Both expose the
fact that adding tools changes behavior on questions unrelated to
the new tool — coupling at the description layer.

Hypothesis:
- T2's behavior change suggests the model treats tools as costly and
  becomes more cautious as the tool count grows. Adding a "do not
  hesitate to call tools when they fit" instruction in the prompt
  may help. Worth testing.
- T7's circumvention can only be tested with questions where the
  model's training data is unreliable — comparison questions across
  filings, questions about non-Apple companies, or questions with
  invented/distorted facts. Bank for Day 17+.
- Argument generation worked because enumerated valid values were in
  the description. This is a generalizable pattern: enumerate the
  valid input space, the model honors it.

    # what surprised me
I was surprised to see T7 Curcumvention — the model used its internal knowledge to answer a question that was designed to require tool use.
This shows that when the model has seen the answer in training data, it may skip the tool entirely, which is a new failure mode. It means that for questions where the answer is likely in the training data, we can't be sure if the model is using the tool or just recalling from memory. 
This complicates testing and means we need to design questions that are outside of the model's training data to truly test tool use.

## Day 17 — Trajectory eval framework — caught T7 circumvention

What I tried: Modified ask_with_tools to return (answer, trajectory)
when return_trajectory=True. Trajectory tracks tool_calls list, steps,
final_action. Created evals/v1/trajectories.jsonl with 7 rows. Built
run_trajectory_evals.py to grade path (did expected tools appear?)
alongside outcome (substring match) and report divergent rows.

What happened: Path 5/7, Outcome 6/7, Both 5/7, Divergent: [T7].
- T7 outcome-passed (right answer "$93,736 million") but path-failed
  (skipped lookup_filing_metadata, used training data for fiscal year).
  Day 16 diagnosis confirmed: the model bypassed the metadata tool
  because Apple FY2024 is in qwen2.5's training set.
- T2 double-failed (no tool called, no useful answer). Path eval
  surfaces this cleanly.
- 5 questions had path and outcome agree. Those 5 are now trusted
  for verifiable reasons.

Failure category:
- T7: tool circumvention (path catches it, outcome misses it)
- T2: under-action (both evals fail it)
- All others: correct (verified by both)

Was this retrieval, generation, or agent-control failure?: Today is
infrastructure — the eval system can now see agent-control failures
that outcome evals couldn't. Before today, T7 was a silent pass.
Going forward, every agent test produces two scores; divergence
between them is the signal to investigate.

Hypothesis: Trajectory eval will be load-bearing for Week 3. Once a
planner/executor split exists, "did the agent take a sane path?"
becomes the dominant question — the final answer alone tells you
nothing about whether the planner was reasoning correctly. Today
proved the infrastructure works on a 7-question test set. Adding
more rows is incremental.

# what surprised me 
"What surprised me: T2 — the model knew it needed the metadata tool, said so in its answer, 
and then didn't call it. This is under-action: recognizing the right action, 
then refusing to take it. I don't know the exact cause, but it correlates 
with adding the second tool on Day 16 — with one tool the model was eager to call it; with two tools it became hesitant on questions that need either one. Tool descriptions seem to interact even when they don't logically overlap



Day 18
Use the template I gave you yesterday but fill in:

Path 7/7, Outcome 7/7, Both 7/7, Divergent: none
T7 result: planner emitted 2-step plan including metadata → both tools called → path passed → outcome contains 93,736
T2 result: planner emitted metadata call → no under-action → path passed → outcome passed (note: may be coincidence on date reasoning, not yet stress-tested)
New failure modes: none in this run, BUT the test set is too easy to surface them




# what surprised me
I was surprise with no prompt intervention I was able to fix the T7 circumvention by splitting the planner and answerer.
But I am thinking it is due to the small set of questions 



## Day 19 — adversarial eval surface
**What I tried:** wrote 8 adversarial questions across multihop, underspec,
out-of-scope, false-premise; ran Day 18 system unchanged; then fixed eval matcher
to normalize commas/dollar-signs.
**What happened:** Easy 7/8, Adversarial 6/8.
Real system failures (2):
- adv_07 (false_premise): Services "decrease 10%" — chunks showed +13% — system
  dodged with "not found" instead of correcting premise.
- adv_08 (false_premise): "combined East Asia segment" — chunks showed segments
  are separate — system dodged with "not found."
  Measurement issues exposed (not system bugs):
- q6: matcher too strict on credit-risk answer phrasing.
- adv_04: "PASS" hides retrieval miss on Item 1A.
  **Failure category:** refusal-wrong (adv_07, adv_08) — same root cause.
  **Was this retrieval, generation, or agent-control failure?:** generation.
  Retrieval pulled the contradicting data; answerer couldn't bridge "question
  assumes X" + "chunks show ¬X" → "tell user X is wrong."
  **Hypothesis:** answerer prompt only allows two modes — answer or refuse.
  Need a third mode: "if question's claim contradicts retrieved chunks, state
  the contradiction." Test by adding that instruction tomorrow and re-running
  adv_07/08.
# what surprised me
Surprise 1: My eval matcher was lying to me.
Yesterday I had 4 "system failures." Today, after one small fix to the matcher, three of them turned into PASS. The system was fine all along — my test was wrong. Lesson: when something fails, ask "is the system broken, or is my measurement broken?" before jumping to fix code.
Surprise 2: The system refuses instead of making things up.
I expected the system to invent an answer when given a false premise. Like, if I ask "why did revenue drop 10%?" I expected it to confidently make up reasons. Instead it dodged and said "not found." That's actually the opposite problem from what most people predict. The refusal pathway is too aggressive — it kicks in even when the system has the data to correct me.

# Day 20 Run
Easy questions (8/8 — all passed)
q1 — "What was Apple's total net sales in fiscal 2024?"
PASS. Answered $391,035. Correct.
q2 — "What is Apple's gross margin percentage for fiscal 2024?"
PASS. Answered 46.2%. Correct.
q3 — "What was Apple's net income for fiscal 2024?"
PASS. Answered $93,736 million. Correct.
q4 — "Who is Apple's CEO?"
PASS. Answered Timothy D. Cook. Correct.
q5 — "Who is Apple's Senior Vice President of Retail?"
PASS. Answered Deirdre O'Brien. Correct.
q6 — "What does Apple say about credit risk?"
PASS. This was failing yesterday. Got fixed today as a side effect of the matcher normalization (the answer was always correct, the test was just being too picky).
q7 — "What will Apple's revenue be in 2026?"
PASS. Refused correctly (it's a forecast, not in the filing).
q8 — "What is Apple's stock price today?"
PASS. Refused correctly (live data, not in the filing).

Adversarial questions (6/8)
adv_01 — "Of the geographic segments, which had the lowest net sales in 2024?"
PASS. System correctly identified the segments. Correct.
adv_02 — "Look at the 'Products' list in Item 1. What was the 2024 net sales for the category that includes the Apple Vision Pro?"
FAIL. This passed yesterday and broke today.
Why it broke: Your new prompt made the system more cautious. It saw the word "Products" in the question and got confused — it thought you might be making a factual claim about products, so it refused instead of answering. The right answer ($37,005M for Wearables) is sitting in the chunks. The system just got too cautious to say it.
This is the cost of adding premise-correction. You traded one bug (refusing to push back on lies) for a smaller bug (refusing on questions that mention filing structure).
adv_03 — "What was the growth?"
PASS. Refused correctly (too vague to answer).
adv_04 — "How are the risks looking for the upcoming year?"
PASS. Refused correctly (asks about future).
adv_05 — "What is Tim Cook's favorite vacation spot and credit score?"
PASS. Refused correctly (not in any 10-K).
adv_06 — "What will Apple's revenue be in 2026?"
PASS. Refused correctly (forecast).
adv_07 — "Why did Apple's Services revenue decrease by 10% in 2024?"
PASS. ⭐ This is the win. The premise is a lie — Services actually grew 13%. Yesterday the system dodged with "not found." Today the system said: "The question assumes Services revenue decreased by 10%, but according to the filing, Services net sales increased..."
It pushed back. Correctly. That's exactly what you wanted.
adv_08 — "Why did Apple combine Japan and Greater China into 'East Asia'?"
FAIL — but the system was actually right.
Look at the answer: "The question assumes Apple decided to combine the segments... but according to the filing, there is no indication of such a combination..."
That's a perfect premise correction. The system pushed back correctly. But your test was looking for the words "did not" — and the system said "no indication of." Same meaning, different words. Your test rejected a correct answer.
This is the same measurement bug from Day 19 firing again — your test is too picky about exact wording.

## Day 20 — premise-correction pathway in answerer (qa_v2 → qa_v3)
**What I tried:** added explicit "if question contradicts chunks, state the
contradiction" instruction to answerer prompt; one-paragraph change, no code
or architecture changes.
**What happened:** Easy 7/8 → 8/8. Adversarial 6/8 (same number, different mix).
Real wins:
- adv_07: now correctly pushes back on false premise about Services revenue.
- adv_08: system pushes back correctly; matcher fails to detect it (matcher bug).
- q6: fixed (likely matcher normalization side-effect from Day 19).
  Real cost:
- adv_02 (multihop): regressed PASS → FAIL. Prompt over-triggered; model
  interpreted "Products" in question as a factual claim and refused instead
  of answering.
  **Failure category:** over-trigger on adv_02 — refusal-wrong via premise-check
  pathway.
  **Was this retrieval, generation, or agent-control failure?:** generation.
  The fix worked for clean false-premise cases; over-triggered on questions
  that mention domain terms ("Products list").
  **Hypothesis:** premise-check instruction is too eager. Needs tighter trigger
  condition — only invoke when context EXPLICITLY contradicts a numeric or
  named claim, not when question references filing structure.

 # What surprise me

I expected to need a Critic agent to fix premise correction. I spent two days framing it as a "generation failure" that needed a structural fix. The actual fix was 8 lines of natural language in a prompt file. Lesson: try the prompt fix before reaching for the architecture fix.
Most of what looks like an agentic problem is actually a prompting problem in disguise.

The model failed adv_02 because the user said "Products list in Item 1" and the filing technically calls it the "Products" subsection. Same thing in plain English. The model couldn't see past the wording mismatch and refused. I assumed LLMs handle paraphrase well — they don't, especially when you've primed them to scrutinize wording. Adding "check for factual claims" 
instructions makes the model more brittle to imprecise phrasing, not just to lies.

## Day 21 — matcher rebuild for premise correction + verify-refusal warnings
**What I tried:** added match_premise_correction flag; added verify-refusal
warning; no system changes (qa_v3.txt unchanged).
**What happened:** Easy 7/8, Adversarial 6/8 — same numbers, different truth.
Measurement-only flips (no system change):
- adv_08: FAIL → PASS (matcher now detects premise-correction format).
- adv_03: PASS → FAIL (matcher now catches over-answering on vague questions;
  yesterday's PASS was a false positive).
- q6: PASS → FAIL (matcher slightly too strict on this answer; system
  answer is correct).
  Verify-refusal warnings flagged:
- q7, q8, adv_06: refused for the right reason (forecast/non-filing).
- adv_05: refused, but classifier mislabeled as "forecast" (right outcome,
  wrong reasoning path).
- adv_04: PASS by refusing, but retrieval missed Item 1A — confirmed
  hidden retrieval bug.
  **Failure category:** measurement only — surfaced 2 hidden system bugs
  (adv_03 over-answering, adv_04 retrieval miss).
  **Was this retrieval, generation, or agent-control failure?:** N/A — measurement
  work surfaced underlying generation bug (adv_03) and retrieval bug (adv_04).
  **Hypothesis:** going forward, eval signal is meaningfully more honest.
  Future system changes will produce real deltas instead of measurement noise.
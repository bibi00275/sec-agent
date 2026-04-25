## Day 1 — Predictions (written before answers came in)

Q1 "Apple's total net sales in fiscal 2024":
- Will this be retrieved correctly? [yes/no/maybe + why] - No , Chunking may break heading paragraph mid way so it might relate to a sales reference what it sees first and return so i hihgly doubt if it will return right data
  - Will the LLM extract the right number? [yes/no/maybe + why] no , chunking may not be correct first reference in chcunks with sales information may be retrieved and it may not contain the right information
- My bet: [right / wrong / hedged]

Q2 "What does Apple say about supply chain risk?":
- (same three predictions) 
- No , chunking may break heading paragraph mid way so it might relate to a sales reference what it sees first and return so i hihgly doubt if it will return right data

Q3 "Who is Apple's CEO?":
- (same three predictions) - This should retrieve correctly - LLm already knows it so I think llm should retrieve 
- though the chances of getting it from data source 10K might fail, 
- if the retrieved chunk doesnt contain tim cooks name then retrieval is a failure as data is coming llm

## Day 1 — Baseline RAG against Apple FY2024 10-K

**What I tried:** Fixed 2000-char chunks (110 total), nomic-embed-text embeddings, cosine top-3 retrieval, llama3.1:8b for QA on 3 questions. Pickle hack for embeddings. Two plumbing bugs along the way (`.FORMAT` typo, `"msg"` literal instead of `prompt` variable) sent empty content to the LLM until fixed.

**What happened:**
- Q1 (revenue): retrieval correct (revenue table cleanly inside chunk 0), answer correct ($391,035M). Right answer, right reason.
- Q2 (supply chain): retrieval correct (3 chunks all about supply/regulatory risk). Generation contradictory — said "Not found" then summarized the content. Prompt-following failure.
- Q3 (CEO): retrieval failed — top-3 was signatures page (no Tim Cook), product descriptions, and a competition paragraph. Model correctly refused. Right behavior, but only because the prompt's safety rail caught it.

**Failure category:**
- Q1: correct
- Q2: refusal-wrong (refused while also answering — worst of both worlds)
- Q3: retrieval (rescued by refusal-right downstream)

**Was this retrieval, generation, or agent-control failure?:**
- Q1: neither — clean
- Q2: generation (prompt brittleness on refusal logic)
- Q3: retrieval (top-3 missed cover/signature page)

**Hypothesis:**
- Fixed-size chunking gets lucky when the answer is a self-contained table (Q1) and breaks when answers span structural elements like cover pages or section boundaries (Q3).
- The "Not found" instruction is too literal for the LLM — it triggers on missing exact phrasing rather than missing concept. Needs prompt rewrite.
- Top-3 may be too few; OR the embedding model isn't surfacing structural sections like "Executive Officers" because the chunk text is dominated by signature noise.

**Predictions vs reality (Day 1 calibration check):**
Predicted retrieval would fail on all 3 due to bad chunking. Reality: failed only on Q3. Q1 and Q2 succeeded by luck of alignment. Lesson: dirty chunking is an inconsistent failure, not a uniform one.


    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

soup = BeautifulSoup(html, 'lxml').get_text(" ", strip=True)
Total Chars:218587, Total Chunks: 110
Embeddings: (110, 768)

--- RETRIEVED CHUNKS ---
[chunk 0]: ,658 Europe 101,328 7 % 94,294 (1) % 95,118 Greater China 66,952 (8) % 72,559 (2) % 74,200 Japan 25,052 3 % 24,257 (7) % 25,977 Rest of Asia Pacific 30,658 4 % 29,615 1 % 29,375 Total net sales $ 391,035 2 % $ 383,285 (3) % $ 394,328 Americas Americas net sales increased during 2024 compared to 2023...

[chunk 1]:  172,269 Total net sales $ 391,035 $ 383,285 $ 394,328 2024 2023 Long-lived assets: U.S. $ 35,664 $ 33,276 China (1) 4,797 5,778 Other countries 5,219 4,661 Total long-lived assets $ 45,680 $ 43,715 (1) China includes Hong Kong and Taiwan. Apple Inc. | 2024 Form 10-K | 47 Report of Independent Regis...

[chunk 2]: the location of customers and sales through the Company’s retail stores located in those geographic locations. Operating income for each segment consists of net sales to third parties, related cost of sales, and operating expenses directly attributable to the segment. The information provided to the...


================================================================================
Q: What was Apple's total net sales in fiscal 2024?
A: $391,035.

--- RETRIEVED CHUNKS ---
[chunk 0]: quiring changes to the Company’s business or supply chain. New and changing laws and regulations can also create uncertainty about how such laws and regulations will be interpreted and applied. These risks and costs may increase as the Company’s products and services are introduced into specialized ...

[chunk 1]:  realized significant losses on its cash, cash equivalents and marketable securities, future fluctuations in their value could result in significant losses and could have a material adverse impact on the Company’s results of operations and financial condition. The Company is exposed to credit risk o...

[chunk 2]: ith little or no advance notice, which can create uncertainty, and the Company may not be able to effectively mitigate all adverse impacts from such measures. For example, tensions between governments, including the U.S. and China, have in the past led to tariffs and other restrictions affecting the...


================================================================================
Q: What does Apple say about supply chain risk?
A: Not found in provided context.

However, I can provide a summary of the relevant information:

Apple discusses various risks related to its business, including regulatory changes, credit risk, and natural disasters. Specifically, it mentions that:

* Changing regulations relating to export and import of products may affect its business.
* The company is exposed to credit risk on its trade accounts receivable and vendor non-trade receivables.
* Global supply chains can be highly concentrated and geopolitical tensions or conflict could result in significant disruptions.

But the specific term "supply chain risk" is not mentioned in the provided context.

--- RETRIEVED CHUNKS ---
[chunk 0]: I /s/ Chris Kondo Senior Director of Corporate Accounting (Principal Accounting Officer) November 1, 2024 CHRIS KONDO /s/ Wanda Austin Director November 1, 2024 WANDA AUSTIN /s/ Alex Gorsky Director November 1, 2024 ALEX GORSKY /s/ Andrea Jung Director November 1, 2024 ANDREA JUNG /s/ Arthur D. Levi...

[chunk 1]: ting the Company’s products and infringing on its intellectual property. Apple Inc. | 2024 Form 10-K | 2 The Company’s ability to compete successfully depends heavily on ensuring the continuing and timely introduction of innovative new products, services and technologies to the marketplace. The Comp...

[chunk 2]:  includes AirPods ® , AirPods Pro ® , AirPods Max ® and Beats ® products. Apple Vision Pro™ is the Company’s first spatial computer based on its visionOS™ operating system. Home includes Apple TV ® , the Company’s media streaming and gaming device based on its tvOS ® operating system, and HomePod ® ...


================================================================================
Q: Who is Apple's CEO?
A: Not found in provided context.

**What surprised me:** [fill this in honestly — one paragraph. What did you expect to see and not see?]
I expected all three questions to fail because of fixed size chunking but what surprised me was it could be lucky if the cut was at the right part 
Though the retrieval worked what surpised me was the prompt brittleness because it was forced to looked into the retrieved context but model could have known it but as prompt forced it to do hence it ignored and shown a no data found. 
I was surprised that multiple chunks related suply chain risk was retrieved not just the first chunk found
1. When you see "Not found in provided context" in your terminal, what does that tell you about the system? What does it not tell you?
When i saw that the it shows that the chunk retrieved doesnt have the information because prompt forced it do so though llm may have the information. 
2. For Q2: what was actually in the retrieved chunks? Did the model have enough information to answer the supply-chain question? If yes, why did it refuse?
One of the chunks was wrong , but 2 chunks had the information retrieval was correct but the generation was wrong prompt is brittle and overresufed on a good context.
3. For Q3: what was actually in the retrieved chunks? Did the model have enough information to answer the CEO question? If yes/no, why did it refuse?
The retrieve chunks didnt have teh answer and the prompt forced it to look into the retrieved chunks so it refused.
4. If you ran an automated test that checks "did the system refuse?" — would Q2 and Q3 look the same or different to that test? And is the system actually behaving the same way in both cases?
Question on net sale was correct the data it fetched from the chunks and the model generated correctly 
Question on the supply chain two of the chunks was correct but the model failed or refused to generate the answer which is a real bug.
Question on the CEO the reitreive chunk didnt have the data and the model refused it , prompt said to read from teh context there was nothing in the context , which is a not a bug but prompt is doing its job.
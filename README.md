README.md — Known Dirty Things, append:

Sub-chunker uses fixed max_chars cuts, slices through sentences and signature lines. Will mis-handle any dense-signal block in a long section.
Min-max normalization fabricates confidence — top score is always ~1.0 even when no chunk is relevant. Need an absolute relevance threshold for refusal logic later.
Chunker only knows back-matter headings present in AAPL 2024 10-K (SIGNATURES, EXHIBIT INDEX, POWER OF ATTORNEY). Other filings may use different conventions.
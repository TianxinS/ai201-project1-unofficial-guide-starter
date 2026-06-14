# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

Restaurant recommendations for Lynnwood, WA and nearby Puget Sound cities, built from Google Maps customer reviews. This knowledge is valuable because review platforms bury the most useful details — specific dish recommendations, price-per-person breakdowns, wait time complaints, and atmosphere notes — across hundreds of individual reviews per restaurant. Official restaurant websites don't capture this lived experience, and manually skimming hundreds of reviews to find a pattern (e.g., "is the wait time bad on weekends?") is impractical. A retrieval system can surface the specific review snippets that directly answer a user's question.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | El Antojo Lynnwood | Google Maps reviews (manually copied) | documents/antojo.txt |
| 2 | Gyro Grill | Google Maps reviews (manually copied) | documents/gyro.txt |
| 3 | JangAn Sullungtang | Google Maps reviews (manually copied) | documents/jangan.txt |
| 4 | Modoo Korean Restaurant | Google Maps reviews (manually copied) | documents/modoo.txt |
| 5 | Taqueria Costa Sur | Google Maps reviews (manually copied) | documents/taqueria.txt |
| 6 | Wingstop | Google Maps reviews (manually copied) | documents/wingstop.txt |
| 7 | The Yemeni House | Google Maps reviews (manually copied) | documents/yemeni.txt |
| 8 | Peace of Mind | Google Maps reviews (manually copied) | documents/peaceofmind.txt |
| 9 | Dick's Dine-in | Google Maps reviews (manually copied) | documents/dicks.txt |
| 10 | MARKET | Google Maps reviews (manually copied) | documents/market.txt |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** One chunk per individual review (no fixed character cap). Reviews range from ~100–500 characters, with long reviews split into sentence groups capped at 500 characters.

**Overlap:** None between separate reviews (each is independently retrievable). For long reviews that get split, a ~50-character overlap is carried into the next sub-chunk so no sentence is cut off mid-thought.

**Why these choices fit your documents:** Each Google Maps review is a natural semantic unit expressing one person's complete opinion. Splitting a single review into fixed-size character windows would fragment a sentence like "The wait was no wait at all" into a half-sentence that loses its meaning. Combining multiple reviews into one chunk would merge conflicting opinions and make distance scores less discriminating. Chunking one-review-per-chunk preserves each voice intact and makes retrieval more precise.

**Preprocessing:** The documents are plain text exports of Google Maps reviews. Each file begins with a 4-line header (restaurant name, rating, price range, cuisine), followed by individual reviews separated by blank lines. The header is parsed and prepended as metadata to every chunk; no HTML cleaning was needed since the source was plain text.

**Final chunk count:** Run `python test_pipeline.py` to see the current count printed to the console.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via sentence-transformers. It runs locally with no API key, is fast on CPU, and performs well on short opinion-based text. The model is initialized through ChromaDB's `SentenceTransformerEmbeddingFunction`, which handles embedding automatically at both ingestion and query time.

**Production tradeoff reflection:** If cost weren't a constraint, I'd consider `text-embedding-3-large` (OpenAI) or `bge-large-en` for better accuracy on nuanced opinion language — distinguishing "the wait wasn't bad" from "the wait was terrible" requires more semantic precision than a small model offers. Multilingual support would also matter: ethnic-cuisine restaurants in the dataset (Korean, Yemeni, Mexican) occasionally receive non-English reviews, and `all-MiniLM-L6-v2` handles those weakly compared to `paraphrase-multilingual-MiniLM-L12-v2`. The tradeoff is higher latency and embedding cost per document versus better recall on edge cases.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:** The system prompt explicitly instructs the model: *"Answer questions using ONLY the customer reviews provided in the context. Do not draw on your general knowledge about restaurants. If the retrieved reviews do not contain enough information to answer the question, say clearly: 'I don't have enough review information to answer that.' Do not guess or invent details."* The retrieved chunks are passed as a labeled context block before the user's question, so the model sees retrieved text first and is told the question second.

**How source attribution is surfaced in the response:** Source filenames are appended programmatically by `generator.py` after every LLM response — regardless of whether the LLM included inline citations. Every response ends with a `📍 Retrieved from:` line listing the exact source `.txt` files the retrieved chunks came from. This is guaranteed at the code level, not left to the model to decide.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What's the best Korean resaurant| JangAn| Modoo | ok| Inaccurate|
| 2 | What do reviewers say about the wait time at El Antojo| No wait| No wait| Good| Accurate|
| 3 | Which restaurant has the best broth of soup| JangAn| JangAn| Good| Accurate|
| 4 | What's a good price-per-person range for Mexican food| $10-20| $10-20| Good| Accurate|
| 5 | What's the most negatively reviewed restraurant| WingStop| WingStop| Good| Accurate|
| 6 | Is JangAn kid-friendly?| Don't know| I don't have enough review information to answer that| Good| Accurate|

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**
What's the best Korean resaurant

**What the system returned:**
Modoo

**Root cause (tied to a specific pipeline stage):**
All Modoo comments I pasted are positive, so the model saw biased data. The model didn't compare overall ratings.

**What you would change to fix it:**
Adding more comments for it and I should refine the prompt as well.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** The Chunking Strategy section in planning.md made the implementation decision clear before writing any code — chunk per review, not per fixed character window. This prevented the classic mistake of splitting a short review mid-sentence. Having the reasoning written down ("a review is a natural semantic unit") made it easy to verify the implemented chunker matched the intention and to explain the choice to collaborators.

**One way your implementation diverged from the spec, and why:** The spec described chunking by fixed character count with overlap as a fallback for very long reviews. In practice, the review files are plain text with no HTML or boilerplate to strip, so no cleaning step was needed — the pipeline goes directly from raw text to chunking. The "cleaning" stage from the spec diagram was effectively a no-op and was absorbed into the header parsing step rather than being a separate pass.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:* My Chunking Strategy section from planning.md, two sample review documents (antojo.txt and jangan.txt), and the instruction to implement `chunk_document()` that treats each review as one chunk with a metadata header prepended.
- *What it produced:* A chunker that split on double blank lines (`\n\n`). This broke on reviews like the long Gus Fan review in jangan.txt, which has single blank lines between internal sections (the "Highlights:" list), causing one review to be split into multiple chunks incorrectly.
- *What I changed or overrode:* I directed the AI to switch from blank-line splitting to time-ago boundary detection — finding lines that match "X months ago" and using the line above each as the reviewer name. This correctly identifies review starts even when a review has internal blank lines.

**Instance 2**

- *What I gave the AI:* My grounding requirement from planning.md and the RulesBot generator.py as a reference, with the instruction to adapt it for restaurant reviews and add programmatic source attribution.
- *What it produced:* A generator that included a grounding system prompt and told the LLM to cite sources. The attribution relied entirely on the LLM mentioning restaurant names in its answer.
- *What I changed or overrode:* I added a programmatic source-appending step at the end of `generate_response()` that collects unique source filenames from the retrieved chunks and appends them as a `📍 Retrieved from:` line. This guarantees attribution is always present in the output, independent of what the LLM decides to include in its response text.

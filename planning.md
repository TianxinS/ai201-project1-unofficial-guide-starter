# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
My domain is a restaurant recommendation assistant, built from Google Maps-style restaurant reviews. The goal is to answer questions like "where can I get good Mexican food with no wait time?" or "which restaurants have great service but slow wait times?" by grounding answers in real customer reviews.

This knowledge is valuable because review platforms bury the most useful details — specific dish recommendations, price-per-person breakdowns, wait time complaints, atmosphere notes — across hundreds of individual reviews per restaurant. Official restaurant websites and menus don't capture this lived experience, and skimming through hundreds of reviews manually to find a pattern (e.g., "is the wait time usually bad on weekends?") is impractical. A retrieval system can surface the specific review snippets that answer a user's actual question.


---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

- Google Maps reviews for ~10–15 restaurants in Lynnwood, WA and nearby Puget Sound cities (Mexican, Korean, Vietnamese, American, Mediterranean, etc.), manually copied/scraped, each saved as a text file per restaurant
- Each review includes: restaurant name, overall rating, price range, cuisine type, reviewer name, time posted, review text, and structured ratings (Food/Service/Atmosphere/Wait time)
- Sources cover a range of cuisines and price points so retrieval can answer comparative queries ("which place has the best service for the price")


| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Google| Antojo| https://www.google.com/maps/place/El+Antojo+Lynnwood/@47.8148119,-122.372384,13z/data=!4m11!1m3!2m2!1sRestaurants!6e5!3m6!1s0x54901ab44d828389:0xac041b89b888d0a8!8m2!3d47.8116985!4d-122.3225213!15sCgtSZXN0YXVyYW50c1oNIgtyZXN0YXVyYW50c5IBEm1leGljYW5fcmVzdGF1cmFudJoBRENpOURRVWxSUVVOdlpFTm9kSGxqUmpsdlQycFNTbEV3VG10VlZFSm1Va2RXVFZwRlZrSmlXRTQxVm0xV1MxWnNSUkFC4AEA-gEFCIgBEEQ!16s%2Fg%2F1ptxc67z_?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 2 | Google| Gyro| https://www.google.com/maps/place/Gyro+Grill/@47.8148119,-122.372384,13z/data=!4m11!1m3!2m2!1sRestaurants!6e5!3m6!1s0x5490053652e920a7:0xc5b61771bc1acf0!8m2!3d47.8217009!4d-122.2961283!15sCgtSZXN0YXVyYW50c1oNIgtyZXN0YXVyYW50c5IBD2d5cm9fcmVzdGF1cmFudJoBJENoZERTVWhOTUc5blMwVkpRMEZuU1VSYU0zWXlhRFZSUlJBQuABAPoBBAgAEEg!16s%2Fg%2F11q3_pvdh9?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 3 | Google| JangAn| https://www.google.com/maps/place/장안설렁탕JangAn+Sullungtang/@47.821615,-122.3217616,17z/data=!3m1!4b1!4m6!3m5!1s0x549005e003fff08f:0x481eff0677269131!8m2!3d47.8216151!4d-122.3168907!16s%2Fg%2F11y2qb00r5?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 4 | Google| Modoo| https://www.google.com/maps/place/Modoo+Korean+Restaurant+모두+식당/@47.8303349,-122.3091713,17z/data=!3m1!4b1!4m6!3m5!1s0x549005893ae1ed23:0x4dfbdeedf48f8951!8m2!3d47.8303349!4d-122.3065964!16s%2Fg%2F11j3s5dvgy?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 5 | Google| Taqueria| https://www.google.com/maps/place/Taqueria+Costa+Sur+%7CLynnwood/@47.8148119,-122.372384,13z/data=!4m11!1m3!2m2!1sRestaurants!6e5!3m6!1s0x54901b080987fe19:0x81b8b019740dbc43!8m2!3d47.8102519!4d-122.3237034!15sCgtSZXN0YXVyYW50c1oNIgtyZXN0YXVyYW50c5IBEm1leGljYW5fcmVzdGF1cmFudJoBRENpOURRVWxSUVVOdlpFTm9kSGxqUmpsdlQyNVJkMDFVVGpaTk1uUkpZMFZ3U1ZZd2FEWmlWVTVhWVRCd2VGbHJSUkFC4AEA-gEECCQQRg!16s%2Fg%2F11h_x512y9?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 6 | Google| WingStop| https://www.google.com/maps/place/Wingstop/@47.8148119,-122.372384,13z/data=!4m13!1m3!2m2!1sRestaurants!6e5!3m8!1s0x5490052184e8de33:0xb566f00c99a5da98!8m2!3d47.8205596!4d-122.2880971!9m1!1b1!15sCgtSZXN0YXVyYW50c1oNIgtyZXN0YXVyYW50c5IBGGNoaWNrZW5fd2luZ3NfcmVzdGF1cmFudJoBRENpOURRVWxSUVVOdlpFTm9kSGxqUmpsdlQydzVZVXhVU21sV1JYZ3lUbFJHZWs5V2JHeFZiRVpWVDFab05WSXpZeEFC4AEA-gEECEUQQg!16s%2Fg%2F11l_0mvt4s?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 7 | Google| Yementi| https://www.google.com/maps/place/The+Yemeni+house+restaurant/@47.8148119,-122.372384,13z/data=!4m11!1m3!2m2!1sRestaurants!6e5!3m6!1s0x549005280ee2d66f:0x7b00bb1aca4ebf77!8m2!3d47.8218412!4d-122.3259853!15sCgtSZXN0YXVyYW50c1oNIgtyZXN0YXVyYW50c5IBE3llbWVuaXRlX3Jlc3RhdXJhbnSaAURDaTlEUVVsUlFVTnZaRU5vZEhsalJqbHZUMnBTU0ZGdGNHRlpWM2hUVXpBMVNsa3lSbTVQVkZwaFZtdG9UazlYWXhBQuABAPoBBQiUDxBD!16s%2Fg%2F11yv1pqg_s?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 8 | Google| MARKET| https://www.google.com/maps/place/MARKET+Seafood+Eatery/@47.8104238,-122.453388,13z/data=!4m12!1m2!2m1!1smarket!3m8!1s0x54901b3557978093:0xd3dcb0df56195599!8m2!3d47.8103537!4d-122.3771473!9m1!1b1!15sCgZtYXJrZXRaCCIGbWFya2V0kgESc2VhZm9vZF9yZXN0YXVyYW50mgEkQ2hkRFNVaE5NRzluUzBWSlEwRm5TVVF6TTNFemVXZG5SUkFC4AEA-gEFCPIBEEY!16s%2Fg%2F11f613z2mh?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 9 | Google| Peace of Mind| https://www.google.com/maps/place/Peace+of+Mind+Brewing/@47.8303349,-122.3091713,17z/data=!4m16!1m7!3m6!1s0x549005893ae1ed23:0x4dfbdeedf48f8951!2zTW9kb28gS29yZWFuIFJlc3RhdXJhbnQg66qo65GQIOyLneuLuQ!8m2!3d47.8303349!4d-122.3065964!16s%2Fg%2F11j3s5dvgy!3m7!1s0x54900513c1c3ffff:0xc817ddebce10fd30!8m2!3d47.8316121!4d-122.305372!9m1!1b1!16s%2Fg%2F11t13t7_sf?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|
| 10 | Google| Dick's Dine-in| https://www.google.com/maps/place/Dick's+Drive-In/@47.8127442,-122.3679412,13.33z/data=!4m16!1m7!3m6!1s0x549005893ae1ed23:0x4dfbdeedf48f8951!2zTW9kb28gS29yZWFuIFJlc3RhdXJhbnQg66qo65GQIOyLneuLuQ!8m2!3d47.8303349!4d-122.3065964!16s%2Fg%2F11j3s5dvgy!3m7!1s0x54901163628e5f57:0x6ab7c110ebacce6e!8m2!3d47.8011237!4d-122.331722!9m1!1b1!16s%2Fg%2F1tdqnc1n?entry=ttu&g_ep=EgoyMDI2MDYxMC4wIKXMDSoASAFQAw%3D%3D|

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

Reviews are short (typically 2–6 sentences), so I'll chunk **per individual review** rather than splitting by fixed character count — each review is treated as one chunk, with the restaurant name, cuisine, price range, and structured ratings (Food/Service/Atmosphere/Wait time) prepended as metadata/header text inside the chunk.


**Chunk size:**
roughly 100–400 characters depending on review length, no fixed cap — a review is a natural semantic unit and shouldn't be split mid-thought
**Overlap:**
none needed between reviews, since each review is independently retrievable and self-contained. For unusually long reviews (rare, but some exceed ~500 characters), I'll split by sentence groups with ~50-character overlap so a long review doesn't lose context if split
**Reasoning:**
If chunks were too small (e.g., splitting one review into multiple fragments by character count), a query like "is the chips and salsa free here?" might retrieve a fragment that mentions "salsa" without the sentence explaining it's complimentary, losing the answer. If chunks were too large (e.g., combining many reviews for one restaurant into a single chunk), retrieval would return a wall of mixed opinions and the LLM might conflate which reviewer said what, or distance scores would become less discriminating since one chunk tries to represent too many different sentiments at once.



---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**
I'll use `all-MiniLM-L6-v2` via sentence-transformers (same as the RulesBot starter) — it's fast, lightweight, and performs well on short opinion-based text like reviews.

**Top-k:**
5 chunks per query. Since each chunk is one review, retrieving 5 gives the LLM a handful of different reviewers' perspectives without overwhelming it or diluting relevance with mediocre matches. Too few (e.g., k=1) risks the LLM generalizing from a single outlier opinion. Too many (e.g., k=15) risks pulling in reviews about unrelated restaurants or topics, increasing the chance the LLM gets distracted or contradicts itself.


**Production tradeoff reflection:**
Semantic search works even without exact word overlap because the embedding model captures meaning — a query like "is it kid-friendly?" can match a review saying "great for families with young children" even though no words overlap, because both map to nearby points in embedding space.

If cost weren't a constraint, I'd consider a larger model like `text-embedding-3-large` (OpenAI) or `bge-large-en` for better accuracy on nuanced opinion language (e.g., distinguishing "the wait wasn't bad" from "the wait was terrible"), though at the cost of higher latency and embedding cost per document. Multilingual support would matter if reviews include non-English text (common in ethnic-cuisine restaurants), which `all-MiniLM-L6-v2` handles only weakly compared to multilingual models like `paraphrase-multilingual-MiniLM-L12-v2`.


---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What's the best Korean restaurant?| JangAn|
| 2 | What do reviewers say about the wait time at El Antojo? | Should mention "No wait" based on the example review provided.|
| 3 | Which Mexican restaurant has reviewers comparing it favorably to Alibertos or California Burrito?| El Antojo, with reviewers saying it surpasses those chains in meat/tortilla quality.|
| 4 | What's the most terrible resaurant?| Wingstop|
| 5 | What's a good price-per-person range for Mexican food according to reviews?|  Around $10–20|


---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

- **Inconsistent review formatting:** Reviews vary widely in length, structure, and how much detail reviewers include (some are one sentence, others are paragraphs with structured ratings) — chunking logic needs to handle both gracefully without breaking on missing fields like "Wait time."
- **Off-topic or generic retrieval:** Vague queries (e.g., "is this place good?") might retrieve generic positive reviews that don't actually answer specifics like price, wait time, or dish quality, since "good" doesn't carry much semantic signal.
- **Missing source attribution across mixed-cuisine queries:** If a user asks a comparative question across restaurants, retrieved chunks from different restaurants need clear metadata (restaurant name) attached, or the LLM might attribute one restaurant's review to another.
- **Sparse coverage for less-reviewed topics:** Some specific questions (e.g., "is there outdoor seating?") may simply not be covered by any review, and the system needs to clearly say "not found" rather than hallucinate an answer.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

- **Chunking implementation:** I'll give Claude my Chunking Strategy section plus 2–3 sample review documents, and ask it to implement a `load_and_chunk_reviews()` function that parses each review (with metadata header) into a chunk dict with `text`, `restaurant`, `cuisine`, and `ratings` fields.
- **Retriever (`retrieve()`):** I'll reuse the RulesBot `retrieve()` spec/implementation pattern, giving Claude my Retrieval Approach section (top-k=5, all-MiniLM-L6-v2) and asking it to adapt the function so the returned `"game"` field becomes `"restaurant"`.
- **Generator (`generate_response()`):** I'll give Claude my grounding system prompt from the RulesBot generator spec and ask it to adapt the wording for restaurant reviews (e.g., "cite which restaurant the review is about" instead of "which game"), ensuring it still refuses to answer beyond retrieved context.
- **Evaluation testing:** I'll give Claude my 5 evaluation questions and the actual system outputs, and ask it to help me assess whether each response correctly grounds itself in the retrieved reviews or hallucinates, and suggest fixes if retrieval misses the right chunk.

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**

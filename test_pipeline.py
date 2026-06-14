"""
Pipeline validation script — run this before committing to Milestone 4.

Covers M3 checkpoint (chunk inspection) and M4 checkpoint (retrieval testing).
Usage: python test_pipeline.py
"""
import random
from ingest import load_documents, chunk_document
from retriever import embed_and_store, retrieve, get_collection

# ---------------------------------------------------------------------------
# M3: Chunk inspection
# ---------------------------------------------------------------------------

def inspect_chunks():
    print("\n" + "=" * 60)
    print("  MILESTONE 3 — Chunk Inspection")
    print("=" * 60)

    documents = load_documents()
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc["text"], doc["filename"])
        all_chunks.extend(chunks)

    print(f"\nTotal chunks produced: {len(all_chunks)}")
    print(f"(Target range: 50–2000)\n")

    print("--- 5 random chunks ---\n")
    sample = random.sample(all_chunks, min(5, len(all_chunks)))
    for i, chunk in enumerate(sample, 1):
        print(f"[Chunk {i}]")
        print(f"  chunk_id : {chunk['chunk_id']}")
        print(f"  source   : {chunk['source']}")
        print(f"  restaurant: {chunk['restaurant']}")
        print(f"  length   : {len(chunk['text'])} chars")
        print(f"  text preview:\n{chunk['text'][:300]}")
        print()

    return all_chunks


# ---------------------------------------------------------------------------
# M4: Retrieval testing
# ---------------------------------------------------------------------------

EVAL_QUERIES = [
    "What's the best Korean restaurant?",
    "What do reviewers say about the wait time at El Antojo?",
    "Which Mexican restaurant do reviewers compare favorably to Alibertos or California Burrito?",
    "What's the most negatively reviewed restaurant?",
    "What's a good price-per-person range for Mexican food?",
]


def test_retrieval():
    print("\n" + "=" * 60)
    print("  MILESTONE 4 — Retrieval Testing")
    print("=" * 60)

    collection = get_collection()
    if collection.count() == 0:
        print("\n⚠️  Vector store is empty. Embedding chunks first...\n")
        documents = load_documents()
        all_chunks = []
        for doc in documents:
            chunks = chunk_document(doc["text"], doc["filename"])
            all_chunks.extend(chunks)
        embed_and_store(all_chunks)

    for i, query in enumerate(EVAL_QUERIES[:3], 1):
        print(f"\n--- Query {i}: {query} ---")
        results = retrieve(query)
        if not results:
            print("  No results returned.")
            continue
        for j, r in enumerate(results, 1):
            print(f"  Result {j} | dist: {r['distance']:.3f} | source: {r['source']}")
            print(f"    {r['text'][:200].strip()}...")
        print()


if __name__ == "__main__":
    inspect_chunks()
    test_retrieval()

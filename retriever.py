import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)

# BM25 index and chunk list — populated lazily on first hybrid query.
_bm25 = None
_all_chunks = []


def get_collection():
    return _collection


def embed_and_store(chunks):
    """Embed chunks and store in ChromaDB with full metadata."""
    _collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{
            "restaurant": c["restaurant"],
            "source": c["source"],
            "food_rating": c.get("food_rating", -1),
            "service_rating": c.get("service_rating", -1),
            "atmosphere_rating": c.get("atmosphere_rating", -1),
            "months_ago": c.get("months_ago", -1),
        } for c in chunks],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector database.")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_all_chunks():
    """Fetch every chunk from ChromaDB into memory for BM25."""
    global _all_chunks
    result = _collection.get(include=["documents", "metadatas"])
    _all_chunks = [
        {
            "text": result["documents"][i],
            "chunk_id": result["ids"][i],
            "restaurant": result["metadatas"][i]["restaurant"],
            "source": result["metadatas"][i]["source"],
            "food_rating": result["metadatas"][i].get("food_rating", -1),
            "service_rating": result["metadatas"][i].get("service_rating", -1),
            "atmosphere_rating": result["metadatas"][i].get("atmosphere_rating", -1),
            "months_ago": result["metadatas"][i].get("months_ago", -1),
        }
        for i in range(len(result["documents"]))
    ]
    return _all_chunks


def _build_bm25():
    global _bm25
    chunks = _load_all_chunks()
    if not chunks:
        return
    tokenized = [c["text"].lower().split() for c in chunks]
    _bm25 = BM25Okapi(tokenized)


def _get_bm25():
    global _bm25
    if _bm25 is None and _collection.count() > 0:
        _build_bm25()
    return _bm25


def _chunk_passes(chunk, where):
    """Return True if a chunk satisfies all conditions in a where dict."""
    if not where:
        return True
    for key, condition in where.items():
        val = chunk.get(key, -1)
        if isinstance(condition, dict):
            for op, threshold in condition.items():
                if op == "$gte" and val < threshold:
                    return False
                if op == "$lte" and val > threshold:
                    return False
                if op == "$eq" and val != threshold:
                    return False
        elif val != condition:
            return False
    return True


def _build_chroma_where(where):
    """
    Convert a simple {key: {op: val}, ...} dict to a ChromaDB-compatible where clause.
    ChromaDB requires $and when filtering on multiple keys simultaneously.
    """
    if not where:
        return None
    conditions = [{k: v} for k, v in where.items()]
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


# ---------------------------------------------------------------------------
# Public retrieval functions
# ---------------------------------------------------------------------------

def retrieve(query, n_results=N_RESULTS, where=None):
    """
    Semantic search using ChromaDB's cosine similarity.

    where: optional dict of metadata filters, e.g.
      {"food_rating": {"$gte": 4}, "months_ago": {"$lte": 12}}
    """
    if _collection.count() == 0:
        return []

    chroma_where = _build_chroma_where(where)
    kwargs = {
        "query_texts": [query],
        "n_results": min(n_results, _collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }
    if chroma_where:
        kwargs["where"] = chroma_where

    try:
        results = _collection.query(**kwargs)
    except Exception:
        # Filter may match zero docs — fall back to unfiltered
        kwargs.pop("where", None)
        results = _collection.query(**kwargs)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    return [
        {
            "text": documents[i],
            "restaurant": metadatas[i]["restaurant"],
            "source": metadatas[i]["source"],
            "chunk_id": ids[i],
            "distance": distances[i],
        }
        for i in range(len(documents))
    ]


def hybrid_retrieve(query, n_results=N_RESULTS, where=None):
    """
    Hybrid search combining semantic (ChromaDB) and keyword (BM25) results
    using Reciprocal Rank Fusion (RRF).

    RRF merges the two ranked lists without needing to normalise their scores:
      score(chunk) = Σ  1 / (RRF_K + rank_in_list)
    Higher score = more relevant.
    """
    RRF_K = 60
    candidate_k = min(n_results * 4, max(_collection.count(), 1))

    # --- Semantic arm ---
    semantic_results = retrieve(query, n_results=candidate_k, where=where)

    # --- BM25 arm ---
    bm25 = _get_bm25()
    if bm25 is None:
        return semantic_results[:n_results]

    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # Rank all chunks by BM25 score, then apply the metadata filter manually
    bm25_ranked_indices = sorted(
        range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True
    )
    bm25_top = [i for i in bm25_ranked_indices if _chunk_passes(_all_chunks[i], where)][:candidate_k]

    # --- RRF fusion ---
    rrf_scores = {}

    for rank, chunk in enumerate(semantic_results):
        cid = chunk["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (RRF_K + rank + 1)

    for rank, idx in enumerate(bm25_top):
        cid = _all_chunks[idx]["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0) + 1 / (RRF_K + rank + 1)

    sorted_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)[:n_results]

    chunk_by_id = {c["chunk_id"]: c for c in _all_chunks}
    semantic_dist = {c["chunk_id"]: c["distance"] for c in semantic_results}

    return [
        {
            "text": chunk_by_id[cid]["text"],
            "restaurant": chunk_by_id[cid]["restaurant"],
            "source": chunk_by_id[cid]["source"],
            "chunk_id": cid,
            "distance": semantic_dist.get(cid, 0.5),
            "rrf_score": rrf_scores[cid],
        }
        for cid in sorted_ids
        if cid in chunk_by_id
    ]

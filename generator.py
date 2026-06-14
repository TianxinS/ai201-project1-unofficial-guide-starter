from groq import Groq
from config import GROQ_API_KEY, LLM_MODEL

_client = Groq(api_key=GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a restaurant recommendation assistant for the Lynnwood, WA area and nearby Puget Sound cities.

Answer questions using ONLY the customer reviews provided in the context. Do not draw on your general knowledge about restaurants.

Guidelines:
- Always name which restaurant(s) the information comes from.
- Quote or closely paraphrase specific details from reviews (dishes, prices, wait times, ratings) rather than speaking in generalities.
- When comparing restaurants, only compare based on what reviewers explicitly said.
- If the retrieved reviews do not contain enough information to answer the question, say clearly: "I don't have enough review information to answer that." Do not guess or invent details.
- Keep answers concise and directly useful — the user wants a recommendation, not a summary of every review."""


def generate_response(query, retrieved_chunks):
    """
    Generate a grounded answer from retrieved review chunks.

    Chunks are formatted into a context block, then passed to the LLM with a
    strict grounding system prompt. Returns the response as a plain string.
    """
    if not retrieved_chunks:
        return (
            "I couldn't find any relevant reviews for your question. "
            "Try asking about a specific restaurant, cuisine, dish, or aspect "
            "like wait time, price, or service."
        )

    context_parts = []
    for chunk in retrieved_chunks:
        context_parts.append(f"[{chunk['restaurant']}]\n{chunk['text']}")
    context = "\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Customer reviews (context):\n\n{context}\n\n"
                f"Question: {query}"
            ),
        },
    ]

    response = _client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )

    answer = response.choices[0].message.content

    # Programmatically append the source files so attribution is guaranteed
    # regardless of whether the LLM included citations in its response.
    unique_sources = list(dict.fromkeys(c["source"] for c in retrieved_chunks))
    source_line = "  •  ".join(unique_sources)
    return f"{answer}\n\n---\n📍 **Retrieved from:** {source_line}"

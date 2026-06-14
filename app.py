import gradio as gr
from ingest import load_documents, chunk_document
from retriever import embed_and_store, retrieve, hybrid_retrieve, get_collection
from generator import generate_response


def run_ingestion():
    collection = get_collection()
    if collection.count() > 0:
        print(f"Vector store already populated ({collection.count()} chunks). Skipping ingestion.")
        print("To re-ingest, delete the ./chroma_db folder and restart.")
        return
    print("Ingesting restaurant review documents...")
    documents = load_documents()
    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc["text"], doc["filename"])
        all_chunks.extend(chunks)
    if all_chunks:
        embed_and_store(all_chunks)
        print(f"Ingestion complete. {len(all_chunks)} chunks stored.")
    else:
        print("\n⚠️  No chunks produced.\n")


def _build_where(min_food, min_service, min_atmosphere, max_months):
    """Build a metadata filter dict from slider values. 0 means no filter on that field."""
    where = {}
    if min_food > 0:
        where["food_rating"] = {"$gte": int(min_food)}
    if min_service > 0:
        where["service_rating"] = {"$gte": int(min_service)}
    if min_atmosphere > 0:
        where["atmosphere_rating"] = {"$gte": int(min_atmosphere)}
    if max_months > 0:
        where["months_ago"] = {"$lte": int(max_months)}
    return where if where else None


def ask(message, history, search_mode, min_food, min_service, min_atmosphere, max_months):
    if not message.strip():
        return history, ""

    where = _build_where(min_food, min_service, min_atmosphere, max_months)

    if search_mode == "Hybrid (BM25 + Semantic)":
        retrieved = hybrid_retrieve(message, where=where)
    else:
        retrieved = retrieve(message, where=where)

    response = generate_response(message, retrieved)
    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ]
    return history, ""


SIDEBAR_HTML = """
<div style="background:#fff7ed; border:1px solid #fed7aa;
            border-radius:10px; padding:1rem; margin-top:0.5rem;">
    <p style="font-size:0.8rem; font-weight:700; color:#9a3412;
               margin:0 0 0.5rem; letter-spacing:0.05em;">
        📍 RESTAURANTS LOADED
    </p>
    <ul style="font-size:0.85rem; color:#c2410c; list-style:none;
                padding:0; margin:0; line-height:1.8;">
        <li>🌮 El Antojo Lynnwood</li>
        <li>🥙 Gyro Grill</li>
        <li>🍲 JangAn Sullungtang</li>
        <li>🍜 Modoo Korean Restaurant</li>
        <li>🌯 Taqueria Costa Sur</li>
        <li>🍗 Wingstop</li>
        <li>🫓 The Yemeni House</li>
    </ul>
    <hr style="border:none; border-top:1px solid #fed7aa; margin:0.75rem 0;">
    <p style="font-size:0.75rem; color:#ea580c; margin:0; line-height:1.5;">
        Answers grounded in loaded reviews only.
    </p>
</div>
"""

with gr.Blocks(title="Restaurant Guide") as demo:

    gr.HTML("""
        <div style="text-align:center; padding:1.25rem 0 0.5rem;">
            <h1 style="font-size:2rem; font-weight:700; color:#9a3412; margin:0;">
                🍽️ The Unofficial Restaurant Guide
            </h1>
            <p style="color:#6b7280; font-size:1rem; margin:0.4rem 0 0;">
                Ask anything about local restaurants — answers grounded in real customer reviews.
            </p>
        </div>
    """)

    with gr.Row():
        # --- Chat column ---
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=440, label="Chat")
            with gr.Row():
                msg = gr.Textbox(
                    placeholder='e.g. "Where can I get good Korean soup?"',
                    show_label=False,
                    scale=8,
                )
                submit_btn = gr.Button("Ask", scale=1, variant="primary")
            gr.Examples(
                examples=[
                    "What's the best Korean restaurant?",
                    "What do reviewers say about the wait time at El Antojo?",
                    "Which Mexican restaurant compares favorably to Alibertos?",
                    "What's the most negatively reviewed restaurant?",
                    "What's a good price range for Mexican food?",
                    "Which restaurant has the best broth?",
                    "Is JangAn kid-friendly?",
                ],
                inputs=msg,
            )

        # --- Controls column ---
        with gr.Column(scale=1, min_width=200):
            gr.HTML(SIDEBAR_HTML)

            search_mode = gr.Radio(
                choices=["Semantic Only", "Hybrid (BM25 + Semantic)"],
                value="Semantic Only",
                label="🔍 Search Mode",
            )
            gr.HTML("<p style='font-size:0.75rem; color:#6b7280; margin:0.25rem 0 0.75rem;'>"
                    "Hybrid combines keyword + semantic search using RRF.</p>")

            gr.Markdown("**⭐ Rating Filters** (0 = no filter)")
            min_food = gr.Slider(0, 5, value=0, step=1, label="Min Food Rating")
            min_service = gr.Slider(0, 5, value=0, step=1, label="Min Service Rating")
            min_atmosphere = gr.Slider(0, 5, value=0, step=1, label="Min Atmosphere Rating")

            gr.Markdown("**📅 Recency Filter** (0 = no filter)")
            max_months = gr.Slider(0, 36, value=0, step=1, label="Max age (months)")

    inputs = [msg, chatbot, search_mode, min_food, min_service, min_atmosphere, max_months]
    outputs = [chatbot, msg]

    submit_btn.click(ask, inputs=inputs, outputs=outputs)
    msg.submit(ask, inputs=inputs, outputs=outputs)


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  Restaurant Guide — starting up")
    print("=" * 50 + "\n")
    run_ingestion()
    demo.launch(theme=gr.themes.Soft(primary_hue="orange"))

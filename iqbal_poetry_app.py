"""
╔══════════════════════════════════════════════════════════╗
║       IQBAL POETRY INTELLIGENCE — RAG + GGUF App         ║
║  Uses: Meta-Llama-3.1-8B GGUF + FAISS + Multilingual     ║
╚══════════════════════════════════════════════════════════╝

Requirements:
    pip install gradio langchain-huggingface langchain-community faiss-gpu
    pip install llama-cpp-python (with CUDA: CMAKE_ARGS="-DLLGGUF_CUBLAS=on" pip install llama-cpp-python)

Run: python iqbal_poetry_app.py
"""

import json
import os
import gradio as gr
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from llama_cpp import Llama

# ─────────────────────────────────────────────
#  CONFIG — update paths if needed
# ─────────────────────────────────────────────
GGUF_MODEL_PATH = r"D:\Langchain_RAG\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
FAISS_INDEX_PATH = "iqbal_index"
EMBED_MODEL      = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TOP_K            = 4        # retrieved verses
N_CTX            = 4096     # context window for LLM
N_GPU_LAYERS     = 35       # layers offloaded to GPU (RTX 4060 Ti: 35–40 is ideal)

# ─────────────────────────────────────────────
#  LOAD MODELS (once at startup)
# ─────────────────────────────────────────────
print("🌙 Loading Iqbal Poetry Intelligence...")

print("  ↳ Loading multilingual embeddings on GPU...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cuda"}
)

print("  ↳ Loading FAISS vector index...")
db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

print(f"  ↳ Loading GGUF LLM: {os.path.basename(GGUF_MODEL_PATH)}...")
llm = Llama(
    model_path=GGUF_MODEL_PATH,
    n_ctx=N_CTX,
    n_gpu_layers=N_GPU_LAYERS,
    verbose=False,
    chat_format="llama-3",
    flash_attn=False,
    use_mmap=True,
    use_mlock=False,
)

print("✅ All models loaded. Starting Gradio UI...\n")


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def extract_verse_text(verse_data: dict) -> dict:
    """Extract Original / Urdu / English from a verse dict."""
    result = {"original": "", "urdu": "", "english": ""}
    for text in verse_data.get("Text", []):
        lang    = text.get("lang", "")
        content = text.get("_content", "").strip()
        if lang == "Original": result["original"] = content
        elif lang == "Urdu":   result["urdu"]     = content
        elif lang == "English":result["english"]  = content
    return result


def format_context_for_llm(docs: list) -> str:
    """Build a clean context block from retrieved documents."""
    context_parts = []
    for i, doc in enumerate(docs, 1):
        try:
            data      = json.loads(doc.page_content)
            book_name = data.get("bookName", doc.metadata.get("book", "Unknown"))
            poem_name = data.get("name", "Untitled")
            verses_text = []
            for para in data.get("Para", []):
                for verse in para.get("Verse", []):
                    v = extract_verse_text(verse)
                    if v["english"]:
                        verses_text.append(v["english"])
                    elif v["urdu"]:
                        verses_text.append(v["urdu"])
                    elif v["original"]:
                        verses_text.append(v["original"])
            combined = "\n".join(verses_text[:6])  # limit to avoid token overflow
            context_parts.append(
                f"[Excerpt {i} — Book: {book_name} | Poem: {poem_name}]\n{combined}"
            )
        except Exception:
            context_parts.append(f"[Excerpt {i}]\n{doc.page_content[:400]}")
    return "\n\n".join(context_parts)


def build_html_results(docs: list) -> str:
    """Build styled HTML cards for retrieved verses."""
    cards = []
    for i, doc in enumerate(docs, 1):
        try:
            data      = json.loads(doc.page_content)
            book_name = data.get("bookName", doc.metadata.get("book", "Unknown"))
            poem_name = data.get("name", "Untitled")
            verse_blocks = []
            for para in data.get("Para", []):
                para_name = para.get("name", "")
                if para_name:
                    verse_blocks.append(
                        f'<div class="para-title">{para_name}</div>'
                    )
                for verse in para.get("Verse", [])[:3]:
                    v = extract_verse_text(verse)
                    block = '<div class="verse-block">'
                    if v["original"]:
                        block += f'<div class="original">{v["original"]}</div>'
                    if v["urdu"]:
                        block += f'<div class="urdu">{v["urdu"]}</div>'
                    if v["english"]:
                        block += f'<div class="english">{v["english"]}</div>'
                    block += "</div>"
                    verse_blocks.append(block)
            verses_html = "".join(verse_blocks) if verse_blocks else "<p>No verses found.</p>"
            cards.append(f"""
            <div class="result-card">
                <div class="card-header">
                    <span class="card-num">#{i}</span>
                    <span class="book-badge">{book_name}</span>
                    <span class="poem-name">{poem_name}</span>
                </div>
                <div class="card-body">{verses_html}</div>
            </div>""")
        except Exception as e:
            cards.append(f"""
            <div class="result-card">
                <div class="card-header"><span class="card-num">#{i}</span> Raw</div>
                <div class="card-body"><pre>{doc.page_content[:400]}</pre></div>
            </div>""")
    return "".join(cards)


# ─────────────────────────────────────────────
#  CORE RAG + LLM PIPELINE
# ─────────────────────────────────────────────
def iqbal_query(query: str, mode: str, history: list):
    """
    mode: "Understand & Explain" | "Find Verses Only" | "Thematic Analysis" | "Comparative Study"
    """
    if not query.strip():
        yield history, "", "<p style='color:#888'>Please enter a query.</p>"
        return

    # 1. Retrieve
    docs = db.similarity_search(query, k=TOP_K)
    verses_html = build_html_results(docs)
    context     = format_context_for_llm(docs)

    # 2. Build prompt based on mode
    if mode == "Find Verses Only":
        yield history, "", verses_html
        return

    mode_instructions = {
        "Understand & Explain": (
            "You are a scholar of Allama Iqbal's philosophy and poetry. "
            "Using the provided verses as context, explain the meaning, symbolism, and "
            "philosophical significance of the topic to the user. "
            "Reference specific images like Khudi (self), Shaheen (eagle), Ishq (love), "
            "and Faqr (spiritual poverty) where relevant. Be insightful and poetic in tone."
        ),
        "Thematic Analysis": (
            "You are an academic expert on Iqbal's poetry. Perform a deep thematic analysis "
            "of the query using the provided verse excerpts. Identify recurring motifs, "
            "philosophical themes (from Asrar-e-Khudi, Reconstruction of Religious Thought, etc.), "
            "and connect them to Islamic mysticism, Nietzsche, Bergson, or Rumi where applicable."
        ),
        "Comparative Study": (
            "You are a comparative literature scholar. Using the provided Iqbal verses, "
            "compare and contrast how Iqbal treats this topic versus classical Sufi poets "
            "like Rumi, Hafiz, or modern thinkers. Highlight what makes Iqbal's perspective unique."
        ),
    }

    system_prompt = mode_instructions.get(mode, mode_instructions["Understand & Explain"])

    user_message = f"""Topic/Question: {query}

Relevant verses from Iqbal's works:
───────────────────────────────────
{context}
───────────────────────────────────

Please provide your analysis."""

    messages = [{"role": "system", "content": system_prompt}]
    # Add chat history
    for human, assistant in history:
        messages.append({"role": "user",      "content": human})
        messages.append({"role": "assistant", "content": assistant})
    messages.append({"role": "user", "content": user_message})

    # 3. Stream LLM response
    full_response = ""
    new_history   = history + [[query, ""]]

    for chunk in llm.create_chat_completion(
        messages=messages,
        max_tokens=900,
        temperature=0.7,
        top_p=0.9,
        stream=True,
    ):
        delta = chunk["choices"][0]["delta"].get("content", "")
        if delta:
            full_response          += delta
            new_history[-1][1]      = full_response
            yield new_history, "", verses_html

    yield new_history, "", verses_html


def clear_chat():
    return [], "", ""


# ─────────────────────────────────────────────
#  GRADIO UI
# ─────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=Noto+Nastaliq+Urdu&display=swap');

:root {
    --gold:    #c9a84c;
    --gold-lt: #e8c97a;
    --ink:     #0d0b08;
    --paper:   #f5efe0;
    --parch:   #ede0c4;
    --deep:    #1a1508;
    --rust:    #8b3a1a;
    --teal:    #1a5f5a;
    --muted:   #5a4f3a;
}

/* ── Global ── */
body, .gradio-container {
    background: var(--ink) !important;
    font-family: 'EB Garamond', serif !important;
    color: var(--paper) !important;
}

/* ── Header ── */
.iqbal-header {
    text-align: center;
    padding: 2.5rem 1rem 1rem;
    background: radial-gradient(ellipse at 50% 0%, #3d2b0a 0%, var(--ink) 70%);
    border-bottom: 1px solid #3a2e18;
    position: relative;
    overflow: hidden;
}
.iqbal-header::before {
    content: "";
    position: absolute; inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M30 5 L35 20 L50 20 L38 29 L43 44 L30 35 L17 44 L22 29 L10 20 L25 20 Z' fill='none' stroke='%23c9a84c' stroke-width='0.3' opacity='0.15'/%3E%3C/svg%3E");
    opacity: 0.4;
}
.iqbal-header h1 {
    font-family: 'Cinzel Decorative', cursive !important;
    font-size: 2.4rem !important;
    color: var(--gold) !important;
    margin: 0 !important;
    letter-spacing: 0.05em;
    text-shadow: 0 0 40px rgba(201,168,76,0.4);
}
.iqbal-header .subtitle {
    font-family: 'EB Garamond', serif;
    font-style: italic;
    color: var(--gold-lt);
    font-size: 1.05rem;
    opacity: 0.8;
    margin-top: 0.3rem;
}
.iqbal-header .urdu-title {
    font-family: 'Noto Nastaliq Urdu', serif;
    font-size: 1.6rem;
    color: var(--gold);
    direction: rtl;
    margin-top: 0.5rem;
    opacity: 0.9;
}
.divider-ornament {
    color: var(--gold);
    font-size: 1.4rem;
    text-align: center;
    margin: 0.5rem 0;
    opacity: 0.6;
    letter-spacing: 0.5rem;
}

/* ── Panels ── */
.panel-label {
    font-family: 'Cinzel Decorative', cursive !important;
    font-size: 0.75rem !important;
    color: var(--gold) !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.gr-box, .gr-panel, .gradio-box {
    background: #14110a !important;
    border: 1px solid #2e2514 !important;
    border-radius: 8px !important;
}

/* ── Chat ── */
.chatbot {
    background: #100e08 !important;
    border: 1px solid #2e2514 !important;
    border-radius: 8px !important;
    font-family: 'EB Garamond', serif !important;
    font-size: 1.05rem !important;
}
.chatbot .message.user {
    background: #1e1708 !important;
    border: 1px solid #3a2e18 !important;
    color: var(--gold-lt) !important;
    border-radius: 8px 8px 2px 8px !important;
}
.chatbot .message.bot {
    background: #0d1510 !important;
    border: 1px solid #1a3528 !important;
    color: #d4e8d0 !important;
    border-radius: 8px 8px 8px 2px !important;
    line-height: 1.75 !important;
}

/* ── Input ── */
textarea, input[type="text"] {
    background: #1a1508 !important;
    border: 1px solid var(--gold) !important;
    color: var(--paper) !important;
    font-family: 'EB Garamond', serif !important;
    font-size: 1.1rem !important;
    border-radius: 6px !important;
    caret-color: var(--gold);
}
textarea:focus, input[type="text"]:focus {
    box-shadow: 0 0 12px rgba(201,168,76,0.25) !important;
    border-color: var(--gold-lt) !important;
}

/* ── Buttons ── */
button.primary {
    background: linear-gradient(135deg, #7a5a10 0%, #c9a84c 50%, #7a5a10 100%) !important;
    color: var(--ink) !important;
    font-family: 'Cinzel Decorative', cursive !important;
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.6rem 1.5rem !important;
    cursor: pointer;
    transition: all 0.2s;
    box-shadow: 0 2px 12px rgba(201,168,76,0.3);
}
button.primary:hover {
    box-shadow: 0 4px 20px rgba(201,168,76,0.5) !important;
    transform: translateY(-1px);
}
button.secondary {
    background: transparent !important;
    color: var(--muted) !important;
    border: 1px solid #2e2514 !important;
    font-family: 'EB Garamond', serif !important;
    border-radius: 6px !important;
}

/* ── Mode Radio ── */
.gr-radio label {
    color: var(--paper) !important;
    font-family: 'EB Garamond', serif !important;
}

/* ── Verse Cards ── */
.result-card {
    background: linear-gradient(160deg, #1a1508 0%, #120f07 100%);
    border: 1px solid #3a2e18;
    border-radius: 10px;
    margin: 0.8rem 0;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    transition: transform 0.2s, box-shadow 0.2s;
}
.result-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(201,168,76,0.15);
}
.card-header {
    background: linear-gradient(90deg, #2a1f06 0%, #1a1508 100%);
    border-bottom: 1px solid #3a2e18;
    padding: 0.6rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-wrap: wrap;
}
.card-num {
    font-family: 'Cinzel Decorative', cursive;
    color: var(--gold);
    font-size: 0.85rem;
    font-weight: 700;
}
.book-badge {
    background: rgba(201,168,76,0.15);
    border: 1px solid rgba(201,168,76,0.35);
    color: var(--gold-lt);
    padding: 0.15rem 0.6rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-family: 'EB Garamond', serif;
}
.poem-name {
    color: var(--muted);
    font-style: italic;
    font-size: 0.95rem;
    font-family: 'EB Garamond', serif;
}
.card-body {
    padding: 1rem 1.2rem;
}
.verse-block {
    border-left: 2px solid rgba(201,168,76,0.3);
    padding-left: 1rem;
    margin: 0.75rem 0;
}
.original {
    font-family: 'Noto Nastaliq Urdu', serif;
    direction: rtl;
    font-size: 1.3rem;
    color: var(--gold-lt);
    line-height: 2.2;
    margin-bottom: 0.3rem;
}
.urdu {
    font-family: 'Noto Nastaliq Urdu', serif;
    direction: rtl;
    font-size: 1.1rem;
    color: #c8b87a;
    line-height: 2;
    margin-bottom: 0.3rem;
}
.english {
    font-family: 'EB Garamond', serif;
    font-style: italic;
    color: #9ab89a;
    font-size: 1rem;
    line-height: 1.6;
}
.para-title {
    font-family: 'Cinzel Decorative', cursive;
    color: var(--rust);
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0.5rem 0 0.25rem;
    opacity: 0.8;
}

/* ── Verses Panel ── */
.verses-panel {
    background: #0d0b08;
    border: 1px solid #2e2514;
    border-radius: 8px;
    padding: 1rem;
    max-height: 600px;
    overflow-y: auto;
}
.verses-panel::-webkit-scrollbar { width: 4px; }
.verses-panel::-webkit-scrollbar-track { background: #1a1508; }
.verses-panel::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 2px; }

/* ── Footer ── */
.iqbal-footer {
    text-align: center;
    padding: 1rem;
    color: var(--muted);
    font-style: italic;
    font-size: 0.9rem;
    border-top: 1px solid #2e2514;
    margin-top: 1rem;
}
"""

HEADER_HTML = """
<div class="iqbal-header">
    <h1>✦ Iqbal Intelligence ✦</h1>
    <div class="urdu-title">اقبال کی شاعری کو سمجھیں</div>
    <div class="subtitle">Explore the Philosophy & Poetry of Allama Iqbal · Powered by RAG + Llama 3.1</div>
    <div class="divider-ornament">❧ ✦ ❧</div>
</div>
"""

FOOTER_HTML = """
<div class="iqbal-footer">
    Powered by Meta-Llama-3.1-8B · FAISS Semantic Search · Multilingual Embeddings
    <br><em>"Rise up beyond the limits of the sky — that is your destiny."</em>
</div>
"""

with gr.Blocks(title="Iqbal Intelligence") as demo:

    gr.HTML(HEADER_HTML)

    with gr.Row():
        # ── Left: Chat ──────────────────────────────
        with gr.Column(scale=3):
            gr.HTML('<div class="panel-label">💬 Ask & Understand</div>')
            chatbot = gr.Chatbot(
                label="",
                height=460,
                elem_classes=["chatbot"],
                show_label=False,
            )
            with gr.Row():
                query_input = gr.Textbox(
                    placeholder="Ask about Khudi, Shaheen, Ishq, Faqr, or any theme...",
                    show_label=False,
                    lines=2,
                    scale=5,
                )
                with gr.Column(scale=1, min_width=120):
                    submit_btn = gr.Button("✦ Ask", variant="primary")
                    clear_btn  = gr.Button("Clear", variant="secondary")

            gr.HTML('<div class="panel-label" style="margin-top:0.8rem">🎭 Mode</div>')
            mode_radio = gr.Radio(
                choices=["Understand & Explain", "Find Verses Only", "Thematic Analysis", "Comparative Study"],
                value="Understand & Explain",
                show_label=False,
            )

        # ── Right: Verses ────────────────────────────
        with gr.Column(scale=2):
            gr.HTML('<div class="panel-label">📜 Retrieved Verses</div>')
            verses_output = gr.HTML(
                value='<div class="verses-panel"><p style="color:#5a4f3a;font-style:italic;text-align:center;margin-top:2rem">Your retrieved verses will appear here...</p></div>',
                elem_classes=["verses-panel"],
            )

    gr.HTML(FOOTER_HTML)

    # ── Event handlers ──────────────────────────────
    state = gr.State([])

    def on_submit(query, mode, history):
        full_html_wrapper = '<div class="verses-panel">{}</div>'
        for new_hist, _, verses_html in iqbal_query(query, mode, history):
            yield new_hist, "", full_html_wrapper.format(verses_html)

    submit_btn.click(
        fn=on_submit,
        inputs=[query_input, mode_radio, chatbot],
        outputs=[chatbot, query_input, verses_output],
    )
    query_input.submit(
        fn=on_submit,
        inputs=[query_input, mode_radio, chatbot],
        outputs=[chatbot, query_input, verses_output],
    )
    clear_btn.click(
        fn=lambda: ([], "", '<div class="verses-panel"><p style="color:#5a4f3a;font-style:italic;text-align:center;margin-top:2rem">Search cleared.</p></div>'),
        outputs=[chatbot, query_input, verses_output],
    )


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,       # set True to get a public gradio.live link
        inbrowser=True,
        css=CUSTOM_CSS,
    )





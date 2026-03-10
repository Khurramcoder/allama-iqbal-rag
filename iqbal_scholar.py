"""
╔══════════════════════════════════════════════════════════════╗
║         IQBAL POETRY INTELLIGENCE — Final App                ║
║                                                              ║
║  Reads ALL books from JSON files in:                         ║
║    E:\allama-iqbal.com-main\allama-iqbal.com-main\           ║
║       src\assets\content\                                    ║
║                                                              ║
║  Portrait : E:\allama-iqbal.com-main\Allama-Iqbal-2.jpg      ║
║  LLM      : Ollama → iqbal-llama (your local GGUF)           ║
║                                                              ║
║  ONE-TIME SETUP:                                             ║
║    1. Install Ollama: https://ollama.com/download/windows    ║
║    2. In PowerShell:                                         ║
║         $text = "FROM D:\Langchain_RAG\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`nPARAMETER temperature 0.35`nPARAMETER num_predict 600"
║         $text | Out-File "D:\Langchain_RAG\Modelfile" -Encoding utf8
║         ollama create iqbal-llama -f D:\Langchain_RAG\Modelfile
║    3. python iqbal_scholar.py                                ║
╚══════════════════════════════════════════════════════════════╝
"""
import os
os.environ['HUGGINGFACE_HUB_DISABLE_SYMLINKS'] = '1'
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import json
import requests
import gradio as gr
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ─────────────────────────────────────────────────────────
#  PATHS
# ─────────────────────────────────────────────────────────
BASE_DIR    = r"E:\allama-iqbal.com-main"
CONTENT_DIR = os.path.join(BASE_DIR, "allama-iqbal.com-main", "src", "assets", "content")
IQBAL_IMAGE = os.path.join(BASE_DIR, "Allama-Iqbal-2.jpg")
INDEX_DIR   = os.path.join(BASE_DIR, "iqbal_index")

EMBED_MODEL  = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OLLAMA_MODEL = "iqbal-llama:latest"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
TOP_K        = 4

# ─────────────────────────────────────────────────────────
#  STEP 1 — Parse JSON books into rich Documents
# ─────────────────────────────────────────────────────────
def parse_json_file(fpath: str, book_folder: str) -> list:
    """Parse one poem JSON file into a list of Documents."""
    docs = []
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return docs

        book_label  = data.get("bookName",    book_folder)
        poem_name   = data.get("name",        os.path.basename(fpath))
        section     = data.get("sectionName", "")

        for para in data.get("Para", []):
            para_name    = para.get("name",    "")
            para_name_en = para.get("name-en", "")
            para_label   = f"{para_name} / {para_name_en}".strip(" /")

            for verse in para.get("Verse", []):
                v = {"original": "", "urdu": "", "english": ""}
                for text in verse.get("Text", []):
                    lang    = text.get("lang", "")
                    content = text.get("_content", "").strip()
                    if lang == "Original": v["original"] = content
                    elif lang == "Urdu":   v["urdu"]     = content
                    elif lang == "English":v["english"]  = content

                if not any(v.values()):
                    continue

                # Build searchable content combining original + English
                content = " | ".join(x for x in [v["original"], v["english"]] if x)

                docs.append(Document(
                    page_content=content,
                    metadata={
                        "book":     book_label,
                        "poem":     poem_name,
                        "section":  section,
                        "para":     para_label,
                        "original": v["original"],
                        "urdu":     v["urdu"],
                        "english":  v["english"],
                    }
                ))
    except Exception as e:
        print(f"  ⚠ Skipped {os.path.basename(fpath)}: {e}")
    return docs

def load_from_json(content_dir: str) -> list:
    """Walk all book folders and parse every JSON poem file."""
    all_docs    = []
    books_found = []

    for root, dirs, files in os.walk(content_dir):
        for fname in sorted(files):
            if not fname.endswith(".json"):
                continue
            fpath       = os.path.join(root, fname)
            book_folder = os.path.relpath(fpath, content_dir).split(os.sep)[0]
            docs        = parse_json_file(fpath, book_folder)
            all_docs.extend(docs)
            if book_folder not in books_found:
                books_found.append(book_folder)

    print(f"  -> {len(books_found)} books: {', '.join(sorted(books_found))}")
    return all_docs

def load_from_txt(path: str) -> list:
    """Fallback: load from flat verse text file."""
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    return [Document(
        page_content=ln,
        metadata={"book": "unknown", "poem": "", "section": "",
                  "para": "", "original": ln, "urdu": "", "english": ""}
    ) for ln in lines]

# ─────────────────────────────────────────────────────────
#  STEP 2 — Embeddings + FAISS
# ─────────────────────────────────────────────────────────
print("Initialising Iqbal Poetry Intelligence…")
print("  -> Loading multilingual embeddings on GPU…")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBED_MODEL,
    model_kwargs={"device": "cpu"},  # Ensure this is "cpu"
    encode_kwargs={"normalize_embeddings": True},
)

faiss_file = os.path.join(INDEX_DIR, "index.faiss")
if os.path.exists(faiss_file):
    print(f"  -> Loading FAISS index from: {INDEX_DIR}")
    db = FAISS.load_local(INDEX_DIR, embeddings, allow_dangerous_deserialization=True)
else:
    if os.path.exists(CONTENT_DIR):
        print(f"  -> Building rich index from JSON books…")
        docs = load_from_json(CONTENT_DIR)
    elif os.path.exists(VERSES_TXT):
        print(f"  -> JSON not found — falling back to {VERSES_TXT}")
        docs = load_from_txt(VERSES_TXT)
    else:
        raise FileNotFoundError(
            f"No data found.\nExpected: {CONTENT_DIR}\nor: {VERSES_TXT}"
        )
    print(f"  -> Indexing {len(docs)} verse documents…")
    db = FAISS.from_documents(docs, embeddings)
    os.makedirs(INDEX_DIR, exist_ok=True)
    db.save_local(INDEX_DIR)
    print(f"  -> Index saved → {INDEX_DIR}")

# ─────────────────────────────────────────────────────────
#  STEP 3 — Check Ollama
# ─────────────────────────────────────────────────────────
print(f"  -> Connecting to Ollama model: {OLLAMA_MODEL}…")
try:
    # Use 127.0.0.1 instead of localhost
    requests.get("http://127.0.0.1:11434", timeout=5)
    print("[OK] Ollama server found.\n")
except Exception as e:
    print(f"[ERROR] Could not connect to Ollama: {e}")

# ─────────────────────────────────────────────────────────
#  STEP 4 — RAG pipeline
# ─────────────────────────────────────────────────────────
def format_verse_card(doc: Document) -> str:
    """Format retrieved verse with full metadata for display."""
    m       = doc.metadata
    book    = m.get("book",    "")
    poem    = m.get("poem",    "")
    para    = m.get("para",    "")
    orig    = m.get("original","")
    urdu    = m.get("urdu",   "")
    english = m.get("english", "")

    lines = []
    if book or poem:
        lines.append(f"📖 {book}  •  {poem}")
    if para:
        lines.append(f"   [{para}]")
    if orig:
        lines.append(f"\n   {orig}")
    if urdu:
        # Urdu is often a note/explanation — show first 120 chars
        lines.append(f"   {urdu[:120]}…" if len(urdu) > 120 else f"   {urdu}")
    if english:
        lines.append(f"   ✦ {english}")
    return "\n".join(lines)

def retrieve(query: str):
    results = db.similarity_search(query, k=TOP_K)

    # Context for LLM: English preferred, fallback to original
    context_parts = []
    for doc in results:
        m       = doc.metadata
        book    = m.get("book", "")
        poem    = m.get("poem", "")
        english = m.get("english", "")
        original= m.get("original","")
        text    = english or original
        label   = f"[{book} — {poem}]" if (book or poem) else ""
        context_parts.append(f"{label}\n{text[:350]}")

    context     = "\n\n".join(context_parts)
    verse_cards = "\n\n─────────────────────────────\n\n".join(
        format_verse_card(d) for d in results
    )
    return context, verse_cards

def generate_answer(query: str):
    if not query or not query.strip():
        return "*Please enter a question.*", ""

    context, verse_cards = retrieve(query)

    prompt = f"""<|start_header_id|>system<|end_header_id|>
You are a distinguished scholar of Allama Iqbal's poetry and philosophy.
Using the retrieved verses below as context, answer the user's question with depth and clarity.
When referencing Urdu or Persian verses, explain their meaning in English.
Mention the book and poem name where relevant. Be insightful, poetic, and precise.

Retrieved verses:
{context}
<|eot_id|><|start_header_id|>user<|end_header_id|>
{query}
<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    try:
        r = requests.post(OLLAMA_URL, json={
    "model": OLLAMA_MODEL,
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.5,         # Slightly higher for more variety
        "num_predict": 600,
        "num_ctx": 4096,
        "repeat_penalty": 1.2,      # Prevents the loop you just saw
        "top_p": 0.9                # Helps the model stay coherent
    }
}, timeout=180)
        answer = r.json().get("response", "").strip()
        if not answer:
            answer = "*(No response — check Ollama is running and iqbal-llama is loaded)*"
    except requests.exceptions.ConnectionError:
        answer = (
            "[ERROR] **Ollama is not running.**\n\n"
            "Open a new terminal and run:\n```\nollama serve\n```"
        )
    except Exception as e:
        answer = f"[ERROR] Error: {e}"

    return answer, verse_cards

# ─────────────────────────────────────────────────────────
#  STEP 5 — CSS & HTML
# ─────────────────────────────────────────────────────────
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Noto+Nastaliq+Urdu&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
    --deep:      #0e0d09;
    --panel:     #13120d;
    --border:    #2a2416;
    --gold:      #c8a951;
    --gold-dim:  #8a7235;
    --gold-glow: rgba(200,169,81,0.15);
    --cream:     #ede3c8;
    --parchment: #c8b890;
    --muted:     #6b5f42;
    --radius:    10px;
}

body, .gradio-container {
    background: #090805 !important;
    background-image:
        radial-gradient(ellipse 100% 55% at 50% 0%,   rgba(200,169,81,0.07) 0%, transparent 65%),
        radial-gradient(ellipse 60%  40% at 100% 100%, rgba(100,50,10,0.05)  0%, transparent 60%) !important;
    font-family: 'Cormorant Garamond', serif !important;
    color: var(--cream) !important;
}

.iq-header {
    text-align: center; padding: 2.8rem 2rem 1.8rem;
    background: linear-gradient(180deg, #161208 0%, transparent 100%);
    border-bottom: 1px solid var(--border); position: relative;
}
.iq-header::after {
    content: ""; position: absolute; bottom: 0; left: 8%; right: 8%; height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold-dim), var(--gold), var(--gold-dim), transparent);
}
.iq-moon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 54px; height: 54px; border: 1px solid var(--gold-dim); border-radius: 50%;
    font-size: 1.5rem; color: var(--gold); margin-bottom: .9rem;
    box-shadow: 0 0 30px var(--gold-glow);
    animation: moon-pulse 4s ease-in-out infinite;
}
@keyframes moon-pulse {
    0%, 100% { box-shadow: 0 0 22px var(--gold-glow); }
    50%       { box-shadow: 0 0 44px rgba(200,169,81,0.28); }
}
.iq-title {
    font-family: 'Playfair Display', serif !important;
    font-size: clamp(1.9rem, 3.8vw, 3rem) !important; font-weight: 700 !important;
    color: var(--gold) !important; letter-spacing: 0.04em; margin: 0 !important;
    text-shadow: 0 0 50px rgba(200,169,81,0.22);
}
.iq-urdu {
    font-family: 'Noto Nastaliq Urdu', serif; font-size: 1.55rem; direction: rtl;
    color: var(--parchment); margin-top: .45rem; opacity: .88;
}
.iq-sub { font-style: italic; font-size: .98rem; color: var(--muted); margin-top: .35rem; letter-spacing: .07em; }
.iq-divider {
    display: flex; align-items: center; justify-content: center;
    gap: .8rem; margin-top: 1rem; color: var(--gold-dim); font-size: 1rem;
}
.iq-divider span { flex: 1; max-width: 100px; height: 1px; background: linear-gradient(90deg, transparent, var(--gold-dim)); }
.iq-divider span:last-child { transform: scaleX(-1); }

.portrait-col img {
    border-radius: var(--radius) !important; border: 1px solid var(--border) !important;
    box-shadow: 0 6px 40px rgba(0,0,0,0.6), 0 0 0 1px rgba(200,169,81,0.08) !important;
    filter: sepia(12%) contrast(1.05) brightness(0.98); width: 100% !important;
}

.sec-lbl {
    font-family: 'Playfair Display', serif; font-size: .68rem; letter-spacing: .2em;
    text-transform: uppercase; color: var(--gold-dim); margin-bottom: .4rem; margin-top: .2rem;
}

textarea, input[type="text"] {
    background: var(--panel) !important; border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important; color: var(--cream) !important;
    font-family: 'Cormorant Garamond', serif !important; font-size: 1.12rem !important;
    caret-color: var(--gold); transition: border-color .2s, box-shadow .2s;
}
textarea:focus, input:focus {
    border-color: var(--gold-dim) !important;
    box-shadow: 0 0 0 3px var(--gold-glow) !important; outline: none !important;
}

button.primary {
    background: linear-gradient(135deg, #55400c 0%, #c8a951 50%, #55400c 100%) !important;
    color: #0a0800 !important; font-family: 'Playfair Display', serif !important;
    font-size: .88rem !important; font-weight: 700 !important; letter-spacing: .14em !important;
    text-transform: uppercase !important; border: none !important;
    border-radius: var(--radius) !important; padding: .65rem 1.8rem !important;
    box-shadow: 0 2px 18px rgba(200,169,81,0.22); transition: all .25s ease; cursor: pointer !important;
}
button.primary:hover {
    box-shadow: 0 4px 32px rgba(200,169,81,0.42) !important; transform: translateY(-2px) !important;
}

.answer-panel {
    background: linear-gradient(160deg, #131109 0%, #0d0c08 100%);
    border: 1px solid var(--border); border-radius: var(--radius);
    padding: 1.4rem 1.6rem; min-height: 160px;
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.13rem !important; line-height: 1.9 !important;
}
.answer-panel p      { color: var(--cream) !important; margin-bottom: .6rem; }
.answer-panel strong { color: var(--gold) !important; }
.answer-panel em     { color: var(--parchment) !important; }

.gr-accordion { background: #0d0c08 !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
.gr-accordion summary { color: var(--muted) !important; font-family: 'Cormorant Garamond', serif !important; font-style: italic; }

.gr-examples { border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
.gr-examples button {
    background: var(--panel) !important; border: 1px solid var(--border) !important;
    color: var(--parchment) !important; font-family: 'Cormorant Garamond', serif !important;
    font-size: .95rem !important; border-radius: 6px !important; transition: all .2s;
}
.gr-examples button:hover { border-color: var(--gold-dim) !important; color: var(--gold) !important; background: #1c1a11 !important; }

.gr-markdown h1, .gr-markdown h2, .gr-markdown h3 { font-family: 'Playfair Display', serif !important; color: var(--gold) !important; }
.gr-markdown p { color: var(--cream) !important; line-height: 1.8 !important; }

.iq-footer {
    text-align: center; padding: 1.2rem 1rem; color: var(--muted);
    font-style: italic; font-size: .88rem;
    border-top: 1px solid var(--border); margin-top: 1.2rem;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--deep); }
::-webkit-scrollbar-thumb { background: var(--gold-dim); border-radius: 3px; }

.gr-box, .gr-panel { background: var(--deep) !important; border: 1px solid var(--border) !important; border-radius: var(--radius) !important; }
"""

HEADER_HTML = """
<div class="iq-header">
    <div class="iq-moon">☽</div>
    <h1 class="iq-title">Wisdom of the East</h1>
    <div class="iq-urdu">حکیمِ الامت — علامہ محمد اقبال</div>
    <p class="iq-sub">An AI Scholar of Allama Iqbal's Poetry &amp; Philosophy · Powered by Llama 3.1 + RAG</p>
    <div class="iq-divider"><span></span>✦<span></span></div>
</div>
"""

FOOTER_HTML = """
<div class="iq-footer">
    Meta-Llama 3.1 · 8B · Q4_K_M &nbsp;·&nbsp; Ollama &nbsp;·&nbsp; FAISS Semantic Search &nbsp;·&nbsp;
    Multilingual Embeddings &nbsp;·&nbsp; 12 Books · Original + Urdu + English
    <br><em>"Tu shaheen hai, parwaz hai kaam tera — tere saamne aasmaan aur bhi hain"</em>
</div>
"""

EXAMPLES = [
    ["What is Iqbal's concept of Khudi (Selfhood)?"],
    ["Explain the significance of Shaheen (Eagle) in his poetry."],
    ["اقبال کے کلام میں خودی کا کیا مفہوم ہے؟"],
    ["What does Iqbal say about the youth of the Muslim Ummah?"],
    ["شکوہ اور جوابِ شکوہ کا مرکزی خیال کیا ہے؟"],
    ["How does Iqbal compare Ishq (Love) and Aql (Reason)?"],
    ["What is Faqr (spiritual poverty) in Iqbal's philosophy?"],
    ["Explain Iqbal's vision of Mard-e-Momin — the perfect human."],
]

# ─────────────────────────────────────────────────────────
#  STEP 6 — Gradio UI
# ─────────────────────────────────────────────────────────
with gr.Blocks(title="Iqbal AI Scholar") as demo:

    gr.HTML(HEADER_HTML)

    with gr.Row(equal_height=False):

        with gr.Column(scale=2, min_width=260, elem_classes=["portrait-col"]):
            gr.Image(
                value=IQBAL_IMAGE,
                label="Dr. Allama Muhammad Iqbal  ·  1877 – 1938",
                interactive=False,
                height=420,
            )
            gr.HTML('<div class="sec-lbl" style="margin-top:1rem">✦ Your Question</div>')
            query_input = gr.Textbox(
                label="",
                placeholder="Ask about Khudi, Shaheen, Ishq… or type in Urdu / Persian",
                lines=3,
            )
            submit_btn = gr.Button("✦  Seek Wisdom  ✦", variant="primary")
            gr.HTML('<div class="sec-lbl" style="margin-top:1rem">✦ Sample Questions</div>')
            gr.Examples(examples=EXAMPLES, inputs=query_input, label="")

        with gr.Column(scale=3):
            gr.HTML('<div class="sec-lbl">✦ Scholarly Response</div>')
            answer_output = gr.Markdown(
                value="*The scholar awaits your question…*",
                elem_classes=["answer-panel"],
            )
            gr.HTML('<div style="margin-top:.9rem"></div>')
            with gr.Accordion("📜  Retrieved Source Verses  (Book · Poem · Original · Urdu · English)", open=False):
                context_output = gr.Textbox(
                    lines=14,
                    label="",
                    interactive=False,
                )

    gr.HTML(FOOTER_HTML)

    submit_btn.click(fn=generate_answer, inputs=query_input, outputs=[answer_output, context_output])
    query_input.submit(fn=generate_answer, inputs=query_input, outputs=[answer_output, context_output])

# ─────────────────────────────────────────────────────────
#  LAUNCH
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    demo.launch(css=CSS, server_port=7860, inbrowser=True, share=False)

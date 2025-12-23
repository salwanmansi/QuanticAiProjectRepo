import re, logging, hashlib

from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from openai import RateLimitError

# ---------- logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- config
from config import Config
cfg = Config()

# ---------- helpers
def has_source_citation(text: str) -> bool:
    if not text:
        return False
    pattern = r"Source:\s*[^\n]+?\s+p\.(?:\d+|\?)"
    return re.search(pattern, text) is not None

def extract_cited_filenames(text: str) -> list[str]:
    # Captures filename in: "Source: <filename> p.<page>"
    pattern = r"Source:\s*([^\n]+?)\s+p\.(?:\d+|\?)"
    return [m.strip() for m in re.findall(pattern, text or "")]

def citations_subset_of_ctx(text: str, ctx_sources: list[str]) -> bool:
    cited = extract_cited_filenames(text)
    if not cited:
        return False
    ctx = set(ctx_sources)
    return all(c in ctx for c in cited)

def has_numbered_citations(text: str) -> bool:
    return bool(re.search(r"\[\d+\]\.", text))

def extract_source_numbers(text: str) -> set[int]:
    return {int(n) for n in re.findall(r"\[(\d+)\]", text)}

def extract_sources_block(text: str) -> dict[int, str]:
    """
    Returns {1: 'filename p.page', ...}
    """
    sources = {}
    for num, ref in re.findall(r"\[(\d+)\]\s+([^\n]+)", text):
        sources[int(num)] = ref.strip()
    return sources

# ---------- RAG components
# 1) Set ChatPromptTemplate for RAG
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a policy assistant.\n"
     "Answer ONLY using the provided context from the policy corpus.\n"
     "If the answer is not in the context, refuse.\n\n"
     "Rules:\n"
     "- Do NOT use outside knowledge.\n"
     "- Each Answer sentence MUST be on its own line and MUST end with a numbered citation like [1].\n"
     "- You can use more than one citation per answer line like this [1][2][3][n].\n"
     "- Use only citation numbers that exist in the Context labels.\n"
     "- Sources section MUST list only those refs exactly as shown in the Context labels.\n"
     "- CONSISTENCY:\n"
     "  * Every citation number used in Answer MUST appear in Sources.\n"
     "  * Every entry in Sources MUST be cited at least once in Answer.\n"
     "  * Sources must not contain unused citation numbers.\n"
     "- Include a Documents section listing each unique filename from Sources exactly once.\n"
     "- Nothing may appear after the Files section.\n"
    ),
    ("user",
     "Question: {question}\n\n"
     "Context:\n{context}\n\n"
     "Write the response in EXACTLY this format:\n\n"
     "Answer:\n"
     "sentence1 [1].\n"
     "sentence2 [2].\n"
     "sentence3 [3].\n\n"
     "Sources:\n"
     "[1] <filename> p.<page>\n"
     "[2] <filename> p.<page>\n"
     "[3] <filename> p.<page>\n\n"
     "Documents: (no repetition)\n"
     "<filename>\n"
     "<filename>\n\n"
     "Constraints:\n"
     "- ONE sentence per line in Answer.\n"
     "- Sources lines must be one per line.\n"
     "- Files must be unique filenames from Sources only.\n"
     "- Nothing may appear after Files.\n\n"
     "If the answer is not in the context, write EXACTLY:\n"
     "Answer:\n"
     "I cannot answer from the provided context.\n\n"
     "Sources:\n"
     "(empty)\n\n"
     "Files (no repetition)\n"
     "(empty)\n"
    )
])

# 2) Context
embeddings = HuggingFaceEmbeddings(model_name=cfg.EMB_MODEL)
vectordb = Chroma(persist_directory=cfg.PERSIST_DIR, embedding_function=embeddings)

def make_numbered_context(context_docs):
    """
    Returns:
      context_str: blocks where each chunk is labeled [i] <filename> p.<page>
      refs: dict[int, str] mapping i -> "<filename> p.<page>"
    """
    blocks = []
    refs = {}

    for i, doc in enumerate(context_docs, start=1):
        src = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", None)

        # Display page consistently (1-based if stored as int)
        if isinstance(page, int):
            page_str = str(page + 1)
        elif page is None:
            page_str = "?"
        else:
            page_str = str(page)

        ref = f"{src} p.{page_str}"
        refs[i] = ref

        blocks.append(f"[{i}] {ref}\n{doc.page_content}")

    context_str = "\n\n---\n\n".join(blocks)
    return context_str, refs

# 3) LLM
llm = ChatOpenAI(
    model_name=cfg.LLM_MODEL_NAME,
    openai_api_key=cfg.OPENROUTER_API_KEY,
    openai_api_base=cfg.OPENAI_API_BASE,
    default_headers=cfg.default_headers,
    temperature=cfg.LLM_TEMPERATURE,
    max_tokens=cfg.LLM_MAX_TOKENS,
    timeout=cfg.LLM_TIMEOUT,
)

# 4) Answer and sources
def answer_and_sources(question: str):
    q = (question or "").strip()
    if not q:
        return {"answer": "Please provide a question.", "sources": []}

    # ---- Top-k retrieval
    try:
        results = vectordb.similarity_search_with_relevance_scores(q, k=cfg.TOP_K)
    except Exception:
        log.exception("[rag] retrieval failed")
        return {"answer": "Request failed (retrieval).", "sources": []}

    if not results:
        return {"answer": cfg.REFUSAL_TEXT, "sources": []}

    results = sorted(results, key=lambda x: float(x[1]), reverse=True)
    if float(results[0][1]) < cfg.MIN_RELEVANCE:
        return {"answer": cfg.REFUSAL_TEXT, "sources": []}

    # ---- Build numbered context + allowed refs
    context_docs = [doc for doc, _ in results[:cfg.TOP_K]]
    context_str, allowed_refs = make_numbered_context(context_docs)

    # ---- LLM call
    try:
        messages = prompt.format_messages(question=q, context=context_str)
        llm_resp = llm.invoke(messages)
        response_text = (llm_resp.content or "").strip()
    except Exception:
        log.exception("[rag] LLM failed")
        return {"answer": "Request failed (LLM).", "sources": []}

    # ---- Length cap
    if len(response_text) > cfg.MAX_ANSWER_CHARS:
        response_text = response_text[:cfg.MAX_ANSWER_CHARS].rstrip() + "…"

    # ---- Allow explicit refusal through unchanged
    lower = response_text.lower()
    if "i cannot answer" in lower:
        return {"answer": response_text, "sources": []}

    # ---- Strict validation: citations must be numbers within allowed context
    # Must contain at least one [n].
    cited_nums = {int(n) for n in re.findall(r"\[(\d+)\]", response_text)}
    if not cited_nums:
        return {"answer": cfg.REFUSAL_TEXT, "sources": []}

    # Sources block must exist and must match allowed refs exactly.
    sources_lines = re.findall(r"^\[(\d+)\]\s+(.+)$", response_text, flags=re.MULTILINE)
    if not sources_lines:
        return {"answer": cfg.REFUSAL_TEXT, "sources": []}

    model_sources = {int(n): ref.strip() for n, ref in sources_lines}

    # Every cited number must appear in Sources
    if not cited_nums.issubset(model_sources.keys()):
        return {"answer": cfg.REFUSAL_TEXT, "sources": []}

    # Every source line must match the allowed ref exactly
    for n, ref in model_sources.items():
        if n not in allowed_refs:
            return {"answer": cfg.REFUSAL_TEXT, "sources": []}
        if ref != allowed_refs[n]:
            return {"answer": cfg.REFUSAL_TEXT, "sources": []}

    # ---- Return
    return {
        "answer": response_text,

        # what the model claimed in Sources:
        "sources": {int(n): ref.strip() for n, ref in sources_lines},  # {1: "File.pdf p.2", ...}

        # what YOU retrieved (evidence)
        "docs": [
            {
                "source": d.metadata.get("source", "unknown"),
                "page": (d.metadata.get("page", None) + 1) if isinstance(d.metadata.get("page", None), int) else d.metadata.get("page", None),
                "text": d.page_content
            }
            for d in context_docs
        ],

        # useful for debugging/ablations
        "top_k": cfg.TOP_K,
    }
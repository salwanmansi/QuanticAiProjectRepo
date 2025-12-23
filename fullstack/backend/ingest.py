import os, glob, shutil, random, logging, hashlib, statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    BSHTMLLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ---------- logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- config
from config import Config
cfg = Config()

# ---------- deterministic seeding
try:
    import numpy as np
except ImportError as e:
    raise ImportError("[ingest] numpy is required for deterministic seeding.") from e

try:
    import torch
except ImportError:
    torch = None

random.seed(cfg.SEED)
np.random.seed(cfg.SEED)
if torch is not None:
    torch.manual_seed(cfg.SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(cfg.SEED)

log.info("[ingest] Deterministic seed set to %s", cfg.SEED)

# ---------- printing config values
print(f"[ingest] Using embedding model: {cfg.EMB_MODEL}")
print(f"[ingest] CONTEXT_DIR = {cfg.CONTEXT_DIR}")
print(f"[ingest] PERSIST_DIR = {cfg.PERSIST_DIR}")
print(f"[ingest] CHUNK_SIZE = {cfg.CHUNK_SIZE}, CHUNK_OVERLAP = {cfg.CHUNK_OVERLAP}")
print(f"[ingest] INGEST_RESET = {cfg.INGEST_RESET}")

# ---------- helper functions
INGEST_RUN_ID = os.urandom(4).hex()  # e.g., "a3f91c2d"

def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _file_sha1(path: str) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _base_metadata(file_path: str, corpus_root: str, doc_type: str) -> dict:
    p = Path(file_path)
    rel = os.path.relpath(str(p), start=corpus_root)
    return {
        "source": rel,                              # stable citation key
        "title": p.stem,                            # filename w/o ext
        "file_ext": p.suffix.lower().lstrip("."),   # pdf/md/txt/html
        "doc_type": doc_type,                       # pdf/text/markdown/html
        "file_mtime": int(p.stat().st_mtime),       # seconds since epoch
        "ingested_at": _iso_utc_now(),              # for audit/debug
        "ingest_run_id": INGEST_RUN_ID,             # track a specific run
        # Optional: absolute path for debugging only (remove if you don't want it persisted)
        "source_abs": str(p.resolve()),
    }

# ---------- utilities
def load_documents(folder: str):
    """
    Load documents recursively from:
      - PDF:  .pdf
      - Text: .txt
      - Markdown: .md
      - HTML: .html / .htm

    Adds richer metadata including:
      - source (relative path), page, title, doc_type, file_ext, file_mtime, ingested_at, ingest_run_id, source_sha1
    """
    patterns = [
        "**/*.pdf", "**/*.PDF",
        "**/*.txt", "**/*.TXT",
        "**/*.md",  "**/*.MD",
        "**/*.html", "**/*.HTML",
        "**/*.htm",  "**/*.HTM",
    ]

    paths = []
    for pat in patterns:
        paths += glob.glob(os.path.join(folder, pat), recursive=True)

    paths = sorted(set(paths))  # de-dupe + deterministic ordering

    docs = []

    for p in paths:
        ext = os.path.splitext(p)[1].lower()

        try:
            if ext == ".pdf":
                loader = PyPDFLoader(p)
                loaded = loader.load()

                base = _base_metadata(p, folder, doc_type="pdf")
                base["source_sha1"] = _file_sha1(p)

                for d in loaded:
                    d.metadata.update(base)
                    # normalize page metadata
                    if "page" not in d.metadata and "page_number" in d.metadata:
                        d.metadata["page"] = d.metadata["page_number"]
                    d.metadata.setdefault("page", 1)

                docs.extend(loaded)

            elif ext in (".txt", ".md"):
                loader = TextLoader(p, encoding="utf-8")
                loaded = loader.load()

                base = _base_metadata(p, folder, doc_type=("markdown" if ext == ".md" else "text"))
                base["source_sha1"] = _file_sha1(p)

                for d in loaded:
                    d.metadata.update(base)
                    d.metadata.setdefault("page", 1)

                docs.extend(loaded)

            elif ext in (".html", ".htm"):
                loader = BSHTMLLoader(p, open_encoding="utf-8")
                loaded = loader.load()

                base = _base_metadata(p, folder, doc_type="html")
                base["source_sha1"] = _file_sha1(p)

                for d in loaded:
                    d.metadata.update(base)
                    d.metadata.setdefault("page", 1)

                docs.extend(loaded)

        except UnicodeDecodeError:
            log.warning("[ingest] Unicode decode error, retrying with latin-1: %s", p)

            try:
                if ext in (".txt", ".md"):
                    loader = TextLoader(p, encoding="latin-1")
                    doc_type = "markdown" if ext == ".md" else "text"
                elif ext in (".html", ".htm"):
                    loader = BSHTMLLoader(p, open_encoding="latin-1")
                    doc_type = "html"
                else:
                    raise

                loaded = loader.load()

                base = _base_metadata(p, folder, doc_type=doc_type)
                base["source_sha1"] = _file_sha1(p)

                for d in loaded:
                    d.metadata.update(base)
                    d.metadata.setdefault("page", 1)

                docs.extend(loaded)

            except Exception:
                log.exception("[ingest] Failed fallback load for %s", p)
                continue

        except Exception:
            log.exception("[ingest] Failed to load %s", p)
            continue

    return docs

def assign_chunk_ids(chunks):
    """
    Create stable IDs per chunk based on (source, page, chunk_index).
    Also writes helpful metadata onto each chunk.
    """
    counters = {}  # (source, page) -> next index
    ids = []

    for d in chunks:
        source = d.metadata.get("source", "unknown")
        page = d.metadata.get("page", 1)

        key = (source, page)
        idx = counters.get(key, 0)
        counters[key] = idx + 1

        chunk_id = f"{source}::p{page}::c{idx:03d}"

        d.metadata["chunk_index"] = idx
        d.metadata["chunk_id"] = chunk_id

        ids.append(chunk_id)

    return ids, chunks

def print_ingest_stats(docs, chunks):
    srcs = [d.metadata.get("source", "unknown") for d in docs]
    exts = [os.path.splitext(s)[1].lower().lstrip(".") for s in srcs]
    ext_counts = Counter(exts)

    print("\n[ingest] ---------- Ingestion stats ----------")
    print(f"[ingest] Loaded documents: {len(docs)}")
    print(f"[ingest] Unique sources/files: {len(set(srcs))}")
    print(f"[ingest] File types: {dict(ext_counts)}")

    chunk_lens = [len(c.page_content or "") for c in chunks]
    if not chunk_lens:
        print("[ingest] No chunks to report.")
        print("[ingest] -------------------------------------\n")
        return

    chunk_lens_sorted = sorted(chunk_lens)
    avg_len = int(statistics.mean(chunk_lens_sorted))
    min_len = chunk_lens_sorted[0]
    max_len = chunk_lens_sorted[-1]

    def pct(p):
        idx = int(round((p / 100) * (len(chunk_lens_sorted) - 1)))
        return chunk_lens_sorted[idx]

    p50 = pct(50)
    p90 = pct(90)
    p99 = pct(99)

    print(f"[ingest] Chunks: {len(chunks)}")
    print(f"[ingest] Chunk length chars: min={min_len}, avg={avg_len}, p50={p50}, p90={p90}, p99={p99}, max={max_len}")

    tiny = sum(1 for n in chunk_lens if n < 200)
    huge = sum(1 for n in chunk_lens if n > 2000)
    print(f"[ingest] Tiny chunks (<200 chars): {tiny}")
    print(f"[ingest] Huge chunks (>2000 chars): {huge}")

    chunks_by_source = Counter(c.metadata.get("source", "unknown") for c in chunks)
    print("[ingest] Top sources by chunk count:")
    for src, cnt in chunks_by_source.most_common(10):
        print(f"  - {src}: {cnt}")

    print("[ingest] -------------------------------------\n")

def _safe_rmtree(path: str):
    """
    Refuse to delete suspicious paths.
    """
    ap = os.path.abspath(path)
    if ap in ("/", "") or len(ap) < 10:
        raise ValueError(f"[ingest] Refusing to delete unsafe PERSIST_DIR: {ap}")
    shutil.rmtree(ap)

# ---------- main
def main():
    if not os.path.isdir(cfg.CONTEXT_DIR):
        raise FileNotFoundError(f"[ingest] CONTEXT_DIR not found: {cfg.CONTEXT_DIR}")

    # Optional clean rebuild
    if cfg.INGEST_RESET and os.path.isdir(cfg.PERSIST_DIR):
        print(f"[ingest] INGEST_RESET=1 -> removing existing persisted store at {cfg.PERSIST_DIR}")
        _safe_rmtree(cfg.PERSIST_DIR)

    os.makedirs(cfg.PERSIST_DIR, exist_ok=True)

    docs = load_documents(cfg.CONTEXT_DIR)
    if not docs:
        print(f"⚠️  No documents found in {cfg.CONTEXT_DIR}. Creating empty store.")
        embeddings = HuggingFaceEmbeddings(model_name=cfg.EMB_MODEL)
        Chroma(persist_directory=cfg.PERSIST_DIR, embedding_function=embeddings)
        print(f"✅ Created empty Chroma at {cfg.PERSIST_DIR}")
        return

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg.CHUNK_SIZE,
        chunk_overlap=cfg.CHUNK_OVERLAP,
        separators=[
            "\n\n",        # paragraphs first
            "\n",          # then lines
            "\n• ",        # bullet lines
            "\n- ",        # dash bullets
            "\n* ",        # star bullets
            "\n— ",        # em-dash bullets
            "  ",          # double space
            " ",           # space
            ""             # last resort
        ],
    )

    chunks = splitter.split_documents(docs)
    print_ingest_stats(docs, chunks)

    ids, chunks = assign_chunk_ids(chunks)
    embeddings = HuggingFaceEmbeddings(model_name=cfg.EMB_MODEL)

    # Version-compatible insert (ids supported in some versions, not all)
    try:
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=cfg.PERSIST_DIR,
            ids=ids,
        )
    except TypeError:
        log.warning("[ingest] Chroma.from_documents(ids=...) not supported; falling back to add_documents().")
        db = Chroma(
            persist_directory=cfg.PERSIST_DIR,
            embedding_function=embeddings,
        )
        db.add_documents(documents=chunks, ids=ids)

    print(f"✅ Ingested {len(chunks)} chunks into {cfg.PERSIST_DIR}")

if __name__ == "__main__":
    main()
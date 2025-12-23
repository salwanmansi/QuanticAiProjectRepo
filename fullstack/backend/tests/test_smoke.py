import os

# Set required env vars BEFORE importing app.py (Config() validates on import)
DEFAULT_ENV = {
    "SEED": "42",
    "PERSIST_DIR": "../database/chromadb",
    "EMB_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "CONTEXT_DIR": "../context_data",
    "CHUNK_SIZE": "1100",
    "CHUNK_OVERLAP": "160",
    "INGEST_RESET": "0",
    "TOP_K": "5",
    "MIN_RELEVANCE": "0.25",
    "MAX_ANSWER_CHARS": "2000",
    "MAX_PER_SOURCE": "2",
    "OPENROUTER_API_KEY": "ci_dummy_key",
    "OPENAI_API_BASE": "https://openrouter.ai/api/v1",
    "LLM_MODEL_NAME": "google/gemma-3-27b-it:free",
    "LLM_TEMPERATURE": "0",
    "LLM_MAX_TOKENS": "1024",
    "LLM_TIMEOUT": "60",
    "OPENROUTER_SITE_URL": "http://localhost:8000",
    "OPENROUTER_APP_NAME": "Quantic-AI-RAG",
    "REFUSAL_TEXT": (
        "I can only answer questions about the documents in this policy corpus. "
        "Please ask about company policies and procedures contained in the uploaded documents."
    ),
    "ALLOWED_ORIGINS": "*",
    "PORT": "8000",
}

for k, v in DEFAULT_ENV.items():
    os.environ.setdefault(k, v)

from app import app  # noqa: E402


def test_health():
    c = app.test_client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_version():
    c = app.test_client()
    r = c.get("/api/version")
    assert r.status_code == 200
    body = r.get_json()
    assert body["service"] == "backend"

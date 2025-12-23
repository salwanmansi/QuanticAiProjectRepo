# Quantic – AI

## Project Documentation

- **[README.md](README.md)** – Setup instructions, how to run the backend and frontend, and repository overview  
- **[design-and-evaluation.md](design-and-evaluation.md)** – Design decisions, RAG architecture justification, evaluation methodology, and results  
- **[ai-tooling.md](ai-tooling.md)** – Disclosure of how AI tools (ChatGPT) were used during development  

## Overview

Quantic – AI is a full‑stack Retrieval‑Augmented Generation (RAG) application developed as part of the Quantic University MS in Software Engineering program. The project demonstrates an end‑to‑end, production‑oriented AI system including document ingestion, vector storage, semantic retrieval, citation‑grounded responses, evaluation tooling, and a web‑based chat interface.

The system is intentionally designed to be **reproducible**, **deterministic**, and **auditable**, aligning with academic integrity requirements and real‑world enterprise AI best practices.

---

## Architecture Summary

**High‑level flow:**

1. Documents are ingested and chunked
2. Chunks are embedded and stored in a persistent vector database
3. User queries are semantically retrieved against the vector store
4. A constrained RAG prompt generates citation‑grounded answers
5. Responses are evaluated using automated metrics

**Core principles:**

* Deterministic runs via fixed random seeds
* Strict context‑only answering (no hallucinations)
* Explicit source citations
* Minimal but meaningful CI/CD automation

---

## Repository Structure

```
QuanticAiProject/
├── .github/workflows/              GitHub Actions CI pipeline
├── fullstack/
│   ├── backend/                    Flask RAG API, ingestion pipeline, Gunicorn config
│   ├── context_data/               Contains documents (PDF, TXT. MD, and HTML) knowledge sources
│   ├── database/
│   │   └── chromadb/               Persisted Chroma vector database
│   ├── eval/                       Evaluation files and script
│   ├── frontend/                   React chat UI built with Create React App
├── .gitignore                      What to ignore for github repo
├── ai-tooling.md                   How AI tooling was used to help creating the project
├── deployed.md                     link to the deployed version of the app                     
├── design-and-evaluation.md        Briefly justify design choices
└── README.md                       Project‑level documentation
```

---

## Technology Stack

### Backend

* **Language:** Python 3
* **Framework:** Flask
* **RAG Orchestration:** LangChain
* **Embeddings:** all‑MiniLM‑L6‑v2 (HuggingFace)
* **Vector Store:** ChromaDB (persistent)
* **LLM Provider:** OpenRouter‑compatible models

### Frontend

* **Framework:** React
* **Purpose:** Lightweight chat interface for RAG interaction

### Evaluation

* Custom evaluation scripts for:

  * Groundedness
  * Citation accuracy
  * Exact match
  * Latency (p50 / p95)

### DevOps / CI

* GitHub Actions
* Minimal build & run verification
* Optional Render deployment hook

---

## Backend Environment Configuration

Create a `.env` file in the backend directory:

```
SEED=42
PERSIST_DIR=../database/chromadb
EMB_MODEL=sentence-transformers/all-MiniLM-L6-v2
CONTEXT_DIR=../context_data
CHUNK_SIZE=1100
CHUNK_OVERLAP=160
INGEST_RESET=0
TOP_K=5
MIN_RELEVANCE=0.25
MAX_ANSWER_CHARS=2000
MAX_PER_SOURCE=2
OPENROUTER_API_KEY=<Enter key>
OPENAI_API_BASE=https://openrouter.ai/api/v1
LLM_MODEL_NAME=google/gemma-3-27b-it:free
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=1024
LLM_TIMEOUT=60
OPENROUTER_SITE_URL=http://localhost:8000
OPENROUTER_APP_NAME=Quantic-AI-RAG
REFUSAL_TEXT=I can only answer questions about the documents in this policy corpus. Please ask about company policies and procedures contained in the uploaded documents.
ALLOWED_ORIGINS=http://localhost:3000
PORT=8000
```

> ⚠️ Never commit real API keys to version control.

---

## Frontend Environment Configuration

Create a `.env` file in the frontend directory:

```
REACT_APP_API_BASE=http://localhost:8000
```

---

## Backend Setup & Run

```bash
cd fullstack/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python app.py
```

Verify service health:

```
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
```

---

## Document Ingestion

Place source documents in `context_data/` and run:

```bash
cd fullstack/backend
source .venv/bin/activate
python ingest.py
```

---

## Frontend Setup & Run

```bash
cd fullstack/frontend
npm install
npm start
```

The frontend connects to the backend API and exposes a simple chat UI for querying the RAG system.

---

## Evaluation

Run automated evaluation:

```bash
cd fullstack
source backend/.venv/bin/activate
python eval/run_eval.py
```

Metrics include:

* Groundedness percentage
* Citation accuracy
* Exact match
* Latency p50 / p95

These metrics are intentionally disclosed and documented to comply with Quantic academic integrity rules.

---

## CI/CD

A GitHub Actions workflow is provided that:

1. Installs backend dependencies
2. Performs a build / import sanity check
3. Optionally runs tests
4. On success (main branch), triggers deployment

Minimal automation is intentional and sufficient for the assignment scope.

---

## Design Decisions (Brief)

* **Embedding model:** all‑MiniLM‑L6‑v2 for strong semantic performance with low latency
* **Chunking:** RecursiveCharacterTextSplitter to preserve semantic boundaries
* **Retrieval (k):** Tuned for recall vs. latency trade‑off
* **Prompting:** Strict context‑only RAG prompt with mandatory citations
* **Vector store:** ChromaDB for transparency and local persistence

See **[design-and-evaluation.md](design-and-evaluation.md)** for detailed design decisions and evaluation results.

---

## Academic Integrity Statement

All metrics, evaluation methods, and system behaviors are explicitly disclosed. No hidden heuristics or undisclosed scoring mechanisms are used. The project is designed to be inspectable, reproducible, and auditable.

---

## License

Educational use only.

---

## Author

Salwan Mansi
Quantic University – MS Software Engineering
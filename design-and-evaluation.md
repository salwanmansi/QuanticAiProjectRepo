# Design and Evaluation Documentation
Quantic – AI RAG Application

## 1. System Architecture Overview

Quantic – AI is a full-stack Retrieval-Augmented Generation (RAG) application designed to answer user questions strictly based on a controlled corpus of company policy and procedure documents.

### High-Level Flow

1. Policy documents (PDF, TXT, HTML) are ingested from the `context_data/` directory
2. Documents are cleaned and chunked using deterministic settings
3. Chunks are embedded using a sentence-transformer embedding model
4. Embeddings are stored in a persistent Chroma vector database
5. User questions are embedded and matched via similarity search (Top-K)
6. Retrieved chunks are injected into a structured prompt
7. The LLM generates a grounded, citation-backed response
8. Responses are returned through a REST API and web chat interface

---

## 2. Design Decisions and Rationale

### 2.1 Embedding Model

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**Justification:**
- Free, open-source, and locally runnable
- Strong semantic performance for policy-style documents
- Low latency and small embedding size
- Widely adopted in RAG benchmarks

This model strikes an optimal balance between performance, cost, and reproducibility.

---

### 2.2 Chunking Strategy

**Chunk size:** ~1100 characters  
**Overlap:** ~160 characters  

**Justification:**
- Large enough to preserve policy context
- Overlap prevents semantic loss at boundaries
- Deterministic chunking ensures reproducibility across runs

Recursive chunking was chosen to respect document structure while maintaining consistent chunk sizes.

---

### 2.3 Retrieval Strategy

**Top-K:** configurable (default K = 5)

Additional safeguards include:
- Automatic widening of retrieval if only one source is returned
- Per-source result capping to prevent single-document dominance
- Optional second-pass retrieval for rule-focused queries

This ensures both diversity and relevance of retrieved context.

---

### 2.4 Prompting Strategy

The prompt enforces strict guardrails:
- Answers must ONLY use provided context
- If insufficient context exists, the model must refuse
- Each answer sentence must end with a citation
- Citations must match retrieved document labels
- Output length is capped

This design prioritizes groundedness and auditability over creativity.

---

### 2.5 Vector Store

**Database:** ChromaDB (local persistence)

**Justification:**
- Lightweight and easy to inspect
- No external dependencies or cost
- Suitable for academic evaluation and reproducibility
- Persistent storage allows re-use across sessions

---

## 3. Evaluation Methodology

### 3.1 Evaluation Dataset

A curated evaluation set of **30 questions** was created covering:
- PTO and leave policies
- Remote work and hybrid rules
- Expense reimbursement
- Security and compliance
- Incident management
- Policy conflicts and exceptions

Gold answers and citation expectations were defined where applicable.

---

### 3.2 Answer Quality Metrics

**Groundedness**
- Measures whether answers are fully supported by retrieved context
- Penalizes hallucinated or unsupported statements

**Citation Accuracy**
- Verifies that cited sources directly support the associated claims
- Ensures correct attribution to specific documents

**Exact / Partial Match (optional)**
- Used selectively for deterministic policy questions

---

### 3.3 System Metrics

**Latency**
- p50 and p95 latency measured over 10–20 queries
- Includes retrieval + generation time

Latency metrics were logged during evaluation runs to assess responsiveness.

---

### 3.4 Ablation Experiments

Optional ablations were conducted to observe:
- Different Top-K values (e.g., K=5 vs K=10)
- Impact of chunk size and overlap
- Prompt variants emphasizing rules vs examples

These experiments informed final parameter selection.

---

## 4. Summary

The design choices prioritize:
- Reproducibility
- Grounded, auditable answers
- Clear policy traceability
- Compliance with academic and enterprise AI standards

The resulting system is robust, transparent, and suitable for real-world policy question answering.
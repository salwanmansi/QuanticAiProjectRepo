## 8. Design Documentation

This section describes and justifies the major design choices made in the Quantic-AI policy question-answering system, including the embedding model, document chunking strategy, retrieval depth, prompt format, and vector store.

---

### 8.1 Embedding Model

**Model used:** `sentence-transformers/all-MiniLM-L6-v2`

**Justification:**
The `all-MiniLM-L6-v2` embedding model was selected due to its strong balance between semantic quality, computational efficiency, and widespread adoption in production-grade retrieval systems. The model produces dense 384-dimensional embeddings that capture semantic similarity effectively for policy and procedural text, while remaining lightweight enough to support fast ingestion and retrieval on modest hardware.

This choice is particularly appropriate for a policy corpus, where:
- semantic similarity matters more than keyword overlap,
- documents are formal, declarative, and moderately sized,
- embeddings must be recomputed deterministically during ingestion.

The model integrates cleanly with LangChain and Chroma, enabling reproducible retrieval behavior across ingestion and evaluation runs.

---

### 8.2 Document Chunking Strategy

**Chunking approach:** Recursive character-based chunking (during ingestion)  
**Chunk size:** Fixed-size chunks with overlap (configured during ingestion)

**Justification:**
Policy documents frequently contain long sections with cross-referenced rules, exceptions, and definitions. Recursive character-based chunking preserves local semantic coherence while ensuring that chunks remain small enough to fit within LLM context limits when multiple chunks are retrieved.

Overlapping chunks reduce boundary effects where relevant policy language might otherwise be split across chunks, improving recall during retrieval. This strategy favors correctness and interpretability over aggressive compression.

Chunking is performed once at ingestion time, ensuring that evaluation runs operate over a stable, deterministic document index.

---

### 8.3 Retrieval Depth (TOP_K)

**Evaluated values:** `k ∈ {3, 5, 10}`  
**Default operational range:** `k = 3–5`

**Justification:**
The retrieval depth (`TOP_K`) determines how many document chunks are retrieved and supplied to the LLM as context. An ablation study was conducted comparing `k = 3`, `k = 5`, and `k = 10`.

Results showed:
- Citation accuracy remained at **100%** across all k values.
- Latency increased monotonically with higher k values.
- Groundedness (under a strict lexical heuristic) did not materially improve with higher k.

These results indicate diminishing returns beyond `k = 5` for this corpus. Smaller k values reduce latency and prompt size without degrading citation correctness. As a result, `k = 3–5` provides the best latency–quality tradeoff for this system.

---

### 8.4 Prompt Format and Guardrails

**Prompt style:** Structured RAG prompt with strict output constraints

**Key characteristics:**
- Answers must be derived **only** from retrieved context.
- Each answer sentence must end with one or more numbered citations (e.g., `[1]`, `[2][3]`).
- Citations must correspond exactly to numbered context chunks.
- A `Sources` section must enumerate all cited references.
- If the answer is not supported by the retrieved context, the model must explicitly refuse.

**Justification:**
The prompt was intentionally designed to prioritize **faithfulness and auditability** over verbosity or fluency. Strict formatting rules prevent hallucinated facts, enforce traceability to source documents, and enable automated evaluation of citation correctness.

This design aligns with enterprise and compliance use cases, where incorrect but fluent answers are more harmful than conservative refusals.

---

### 8.5 Vector Store

**Vector database:** Chroma (persistent mode)

**Justification:**
Chroma was selected as the vector store due to its simplicity, transparency, and tight integration with LangChain. Persistent storage allows the vector index to survive application restarts and enables reproducible evaluation runs without re-ingestion.

Chroma supports:
- fast cosine similarity search,
- deterministic retrieval behavior,
- lightweight local deployment without external infrastructure.

For the scale of this project (tens to hundreds of policy documents), Chroma provides sufficient performance while keeping operational complexity low.

---

### 8.6 Overall Design Rationale

The system design emphasizes:
- **Correctness over fluency**
- **Traceability over creativity**
- **Reproducibility over heuristic tuning**

Each component was chosen to support reliable policy question answering under constrained and auditable conditions. The resulting architecture is modular, interpretable, and well-suited for both academic evaluation and real-world compliance-oriented applications.
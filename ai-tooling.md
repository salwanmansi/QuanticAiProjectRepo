# AI Tooling Disclosure

## 1. AI Tools Used

### AI Coding Assistance

**ChatGPT** was used as the primary AI assistant to help generate the document corpus, scaffold the full-stack application, debug runtime issues, and iteratively refine the RAG pipeline and evaluation setup.

---

## 2. How AI Tools Were Used

### Creating policy and procedure documents

I used ChatGPT to generate a synthetic corpus of company policies & procedures for ingestion.

1) Initial corpus generation prompt:
- “I am developing an AI app that will ingest documents. I need your help generating documents as follows: corpus of documents outlining company policies & procedures - about 5–20 short markdown/HTML/PDF/TXT files totaling 30–120 pages.”

2) After reviewing options, I requested a full deliverable:
- “Generate the full corpus immediately as a zip file that includes each policy as a separate pdf document”

3) The first output did not match expectations (10 policies, ~half page each), so I clarified requirements:
- “You gave me a total of 12 policies, then in the zip file you gave me only 10…  
  1. Include all 12 original policies  
  2. Each policy content needs to have 10 pages of content  
  Redo the zip file”

4) The next output contained filler/duplicated pages, so I refined the ask to force uniqueness and evaluation-friendly structure:
- “Replace filler sections with fully unique content per page  
  Add policy conflicts & exceptions (great for eval)  
  Add metadata pages (policy owner, revision, effective date)  
  Create golden QA evaluation sets for RAG benchmarking  
  tune the corpus to my RAG pipeline as follows:  
  1. Orchestration: LangChain  
  2. Prompt Template: RAG  
  3. Embedding model: all-MiniLM-L6-v2  
  4. LLM uses: google/gemma-3-27b-it:free”

This sequence gave ChatGPT enough detail to generate a corpus aligned with the final RAG pipeline and evaluation goals.

---

### Creating the application (backend + frontend)

I uploaded the project requirements and iterated with ChatGPT until I had a working backend and frontend that matched the rubric.

- I repeatedly asked for code updates, then tested locally and returned errors/logs to ChatGPT.
- Once I had a running full-stack version, I re-uploaded the solution and asked ChatGPT to review the structure and identify gaps against requirements:

“Examine the zip folder, it includes:  
1. context_data: these are the 12 pdfs you helped prepared for the policies and procedures.  
2. database: this is where I will create the chroma database  
3. backend: this is where the backend files live  
4. frontend: this is where we will include all UI files  
Remember this file structure when answering the prompts in this project Quantic - AI folder  
Let me know if you see any issues with any of the files inside backend and frontend”

ChatGPT responded with a list of fixes; I then applied them one-by-one rather than trying to change everything at once.

---

### Running and debugging the backend

- When I encountered a **404** error while running the backend, ChatGPT suggested adding a `/` route to the API, which resolved the issue.
- ChatGPT also suggested adding `/api/version` and `/api/config`. I asked why, and after reviewing usefulness, I implemented `/api/version` only.

---

### Running and debugging the frontend

When I encountered frontend build/runtime errors, ChatGPT produced multiple possible fixes. I found the best workflow was to ask for one fix at a time, implement it, then re-test.

---

### Debugging the chat / RAG pipeline

During golden Q&A testing, I encountered guardrail and citation formatting issues. ChatGPT helped by:
- Suggesting adding log statements before refusal branches to reveal what condition triggered a refusal.
- Modifying the backend citation handling when citations were not accepting multiple references, which enabled answers to return with citations again.

At one point I noticed ChatGPT was suggesting “hacks/workarounds” rather than true fixes, so I explicitly told it to stop and only provide real code solutions.

I also observed ChatGPT tended to overwrite entire files. I corrected this by instructing it to:
- Identify what was wrong
- Provide targeted edits
- Specify exactly where to apply changes

This improved the quality of iteration significantly.

---

### Ingest.py iteration approach

I found the most effective approach was to:
- Avoid asking “what’s wrong with this code?” in a general way
- Instead ask ChatGPT to fix one isolated issue at a time, then retest

---

### Evaluation set iteration

ChatGPT initially generated **60** golden Q&A items. When I attempted to use all of them, ChatGPT suggested overly complex code to reduce the dataset. I simplified the process by manually reducing to **30** questions and reloading the file.

---

### Workflow strategy that produced best results

What worked best was providing requirements to ChatGPT in this order:
1) Requirements 1–4 (environment, ingestion, RAG, web app)
2) Requirement 7 (evaluation)
3) Requirements 5–6 (deployment + CI/CD)
4) Requirement 8 (design documentation)

This reduced confusion and prevented ChatGPT from producing “one giant final solution” that required large rewrites.

---

### Final project requirements review

At the end, I uploaded the rubric and the complete project and asked ChatGPT to perform a final scan for gaps. After receiving the gap list, I asked ChatGPT to fix one item at a time until requirements were satisfied.

---

## 3. What Worked Well

- Iterative development: asking ChatGPT to fix **one issue at a time** worked significantly better than large multi-fix requests.
- Copy/pasting actual runtime output and logs into ChatGPT helped it diagnose issues quickly.
- Explaining backend code section-by-section improved my understanding and helped me implement final refinements myself.
- Providing requirements in a structured order (1–4, then 7, then 5–6, then 8) improved alignment to the rubric.

---

## 4. What Did Not Work Well

- Asking ChatGPT to “fix everything” in one request resulted in:
  - large rewrites
  - overwriting files
  - introducing regressions
- Citation ordering: I was not able to force consistent ordering of citation numbers purely through prompt changes; it sometimes skipped a number under Sources.
- Ingest.py debugging: asking for general critique (“tell me what’s wrong”) did not produce good results; targeted requests worked better.
- Evaluation set reduction: ChatGPT proposed overly complex approaches when I tried to reduce an oversized golden Q&A file; manual reduction was faster and clearer.

---

## 5. Academic Integrity Statement

ChatGPT was used as a development aid for generating synthetic policy documents, drafting/iterating code, debugging issues, and improving documentation. All final architectural decisions, code integration, testing, and submission packaging were performed by me. No proprietary or restricted documents were used; the policy corpus was generated to be legally includable in the repository.
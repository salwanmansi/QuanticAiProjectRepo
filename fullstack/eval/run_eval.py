import json
import time
import statistics
import os
import sys
import re
import importlib.util

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

# IMPORTANT: run as if we are inside backend/ so relative paths (.env, chromadb path) match
os.chdir(BACKEND_DIR)

# make backend/config.py importable as "config" from backend/backend.py
sys.path.insert(0, BACKEND_DIR)

BACKEND_FILE = os.path.join(BACKEND_DIR, "backend.py")

spec = importlib.util.spec_from_file_location("project_backend_backend", BACKEND_FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

answer_and_sources = mod.answer_and_sources

# if backend config exists, grab refusal text from it
CFG = getattr(mod, "cfg", None)
REFUSAL_TEXT = getattr(CFG, "REFUSAL_TEXT", "").strip() if CFG else ""

EVAL_FILE = os.path.join(PROJECT_ROOT, "eval", "eval_questions.jsonl")


def load_eval_questions(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def extract_cited_numbers(answer_text: str) -> set[int]:
    return {int(n) for n in re.findall(r"\[(\d+)\]", answer_text or "")}


def is_refusal(answer_text: str) -> bool:
    t = (answer_text or "").strip()
    if not t:
        return True
    # backend's standardized refusal (if set)
    if REFUSAL_TEXT and t == REFUSAL_TEXT:
        return True
    # prompt refusal
    if "cannot answer" in t.lower():
        return True
    return False


def run_eval():
    questions = load_eval_questions(EVAL_FILE)

    latencies = []
    grounded_pass = []
    citation_pass = []
    exact_match = []

    for i, q in enumerate(questions):
        question = (q.get("question") or "").strip()
        gold = (q.get("expected_answer") or "").strip()

        start = time.time()
        result = answer_and_sources(question)
        time.sleep(5.0)
        latency = time.time() - start
        latencies.append(latency)

        answer_text = result.get("answer", "")
        retrieved_docs = result.get("docs", [])          # list[dict]
        model_sources = result.get("sources", {})        # dict[int,str]

        # DEBUG: show first two items so we know what's happening
        if i < 2:
            print("\n--- DEBUG SAMPLE ---")
            print("Q:", question)
            print("Answer:", answer_text[:500])
            print("docs:", len(retrieved_docs), "sources:", len(model_sources))
            print("--- END DEBUG ---\n")

        # Exact / partial match (optional)
        exact_match.append(gold.lower() in answer_text.lower() if gold else False)

        # Refusal/error path handling
        if is_refusal(answer_text):
            # If you refuse correctly, groundedness is "pass" (system didn't hallucinate)
            grounded_pass.append(True)
            # Citation accuracy: pass if no sources were claimed
            citation_pass.append(len(model_sources) == 0)
            continue

        # Citation accuracy: cited numbers must exist in model_sources
        cited_nums = extract_cited_numbers(answer_text)
        citation_ok = bool(cited_nums) and cited_nums.issubset(set(model_sources.keys()))
        citation_pass.append(citation_ok)

        # Groundedness (simple heuristic): each answer line should appear in some retrieved chunk
        if not retrieved_docs:
            grounded_pass.append(False)
        else:
            ok = True
            for line in answer_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line in {"Answer:", "Sources:", "Documents:", "Files (no repetition)", "Files (no repetition):"}:
                    continue
                line_lower = line.lower()
                if not any(line_lower in (d.get("text", "") or "").lower() for d in retrieved_docs if isinstance(d, dict)):
                    ok = False
                    break
            grounded_pass.append(ok)

    p50 = statistics.median(latencies)
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies)

    return {
        "num_questions": len(questions),
        "groundedness_pct": sum(grounded_pass) / len(grounded_pass) if grounded_pass else 0.0,
        "citation_accuracy_pct": sum(citation_pass) / len(citation_pass) if citation_pass else 0.0,
        "exact_match_pct": sum(exact_match) / len(exact_match) if exact_match else 0.0,
        "latency_p50_s": p50,
        "latency_p95_s": p95,
    }


if __name__ == "__main__":
    print(json.dumps(run_eval(), indent=2))
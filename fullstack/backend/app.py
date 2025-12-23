import logging

from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

# ---------- logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- config
from config import Config
cfg = Config()

# ---------- app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": cfg.ALLOWED_ORIGINS}})
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# ---------- api endpoint get /
@app.get("/")
def root():
    return {"ok": True, "service": "backend", "hint": "Try /health or /api routes"}, 200

# ---------- api endpoint get /health
@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

# ---------- api endpoint get /api/version
@app.get("/api/version")
def version():
    return {
        "service": "backend",
        "version": "1.0.0",
        "environment": "local"
    }, 200

# ---------- api endpoint get /chat
@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        log.info("Bad request: missing 'question'")
        return jsonify({"error": "question is required"}), 400

    try:
        from backend import answer_and_sources  # <-- lazy import (important for CI)
        result = answer_and_sources(question)
        return jsonify(result), 200
    except Exception:
        log.exception("Error handling /chat request")
        return jsonify({"error": "Internal server error"}), 500

# ---------- main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg.PORT)
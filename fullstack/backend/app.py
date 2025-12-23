import logging

from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

# ---------- serve React build (production)
from pathlib import Path
from flask import send_from_directory

# ---------- logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- config
from config import Config
cfg = Config()

# ---------- serve React build (production)
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = (BASE_DIR / ".." / "frontend" / "build").resolve()
FRONTEND_STATIC_DIR = (FRONTEND_BUILD_DIR / "static").resolve()

# ---------- app
app = Flask(
    __name__,
    static_folder=str(FRONTEND_STATIC_DIR),   # serve CRA assets from build/static
    static_url_path="/static",
)
CORS(app, resources={r"/*": {"origins": cfg.ALLOWED_ORIGINS}})
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# ---------- serve React build (production)
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = (BASE_DIR / ".." / "frontend" / "build").resolve()

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

# ---------- serve React build (production)
@app.get("/")
def serve_react_index():
    index = FRONTEND_BUILD_DIR / "index.html"
    if index.exists():
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")
    return jsonify({"error": "Frontend build not found. Run `npm run build` in fullstack/frontend."}), 500

@app.get("/<path:path>")
def serve_react_static(path):
    # Serve static assets or fall back to index.html for client-side routes
    file_path = FRONTEND_BUILD_DIR / path
    if file_path.exists():
        return send_from_directory(FRONTEND_BUILD_DIR, path)

    index = FRONTEND_BUILD_DIR / "index.html"
    if index.exists():
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")

    return jsonify({"error": "Frontend build not found. Run `npm run build` in fullstack/frontend."}), 500


# ---------- main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg.PORT)
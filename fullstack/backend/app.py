import logging
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS

# ---------- logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- config
from config import Config  # noqa: E402
cfg = Config()

# ---------- serve React build (production)
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_BUILD_DIR = (BASE_DIR / ".." / "frontend" / "build").resolve()
FRONTEND_STATIC_DIR = (FRONTEND_BUILD_DIR / "static").resolve()

log.info("FRONTEND_BUILD_DIR=%s exists=%s", FRONTEND_BUILD_DIR, FRONTEND_BUILD_DIR.exists())
log.info("FRONTEND_STATIC_DIR=%s exists=%s", FRONTEND_STATIC_DIR, FRONTEND_STATIC_DIR.exists())

# ---------- app
app = Flask(
    __name__,
    static_folder=str(FRONTEND_STATIC_DIR),  # serves /static/* from CRA build/static
    static_url_path="/static",
)
CORS(app, resources={r"/*": {"origins": cfg.ALLOWED_ORIGINS}})
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# OPTIONAL: cache static assets for 1 year (safe for hashed CRA builds)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000

# ---------- api endpoint get /health
@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

# ---------- api endpoint get /api/version
@app.get("/api/version")
def version():
    return jsonify({
        "service": "backend",
        "version": "1.0.0",
        "environment": "render",
    }), 200

# ---------- api endpoint post /chat
@app.post("/chat")
def chat():
    data = request.get_json(force=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        log.info("Bad request: missing 'question'")
        return jsonify({"error": "question is required"}), 400

    try:
        from backend import answer_and_sources  # lazy import (important for CI)
        result = answer_and_sources(question)
        return jsonify(result), 200
    except Exception:
        log.exception("Error handling /chat request")
        return jsonify({"error": "Internal server error"}), 500

# ---------- serve React index (SPA)
@app.get("/")
def serve_react_index():
    index = FRONTEND_BUILD_DIR / "index.html"
    if index.exists():
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")
    return jsonify({"error": "Frontend build not found. Run `npm run build` in fullstack/frontend."}), 500

# ---------- serve React client-side routes (NOT /static/*)
@app.get("/<path:path>")
def serve_react_routes(path: str):
    # Don't interfere with API routes (these should 404 if not defined)
    if path.startswith("api/") or path in ("health", "chat"):
        return jsonify({"error": "Not found"}), 404

    # If a real file exists in the build folder (e.g., favicon.ico, manifest.json), serve it
    file_path = FRONTEND_BUILD_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(FRONTEND_BUILD_DIR, path)

    # Otherwise fall back to index.html for React Router
    index = FRONTEND_BUILD_DIR / "index.html"
    if index.exists():
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")

    return jsonify({"error": "Frontend build not found. Run `npm run build` in fullstack/frontend."}), 500

# ---------- main
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=cfg.PORT)
import os, logging
from dotenv import load_dotenv

# ---------- logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ---------- .env
load_dotenv()

class Config:
    def __init__(self):
        self.SEED = os.getenv("SEED")
        self.PERSIST_DIR = os.getenv("PERSIST_DIR")
        self.EMB_MODEL = os.getenv("EMB_MODEL")

        self.CONTEXT_DIR = os.getenv("CONTEXT_DIR")
        self.CHUNK_SIZE = os.getenv("CHUNK_SIZE")
        self.CHUNK_OVERLAP = os.getenv("CHUNK_OVERLAP")
        self.INGEST_RESET = os.getenv("INGEST_RESET")

        self.TOP_K = os.getenv("TOP_K")
        self.MIN_RELEVANCE = os.getenv("MIN_RELEVANCE")
        self.MAX_ANSWER_CHARS = os.getenv("MAX_ANSWER_CHARS")
        self.MAX_PER_SOURCE = os.getenv("MAX_PER_SOURCE")

        self.OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
        self.OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
        self.LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME")
        self.LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE")
        self.LLM_MAX_TOKENS = os.getenv("LLM_MAX_TOKENS")
        self.LLM_TIMEOUT = os.getenv("LLM_TIMEOUT")

        self.OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL")
        self.OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME")
        
        self.REFUSAL_TEXT = os.getenv("REFUSAL_TEXT")

        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS")
        self.PORT = os.getenv("PORT")

        self._validate()
        self._normalize()

    def _validate(self):
        required = {
            "SEED": self.SEED,
            "PERSIST_DIR": self.PERSIST_DIR,
            "EMB_MODEL": self.EMB_MODEL,

            "CONTEXT_DIR": self.CONTEXT_DIR,
            "CHUNK_SIZE": self.CHUNK_SIZE,
            "CHUNK_OVERLAP": self.CHUNK_OVERLAP,
            "INGEST_RESET": self.INGEST_RESET,

            "TOP_K": self.TOP_K,
            "MIN_RELEVANCE": self.MIN_RELEVANCE,
            "MAX_ANSWER_CHARS": self.MAX_ANSWER_CHARS,
            "MAX_PER_SOURCE": self.MAX_PER_SOURCE,

            "OPENROUTER_API_KEY": self.OPENROUTER_API_KEY,
            "OPENAI_API_BASE": self.OPENAI_API_BASE,
            "LLM_MODEL_NAME": self.LLM_MODEL_NAME,
            "LLM_TEMPERATURE": self.LLM_TEMPERATURE,
            "LLM_MAX_TOKENS": self.LLM_MAX_TOKENS,
            "LLM_TIMEOUT": self.LLM_TIMEOUT,
            
            "OPENROUTER_SITE_URL": self.OPENROUTER_SITE_URL,
            "OPENROUTER_APP_NAME": self.OPENROUTER_APP_NAME,

            "REFUSAL_TEXT": self.REFUSAL_TEXT,

            "ALLOWED_ORIGINS": self.ALLOWED_ORIGINS,
            "PORT": self.PORT,
        }

        missing = [k for k, v in required.items() if v is None or str(v).strip() == ""]
        if missing:
            raise RuntimeError(
                f"[backend] Missing required environment variables: {', '.join(missing)}"
            )

    def _normalize(self):
        self.SEED = int(self.SEED)
        self.PERSIST_DIR = self.PERSIST_DIR
        self.EMB_MODEL = self.EMB_MODEL

        self.CONTEXT_DIR = self.CONTEXT_DIR
        self.CHUNK_SIZE = int(self.CHUNK_SIZE)
        self.CHUNK_OVERLAP = int(self.CHUNK_OVERLAP)
        self.INGEST_RESET = str(self.INGEST_RESET).strip().lower() in ("1", "true", "yes")

        self.TOP_K = int(self.TOP_K)
        self.MIN_RELEVANCE = float(self.MIN_RELEVANCE)
        self.MAX_ANSWER_CHARS = int(self.MAX_ANSWER_CHARS)
        self.MAX_PER_SOURCE = int(self.MAX_PER_SOURCE)

        self.OPENROUTER_API_KEY = self.OPENROUTER_API_KEY
        self.OPENAI_API_BASE = self.OPENAI_API_BASE
        self.LLM_MODEL_NAME = self.LLM_MODEL_NAME
        self.LLM_TEMPERATURE = float(self.LLM_TEMPERATURE)
        self.LLM_MAX_TOKENS = int(self.LLM_MAX_TOKENS)
        self.LLM_TIMEOUT = int(self.LLM_TIMEOUT)

        self.OPENROUTER_SITE_URL = self.OPENROUTER_SITE_URL
        self.OPENROUTER_APP_NAME = self.OPENROUTER_APP_NAME

        self.REFUSAL_TEXT = self.REFUSAL_TEXT

        self.ALLOWED_ORIGINS = self.ALLOWED_ORIGINS
        self.PORT = int(self.PORT)

        headers = {}
        if self.OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = self.OPENROUTER_SITE_URL
        if self.OPENROUTER_APP_NAME:
            headers["X-Title"] = self.OPENROUTER_APP_NAME
        self.default_headers = headers or None
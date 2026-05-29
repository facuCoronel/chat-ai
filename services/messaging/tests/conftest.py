import os


os.environ.setdefault("WEBHOOK_VERIFY_TOKEN", "test-verify-token")
os.environ.setdefault("APP_SECRET", "test-app-secret")
os.environ.setdefault("OLLAMA_BASE_URL", "http://ollama.test")
os.environ.setdefault("OLLAMA_MODEL", "test-model")
os.environ.setdefault("OLLAMA_PROMPT_VERSION", "test")
os.environ.setdefault("WHISPER_BASE_URL", "http://whisper.test")

from __future__ import annotations
import os

def init_langsmith_tracing() -> None:
    """
    Enables LangSmith tracing via env vars.
    Kept as a small explicit init so it's obvious in workshops.
    """
    enabled = os.getenv("ENABLE_LANGSMITH", "").strip().lower() in {"1", "true", "yes", "on"}
    has_key = bool(os.getenv("LANGSMITH_API_KEY", "").strip())
    has_project = bool(os.getenv("LANGCHAIN_PROJECT", "").strip())

    # Default behavior: keep tracing fully off unless explicitly requested.
    if not enabled:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        return

    # If tracing is requested but not configured, disable it to avoid noisy 403 logs.
    if not has_key or not has_project:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        print(
            "LangSmith tracing requested but LANGSMITH_API_KEY/LANGCHAIN_PROJECT are missing; "
            "continuing with tracing disabled."
        )
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
